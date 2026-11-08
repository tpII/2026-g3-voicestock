"""Database constraints that hold even when a writer bypasses the service."""

import sqlite3

import pytest

from pi.catalog import CatalogService, Product, ProductHasStockError
from pi.inventory import create_stock_record


def _product(product_id: str, *, name: str = "Arroz", brand: str = "Gallo") -> Product:
    return Product(
        product_id=product_id,
        name=name,
        brand=brand,
        presentation="1 kg",
        category_id="almacen",
    )


def test_sql_rejects_retirement_while_stock_is_positive(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("arroz"))
    create_stock_record(connection, "arroz", 4)

    with pytest.raises(sqlite3.IntegrityError, match="positive stock"):
        connection.execute(
            "UPDATE catalog_products SET retired = 1 WHERE product_id = 'arroz'"
        )

    assert catalog.get_product("arroz").retired is False
    assert connection.execute(
        "SELECT quantity FROM inventory_stock WHERE product_id = 'arroz'"
    ).fetchone() == (4,)


def test_the_service_still_reports_positive_stock(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("arroz"))
    create_stock_record(connection, "arroz", 4)

    with pytest.raises(ProductHasStockError) as raised:
        catalog.retire_product("arroz")

    assert raised.value.product_id == "arroz"
    assert raised.value.quantity == 4
    assert catalog.get_product("arroz").retired is False


def test_sql_retires_a_product_with_zero_stock(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("arroz"))
    create_stock_record(connection, "arroz", 0)

    connection.execute(
        "UPDATE catalog_products SET retired = 1 WHERE product_id = 'arroz'"
    )

    assert catalog.get_product("arroz").retired is True
    assert connection.execute(
        "SELECT product_id, quantity FROM inventory_stock"
    ).fetchone() == ("arroz", 0)


def test_sql_retires_a_product_without_a_stock_row(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("arroz"))

    connection.execute(
        "UPDATE catalog_products SET retired = 1 WHERE product_id = 'arroz'"
    )

    assert catalog.get_product("arroz").retired is True
    assert connection.execute("SELECT count(*) FROM inventory_stock").fetchone() == (0,)


def test_sql_cannot_point_an_alias_at_another_active_product(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("gallo"))
    catalog.add_product(_product("marolio", brand="Marolio"))
    catalog.add_alias("gallo", "Arroz de un kilo")
    catalog.add_alias("marolio", "Arroz marolio")

    with pytest.raises(sqlite3.IntegrityError, match="alias belongs"):
        connection.execute(
            "UPDATE catalog_aliases SET alias_key = 'arroz de un kilo' "
            "WHERE product_id = 'marolio'"
        )

    assert catalog.list_aliases("marolio") == ("Arroz marolio",)
    assert catalog.list_aliases("gallo") == ("Arroz de un kilo",)


def test_sql_can_move_an_alias_to_an_active_product_that_lacks_it(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("gallo"))
    catalog.add_product(_product("marolio", brand="Marolio"))
    catalog.add_alias("gallo", "Arroz de un kilo")

    connection.execute(
        "UPDATE catalog_aliases SET product_id = 'marolio' "
        "WHERE product_id = 'gallo' AND alias_key = 'arroz de un kilo'"
    )

    assert catalog.list_aliases("gallo") == ()
    assert catalog.list_aliases("marolio") == ("Arroz de un kilo",)


def test_sql_rejects_activation_that_would_share_an_alias(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("gallo"))
    catalog.add_alias("gallo", "Arroz de un kilo")
    catalog.retire_product("gallo")
    catalog.add_product(_product("marolio", brand="Marolio"))
    catalog.add_alias("marolio", "Arroz de un kilo")

    with pytest.raises(sqlite3.IntegrityError, match="alias belongs"):
        connection.execute(
            "UPDATE catalog_products SET retired = 0 WHERE product_id = 'gallo'"
        )

    assert catalog.get_product("gallo").retired is True
    assert catalog.get_product("marolio").retired is False
    assert catalog.list_aliases("gallo") == ("Arroz de un kilo",)


def test_sql_can_retire_a_product_that_shares_an_alias_with_an_active_one(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("marolio", brand="Marolio"))
    catalog.retire_product("marolio")
    catalog.add_product(_product("gallo"))
    catalog.add_alias("marolio", "Arroz de un kilo")
    catalog.add_alias("gallo", "Arroz de un kilo")

    connection.execute(
        "UPDATE catalog_products SET retired = 1 WHERE product_id = 'gallo'"
    )

    assert catalog.get_product("gallo").retired is True
    assert catalog.list_aliases("gallo") == ("Arroz de un kilo",)
