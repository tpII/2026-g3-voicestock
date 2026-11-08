"""Domain rules for products, identity and the active-catalog invariant."""

import pytest

from pi.catalog import (
    CatalogService,
    Category,
    DuplicateIdentityError,
    InvalidCatalogValueError,
    Product,
    UnreachableProductError,
)
from pi.catalog.model import STOCK_UNIT


def _product(product_id: str, name: str, **changes: object) -> Product:
    values: dict[str, object] = {
        "product_id": product_id,
        "name": name,
        "category_id": "bebidas",
        "brand": None,
        "variant": None,
        "presentation": None,
        "aliases": (),
    }
    values.update(changes)
    return Product(**values)  # type: ignore[arg-type]


def test_a_product_keeps_optional_attributes_and_a_stable_id() -> None:
    product = Product(
        product_id=" gaseosa-coca-cola-zero-2250 ",
        name=" Gaseosa ",
        brand="Coca-Cola",
        variant="Zero",
        presentation="2.25 L",
        category_id="bebidas",
        stock_unit=STOCK_UNIT,
        retired=False,
        aliases=("Coca Zero de dos veinticinco",),
    )

    assert product.product_id == "gaseosa-coca-cola-zero-2250"
    assert product.name == "Gaseosa"
    assert product.brand == "Coca-Cola"
    assert product.variant == "Zero"
    assert product.presentation == "2.25 L"
    assert product.identity_key() == ("gaseosa", "coca cola", "zero", "2 25 l")


def test_category_and_aliases_are_not_part_of_the_identity() -> None:
    first = _product("a", "Gaseosa", brand="Coca-Cola", aliases=("Coca",))
    second = _product(
        "b",
        "Gaseosa",
        brand="Coca-Cola",
        category_id="almacen",
        aliases=("Gaseosa cola",),
    )

    assert first.identity_key() == second.identity_key()
    assert first.category_id != second.category_id


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "   "},
        {"name": "---"},
        {"product_id": "  "},
        {"category_id": ""},
        {"stock_unit": "kg"},
        {"retired": 0},
        {"aliases": ("---",)},
        {"aliases": ("Coca", "coca")},
    ],
)
def test_invalid_product_values_are_rejected(kwargs: dict) -> None:
    values = {
        "product_id": "gaseosa",
        "name": "Gaseosa",
        "category_id": "bebidas",
    }
    values.update(kwargs)

    with pytest.raises(InvalidCatalogValueError):
        Product(**values)  # type: ignore[arg-type]


def test_a_blank_optional_attribute_is_absent() -> None:
    product = _product("gaseosa", "Gaseosa", brand=" --- ", variant=None)

    assert product.brand is None
    assert product.variant is None


def test_a_category_name_must_survive_normalization() -> None:
    with pytest.raises(InvalidCatalogValueError):
        Category("bebidas", " --- ")


def test_different_brands_variants_and_presentations_can_coexist(
    catalog: CatalogService,
) -> None:
    catalog.add_product(
        _product(
            "gaseosa-coca-original-2250",
            "Gaseosa",
            brand="Coca-Cola",
            variant="Original",
            presentation="2.25 L",
        )
    )
    catalog.add_product(
        _product(
            "gaseosa-coca-zero-2250",
            "Gaseosa",
            brand="Coca-Cola",
            variant="Zero",
            presentation="2.25 L",
        )
    )
    catalog.add_product(
        _product(
            "gaseosa-sprite-2250",
            "Gaseosa",
            brand="Sprite",
            variant="Lima-Limón",
            presentation="2.25 L",
        )
    )
    catalog.add_product(
        _product(
            "gaseosa-coca-original-500",
            "Gaseosa",
            brand="Coca-Cola",
            variant="Original",
            presentation="500 ml",
        )
    )

    assert catalog.list_active_product_ids() == (
        "gaseosa-coca-original-2250",
        "gaseosa-coca-original-500",
        "gaseosa-coca-zero-2250",
        "gaseosa-sprite-2250",
    )


def test_normalized_duplicate_identities_are_rejected(catalog: CatalogService) -> None:
    catalog.add_product(_product("coca", "Coca-Cola", presentation="2.25 L"))

    with pytest.raises(DuplicateIdentityError) as raised:
        catalog.add_product(_product("cola", "coca cola", presentation="2.25 L"))

    assert raised.value.other_product_id == "coca"
    assert catalog.list_active_product_ids() == ("coca",)


def test_a_product_hidden_by_a_more_specific_one_is_rejected(
    catalog: CatalogService,
) -> None:
    catalog.add_product(
        _product("coca-zero", "Gaseosa", brand="Coca-Cola", variant="Zero")
    )

    with pytest.raises(UnreachableProductError, match="coca"):
        catalog.add_product(_product("coca", "Gaseosa", brand="Coca-Cola"))

    assert catalog.list_active_product_ids() == ("coca-zero",)


def test_a_retired_flag_cannot_be_set_by_inserting_the_product(
    catalog: CatalogService,
) -> None:
    with pytest.raises(InvalidCatalogValueError):
        catalog.add_product(_product("coca", "Gaseosa", retired=True))
