"""Idempotence and conflict handling of the initial catalog seed."""

import json

import pytest

from pi.catalog import (
    CatalogConflictError,
    CatalogService,
    Category,
    Product,
    load_initial_catalog,
)
from pi.catalog.seed import SEED_CATEGORIES, SEED_PRODUCTS
from pi.inventory import InventoryService, create_stock_record
from pi.movement_history import MovementOrigin, SQLiteMovementRecorder
from pi.storage import transaction


def test_the_seed_is_a_small_closed_supermarket() -> None:
    alias_count = sum(len(product.aliases) for product in SEED_PRODUCTS)
    products_without_aliases = [
        product.product_id for product in SEED_PRODUCTS if not product.aliases
    ]

    assert 20 <= len(SEED_PRODUCTS) <= 30
    assert len(SEED_CATEGORIES) == 5
    assert alias_count >= 8
    assert products_without_aliases
    assert all(product.stock_unit == "unit" for product in SEED_PRODUCTS)
    assert len({product.product_id for product in SEED_PRODUCTS}) == len(SEED_PRODUCTS)


def test_the_first_load_is_complete_and_repeatable(connection) -> None:
    load_initial_catalog(connection)
    ids = CatalogService(connection).list_active_product_ids()

    load_initial_catalog(connection)

    catalog = CatalogService(connection)
    assert ids == catalog.list_active_product_ids()
    assert ids == tuple(sorted(product.product_id for product in SEED_PRODUCTS))
    assert "gaseosa-coca-cola-zero-2250" in ids
    assert [category.category_id for category in catalog.list_categories()] == [
        category.category_id for category in SEED_CATEGORIES
    ]
    zero = catalog.get_product("gaseosa-coca-cola-zero-2250")
    assert set(zero.aliases) == {
        "Coca Zero de dos veinticinco",
        "Coca sin azúcar de dos litros y cuarto",
    }
    assert catalog.list_aliases("arroz-gallo-1000") == ()
    assert connection.execute("SELECT count(*) FROM inventory_stock").fetchone() == (0,)
    assert connection.execute(
        "SELECT count(*) FROM inventory_movements"
    ).fetchone() == (0,)


def test_a_conflicting_identity_is_rejected_without_a_partial_seed(
    connection,
) -> None:
    catalog = CatalogService(connection)
    catalog.add_category(Category("bebidas", "Bebidas"))
    catalog.add_product(
        Product(
            product_id="gaseosa-coca-cola-zero-2250",
            name="Otra cosa",
            brand="Otra",
            presentation="1 L",
            category_id="bebidas",
        )
    )

    with pytest.raises(CatalogConflictError, match="gaseosa-coca-cola-zero-2250"):
        load_initial_catalog(connection)

    assert catalog.list_active_product_ids() == ("gaseosa-coca-cola-zero-2250",)
    assert catalog.get_product("gaseosa-coca-cola-zero-2250").name == "Otra cosa"
    assert [category.category_id for category in catalog.list_categories()] == [
        "bebidas"
    ]


def test_a_provisional_row_is_not_completed_by_the_seed(connection) -> None:
    connection.execute(
        "INSERT INTO catalog_products (product_id, stock_unit) "
        "VALUES ('gaseosa-coca-cola-zero-2250', 'unit')"
    )

    with pytest.raises(CatalogConflictError, match="provisional"):
        load_initial_catalog(connection)

    assert CatalogService(connection).list_provisional_product_ids() == (
        "gaseosa-coca-cola-zero-2250",
    )
    assert CatalogService(connection).list_active_product_ids() == ()


def test_the_seed_preserves_retirement_stock_and_history(connection) -> None:
    load_initial_catalog(connection)
    product_id = "yerba-playadito-1000"
    with transaction(connection):
        create_stock_record(connection, product_id, 4)
        level = InventoryService(connection).apply_delta(product_id, 2, "unit")
        SQLiteMovementRecorder(connection).record(
            product_id=product_id,
            delta=2,
            unit="unit",
            quantity_before=4,
            quantity_after=level.quantity,
            origin=MovementOrigin.INITIALIZATION,
            cause={"reason": "carga inicial"},
            causation_key="init-yerba",
        )
    CatalogService(connection).retire_product("shampoo-sedal-340")

    load_initial_catalog(connection)

    catalog = CatalogService(connection)
    assert catalog.get_product("shampoo-sedal-340").retired is True
    assert InventoryService(connection).get_stock(product_id).level.quantity == 6
    movement = connection.execute(
        "SELECT movement_id, delta, cause FROM inventory_movements"
    ).fetchone()
    assert movement[1] == 2
    assert json.loads(movement[2]) == {"reason": "carga inicial"}
    assert catalog.list_active_product_ids().count("shampoo-sedal-340") == 0
