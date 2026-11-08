"""Logical retirement and its interaction with stock."""

import sqlite3
import threading
import time
from pathlib import Path

import pytest

from pi.catalog import (
    CatalogService,
    Category,
    Product,
    ProductHasStockError,
    SqliteProductResolver,
)
from pi.inventory import (
    InventoryService,
    RetiredProductError,
    create_stock_record,
)
from pi.operation_contract import ProductQuery, ResolutionStatus
from pi.storage import apply_migrations, connect, transaction


def _prepare(connection: sqlite3.Connection) -> CatalogService:
    catalog = CatalogService(connection)
    catalog.add_category(Category("bebidas", "Bebidas"))
    catalog.add_product(
        Product(
            product_id="gaseosa-zero",
            name="Gaseosa",
            brand="Coca-Cola",
            variant="Zero",
            presentation="2.25 L",
            category_id="bebidas",
        )
    )
    return catalog


def test_a_product_without_stock_can_be_retired(connection) -> None:
    catalog = _prepare(connection)

    retired = catalog.retire_product("gaseosa-zero")

    assert retired.retired is True
    assert retired.product_id == "gaseosa-zero"
    assert retired.name == "Gaseosa"
    assert catalog.list_active_product_ids() == ()
    assert catalog.get_product("gaseosa-zero").retired is True


def test_a_product_with_zero_stock_can_be_retired(connection) -> None:
    catalog = _prepare(connection)
    create_stock_record(connection, "gaseosa-zero", 0)

    catalog.retire_product("gaseosa-zero")

    level = InventoryService(connection).get_stock("gaseosa-zero").level
    assert level is not None
    assert level.quantity == 0
    assert level.retired is True


def test_positive_stock_rejects_retirement_without_changes(connection) -> None:
    catalog = _prepare(connection)
    create_stock_record(connection, "gaseosa-zero", 4)

    with pytest.raises(ProductHasStockError) as raised:
        catalog.retire_product("gaseosa-zero")

    assert raised.value.quantity == 4
    assert catalog.get_product("gaseosa-zero").retired is False
    assert InventoryService(connection).get_stock("gaseosa-zero").level.quantity == 4


def test_a_failed_retirement_rolls_back_the_caller_transaction(connection) -> None:
    catalog = _prepare(connection)
    create_stock_record(connection, "gaseosa-zero", 0)

    with pytest.raises(ProductHasStockError), transaction(connection):
        InventoryService(connection).apply_delta("gaseosa-zero", 2, "unit")
        catalog.retire_product("gaseosa-zero")

    assert catalog.get_product("gaseosa-zero").retired is False
    assert InventoryService(connection).get_stock("gaseosa-zero").level.quantity == 0


def test_retirement_itself_rolls_back_with_the_caller(connection) -> None:
    catalog = _prepare(connection)

    with pytest.raises(RuntimeError), transaction(connection):
        catalog.retire_product("gaseosa-zero")
        raise RuntimeError("the caller fails before committing")

    assert catalog.get_product("gaseosa-zero").retired is False


def test_a_retired_product_stays_out_of_resolution_and_active_lists(
    connection,
) -> None:
    catalog = _prepare(connection)
    catalog.retire_product("gaseosa-zero")
    resolution = SqliteProductResolver(connection).resolve(
        ProductQuery("Gaseosa", brand="Coca-Cola", variant="Zero")
    )

    assert resolution.status is ResolutionStatus.UNKNOWN
    assert catalog.list_products() == ()
    assert [
        product.product_id for product in catalog.list_products(include_retired=True)
    ] == [
        "gaseosa-zero",
    ]


def test_stock_changes_are_rejected_after_retirement(connection) -> None:
    catalog = _prepare(connection)
    create_stock_record(connection, "gaseosa-zero", 0)
    catalog.retire_product("gaseosa-zero")

    with pytest.raises(RetiredProductError):
        InventoryService(connection).apply_delta("gaseosa-zero", 1, "unit")
    with pytest.raises(RetiredProductError):
        create_stock_record(connection, "gaseosa-zero", 2)

    assert InventoryService(connection).get_stock("gaseosa-zero").level.quantity == 0


def test_retiring_an_already_retired_product_is_stable(connection) -> None:
    catalog = _prepare(connection)
    catalog.retire_product("gaseosa-zero")

    again = catalog.retire_product("gaseosa-zero")

    assert again.retired is True
    assert again.product_id == "gaseosa-zero"


def test_retirement_waits_for_a_concurrent_stock_change(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    connection = connect(path)
    apply_migrations(connection)
    _prepare(connection)
    create_stock_record(connection, "gaseosa-zero", 0)
    connection.close()

    holder = connect(path)
    holder.execute("BEGIN IMMEDIATE")
    holder.execute(
        "UPDATE inventory_stock SET quantity = 4 WHERE product_id = 'gaseosa-zero'"
    )
    outcome: list[str] = []

    def retire() -> None:
        other = connect(path)
        try:
            CatalogService(other).retire_product("gaseosa-zero")
        except ProductHasStockError:
            outcome.append("rejected")
        else:
            outcome.append("retired")
        finally:
            other.close()

    worker = threading.Thread(target=retire)
    worker.start()
    time.sleep(0.2)
    holder.execute("COMMIT")
    worker.join(timeout=6)
    holder.close()

    assert outcome == ["rejected"]
    check = connect(path)
    try:
        product = CatalogService(check).get_product("gaseosa-zero")
        quantity = InventoryService(check).get_stock("gaseosa-zero").level.quantity
    finally:
        check.close()
    assert product.retired is False
    assert quantity == 4
