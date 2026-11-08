"""Alias storage and its separation from product resolution."""

import pytest

from pi.catalog import (
    AliasConflictError,
    CatalogService,
    InvalidCatalogValueError,
    Product,
    SqliteProductResolver,
)
from pi.operation_contract import ProductQuery, ResolutionStatus


def _gaseosa(product_id: str, variant: str, **changes: object) -> Product:
    values: dict[str, object] = {
        "product_id": product_id,
        "name": "Gaseosa",
        "brand": "Coca-Cola",
        "variant": variant,
        "presentation": "2.25 L",
        "category_id": "bebidas",
        "aliases": (),
    }
    values.update(changes)
    return Product(**values)  # type: ignore[arg-type]


def test_a_product_keeps_several_aliases(catalog: CatalogService) -> None:
    catalog.add_product(
        _gaseosa(
            "gaseosa-zero",
            "Zero",
            aliases=(
                "Coca Zero de dos veinticinco",
                "Coca sin azúcar de dos litros y cuarto",
            ),
        )
    )

    assert catalog.list_aliases("gaseosa-zero") == (
        "Coca sin azúcar de dos litros y cuarto",
        "Coca Zero de dos veinticinco",
    )
    assert catalog.get_product("gaseosa-zero").aliases == catalog.list_aliases(
        "gaseosa-zero"
    )


def test_an_empty_alias_is_rejected(catalog: CatalogService) -> None:
    catalog.add_product(_gaseosa("gaseosa-zero", "Zero"))

    with pytest.raises(InvalidCatalogValueError):
        catalog.add_alias("gaseosa-zero", "  --  ")

    assert catalog.list_aliases("gaseosa-zero") == ()


def test_a_normalized_duplicate_alias_is_stored_once(catalog: CatalogService) -> None:
    catalog.add_product(_gaseosa("gaseosa-zero", "Zero", aliases=("Coca-Cola",)))

    catalog.add_alias("gaseosa-zero", "coca cola")

    assert catalog.list_aliases("gaseosa-zero") == ("Coca-Cola",)


def test_two_active_products_cannot_share_an_alias(catalog: CatalogService) -> None:
    catalog.add_product(_gaseosa("gaseosa-zero", "Zero", aliases=("Coca zero",)))
    catalog.add_product(_gaseosa("gaseosa-original", "Original"))

    with pytest.raises(AliasConflictError, match="gaseosa-zero"):
        catalog.add_alias("gaseosa-original", "Coca-zero")

    assert catalog.list_aliases("gaseosa-original") == ()
    assert catalog.list_aliases("gaseosa-zero") == ("Coca zero",)


def test_aliases_do_not_resolve_a_product(connection, catalog: CatalogService) -> None:
    catalog.add_product(
        _gaseosa(
            "gaseosa-zero",
            "Zero",
            aliases=("Coca Zero de dos veinticinco",),
        )
    )
    resolver = SqliteProductResolver(connection)

    alias_query = resolver.resolve(ProductQuery("Coca Zero de dos veinticinco"))
    canonical = resolver.resolve(
        ProductQuery(
            "Gaseosa", brand="Coca-Cola", variant="Zero", presentation="2.25 L"
        )
    )

    assert alias_query.status is ResolutionStatus.UNKNOWN
    assert canonical.status is ResolutionStatus.IDENTIFIED
    assert canonical.product is not None
    assert canonical.product.product_id == "gaseosa-zero"


def test_retired_aliases_leave_the_active_snapshot(
    catalog: CatalogService,
) -> None:
    catalog.add_product(
        _gaseosa("gaseosa-zero", "Zero", aliases=("Coca Zero de dos veinticinco",))
    )

    catalog.retire_product("gaseosa-zero")
    snapshot = catalog.read_snapshot()

    assert snapshot.products == ()
    assert catalog.list_aliases("gaseosa-zero") == ("Coca Zero de dos veinticinco",)
