"""Tests for loading the initial stock of the test supermarket."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from pi import database_cli
from pi.catalog import CatalogService, load_initial_catalog
from pi.catalog.seed import SEED_PRODUCTS
from pi.inventory import (
    INITIAL_STOCK,
    InitialStockMismatchError,
    InvalidQuantityError,
    InventoryService,
    find_active_products_without_stock,
    load_initial_stock,
)
from pi.movement_history import MovementQuery, SQLiteMovementHistory
from pi.storage import apply_migrations, connect, transaction

COCA = "gaseosa-coca-cola-zero-2250"


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "voicestock.sqlite3")
    apply_migrations(connection)
    load_initial_catalog(connection)
    yield connection
    connection.close()


def _stock(connection) -> dict[str, int]:
    return {
        level.product_id: level.quantity
        for level in InventoryService(connection).list_stock()
    }


def _movements(connection) -> list:
    return list(
        SQLiteMovementHistory(connection)
        .find_movements(MovementQuery(limit=200))
        .movements
    )


def test_the_quantities_cover_exactly_the_closed_catalog() -> None:
    assert set(INITIAL_STOCK) == {product.product_id for product in SEED_PRODUCTS}
    assert all(
        type(quantity) is int and quantity >= 0 for quantity in INITIAL_STOCK.values()
    )


def test_the_table_includes_low_and_empty_stock_for_demonstrations() -> None:
    assert 0 in INITIAL_STOCK.values()
    assert any(0 < quantity <= 3 for quantity in INITIAL_STOCK.values())


def test_every_catalog_product_gets_its_defined_quantity(connection) -> None:
    result = load_initial_stock(connection)

    active = CatalogService(connection).list_active_product_ids()
    assert result.created == active
    assert result.skipped == ()
    assert _stock(connection) == {pid: INITIAL_STOCK[pid] for pid in active}
    assert find_active_products_without_stock(connection) == ()


def test_each_positive_load_is_an_initialization_movement(connection) -> None:
    load_initial_stock(connection)

    movements = _movements(connection)
    positive = {pid for pid, quantity in INITIAL_STOCK.items() if quantity > 0}
    assert {movement.product_id for movement in movements} == positive
    coca = next(m for m in movements if m.product_id == COCA)
    assert coca.origin == "initialization"
    assert (coca.quantity_before, coca.delta, coca.quantity_after) == (0, 12, 12)
    assert coca.causation_key == f"initial-stock:{COCA}"
    assert coca.operation_id is None
    assert coca.cause["reason"]


def test_reloading_creates_nothing_and_keeps_changed_quantities(connection) -> None:
    load_initial_stock(connection)
    InventoryService(connection).apply_delta(COCA, -5, "unit")
    stock_before = _stock(connection)
    movements_before = len(_movements(connection))

    result = load_initial_stock(connection)

    assert result.created == ()
    assert len(result.skipped) == len(INITIAL_STOCK)
    assert _stock(connection) == stock_before
    assert _stock(connection)[COCA] == 7
    assert len(_movements(connection)) == movements_before
    assert connection.execute("SELECT count(*) FROM inventory_stock").fetchone() == (
        len(INITIAL_STOCK),
    )


def test_only_missing_records_are_created(connection) -> None:
    with transaction(connection):
        connection.execute(
            "INSERT INTO inventory_stock (product_id, quantity, unit) "
            "VALUES (?, 99, 'unit')",
            (COCA,),
        )

    result = load_initial_stock(connection)

    assert COCA in result.skipped
    assert COCA not in result.created
    assert _stock(connection)[COCA] == 99


def test_a_catalog_product_without_quantity_writes_nothing(connection) -> None:
    quantities = dict(INITIAL_STOCK)
    del quantities[COCA]

    with pytest.raises(InitialStockMismatchError) as raised:
        load_initial_stock(connection, quantities)

    assert raised.value.missing == (COCA,)
    assert _stock(connection) == {}


def test_a_quantity_for_an_unknown_product_writes_nothing(connection) -> None:
    quantities = {**INITIAL_STOCK, "fernet-branca-750": 3}

    with pytest.raises(InitialStockMismatchError) as raised:
        load_initial_stock(connection, quantities)

    assert raised.value.unknown == ("fernet-branca-750",)
    assert _stock(connection) == {}


@pytest.mark.parametrize("quantity", [-1, 1.5, "3", True])
def test_inexact_quantities_write_nothing(connection, quantity) -> None:
    with pytest.raises(InvalidQuantityError):
        load_initial_stock(connection, {**INITIAL_STOCK, COCA: quantity})

    assert _stock(connection) == {}


def test_retired_products_are_not_initialized(connection) -> None:
    CatalogService(connection).retire_product(COCA)
    quantities = dict(INITIAL_STOCK)
    del quantities[COCA]

    result = load_initial_stock(connection, quantities)

    assert COCA not in result.created
    assert COCA not in _stock(connection)


def test_a_failure_inside_the_load_rolls_everything_back(connection) -> None:
    connection.execute(
        "CREATE TEMP TRIGGER fail_on_coca BEFORE INSERT ON inventory_stock "
        f"WHEN NEW.product_id = '{COCA}' "
        "BEGIN SELECT RAISE(FAIL, 'disk I/O error'); END"
    )

    with pytest.raises(sqlite3.IntegrityError):
        load_initial_stock(connection)

    assert _stock(connection) == {}
    assert _movements(connection) == []


def test_the_load_joins_the_caller_unit_of_work(connection) -> None:
    with pytest.raises(RuntimeError), transaction(connection):
        load_initial_stock(connection)
        assert connection.in_transaction is True
        raise RuntimeError("the caller rolls back")

    assert _stock(connection) == {}


def test_the_load_survives_reopening_the_database(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    first = connect(path)
    apply_migrations(first)
    load_initial_catalog(first)
    load_initial_stock(first)
    first.close()

    second = connect(path)
    try:
        assert _stock(second) == dict(INITIAL_STOCK)
        assert load_initial_stock(second).created == ()
    finally:
        second.close()


def test_the_database_command_initializes_and_reports(
    tmp_path, capsys, monkeypatch
) -> None:
    path = tmp_path / "data" / "voicestock.sqlite3"
    # The command refuses temporary paths, and tests run under one.
    original = database_cli.open_database
    monkeypatch.setattr(
        database_cli, "open_database", lambda target: original(target, ())
    )

    assert database_cli.main(["init", "--database", str(path)]) == 0
    first = capsys.readouterr().out
    assert database_cli.main(["init", "--database", str(path)]) == 0
    second = capsys.readouterr().out
    assert database_cli.main(["status", "--database", str(path)]) == 0
    status = capsys.readouterr().out

    total = sum(INITIAL_STOCK.values())
    assert f"initial stock: {len(INITIAL_STOCK)} created, 0 already present" in first
    assert f"initial stock: 0 created, {len(INITIAL_STOCK)} already present" in second
    assert "schema version: 5" in status
    assert f"active products: {len(INITIAL_STOCK)}" in status
    assert f"stock records: {len(INITIAL_STOCK)} ({total} units)" in status
    assert "active products without stock: 0" in status


def test_the_database_command_refuses_a_temporary_path(tmp_path, capsys) -> None:
    path = tmp_path / "x.sqlite3"

    assert database_cli.main(["status", "--database", str(path)]) == 2
    assert "does not persist" in capsys.readouterr().err
    assert not path.exists()
