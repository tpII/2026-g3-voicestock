"""Persistence and lookup of controlled categories."""

from pathlib import Path

import pytest

from pi.catalog import (
    CatalogService,
    Category,
    DuplicateCategoryError,
    Product,
    UnknownCategoryError,
)
from pi.storage import connect, transaction


def test_categories_survive_reopening_the_database(connection, tmp_path: Path) -> None:
    CatalogService(connection).add_category(Category("lacteos", "Lácteos"))

    reopened = connect(tmp_path / "voicestock.sqlite3")
    try:
        categories = CatalogService(reopened).list_categories()
    finally:
        reopened.close()

    assert categories == (Category("lacteos", "Lácteos"),)


def test_a_repeated_category_id_is_rejected(catalog: CatalogService) -> None:
    with pytest.raises(DuplicateCategoryError):
        catalog.add_category(Category("bebidas", "Gaseosas"))

    assert catalog.get_category("bebidas").name == "Bebidas"


def test_normalized_category_names_collide(catalog: CatalogService) -> None:
    with pytest.raises(DuplicateCategoryError, match="almacen"):
        catalog.add_category(Category("almacen-2", "almacen"))

    assert [category.category_id for category in catalog.list_categories()] == [
        "almacen",
        "bebidas",
    ]


def test_a_product_cannot_reference_a_missing_category(
    catalog: CatalogService,
) -> None:
    with pytest.raises(UnknownCategoryError):
        catalog.add_product(
            Product(
                product_id="yerba",
                name="Yerba",
                category_id="inexistente",
                brand="Playadito",
                presentation="1 kg",
            )
        )

    assert catalog.list_active_product_ids() == ()


def test_products_can_be_listed_by_category(catalog: CatalogService) -> None:
    catalog.add_category(Category("lacteos", "Lácteos"))
    catalog.add_product(
        Product(
            product_id="gaseosa",
            name="Gaseosa",
            category_id="bebidas",
            brand="Coca-Cola",
            variant="Zero",
            presentation="2.25 L",
        )
    )
    catalog.add_product(
        Product(
            product_id="yerba",
            name="Yerba",
            category_id="almacen",
            brand="Playadito",
            presentation="1 kg",
        )
    )

    listed = catalog.list_products(category_id="almacen")

    assert [product.product_id for product in listed] == ["yerba"]
    assert catalog.list_products(category_id="lacteos") == ()


def test_an_unknown_category_filter_is_rejected(catalog: CatalogService) -> None:
    with pytest.raises(UnknownCategoryError):
        catalog.list_products(category_id="inexistente")


def test_a_category_write_joins_the_caller_transaction(
    connection, catalog: CatalogService
) -> None:
    with pytest.raises(RuntimeError), transaction(connection):
        catalog.add_category(Category("limpieza", "Limpieza"))
        raise RuntimeError("the caller fails before committing")

    assert [category.category_id for category in catalog.list_categories()] == [
        "almacen",
        "bebidas",
    ]
