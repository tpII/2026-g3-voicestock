"""The catalog gives inventory initialization a stable list of product ids."""

from pi.catalog import CatalogService, load_initial_catalog
from pi.catalog.seed import SEED_PRODUCTS
from pi.inventory import (
    InventoryService,
    StockStatus,
    create_stock_record,
    find_active_products_without_stock,
)
from pi.storage import transaction


def _initialize_missing(connection, quantity: int) -> tuple[str, ...]:
    """Create stock only for active catalog products that do not have it."""
    catalog = CatalogService(connection)
    created: list[str] = []
    with transaction(connection):
        for product_id in catalog.list_active_product_ids():
            lookup = InventoryService(connection).get_stock(product_id)
            if lookup.status is not StockStatus.NOT_INITIALIZED:
                continue
            create_stock_record(connection, product_id, quantity)
            created.append(product_id)
    return tuple(created)


def test_missing_stock_can_be_created_once_from_catalog_ids(connection) -> None:
    load_initial_catalog(connection)
    catalog = CatalogService(connection)
    expected = tuple(sorted(product.product_id for product in SEED_PRODUCTS))

    assert catalog.list_active_product_ids() == expected
    assert find_active_products_without_stock(connection) == expected
    assert catalog.list_provisional_product_ids() == ()

    created = _initialize_missing(connection, 5)
    InventoryService(connection).apply_delta(expected[0], 4, "unit")
    again = _initialize_missing(connection, 5)

    assert created == expected
    assert again == ()
    assert find_active_products_without_stock(connection) == ()
    assert InventoryService(connection).get_stock(expected[0]).level.quantity == 9
    assert InventoryService(connection).get_stock(expected[1]).level.quantity == 5


def test_provisional_rows_are_not_part_of_the_catalog_enumeration(
    connection,
) -> None:
    connection.execute(
        "INSERT INTO catalog_products (product_id, stock_unit) "
        "VALUES ('legacy-product', 'unit')"
    )
    load_initial_catalog(connection)
    catalog = CatalogService(connection)

    assert "legacy-product" not in catalog.list_active_product_ids()
    assert "legacy-product" in find_active_products_without_stock(connection)
    assert catalog.list_provisional_product_ids() == ("legacy-product",)
