"""Tests for product identification (ADR-0006)."""

from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from pi.operation_contract import (
    CatalogProduct,
    InMemoryProductResolver,
    ProductQuery,
    ProductResolver,
    ResolutionStatus,
    load_catalog,
    normalize_attribute,
)

CATALOG_PATH = (
    Path(__file__).parents[2]
    / "fixtures"
    / "operation_contract"
    / "october_catalog.json"
)

# Catalog with separate attributes, to exercise brand, variant and presentation.
ATTRIBUTE_CATALOG = (
    CatalogProduct("coca-original-2l", "Coca Cola", None, "Original", "2 L"),
    CatalogProduct("coca-original-15l", "Coca Cola", None, "Original", "1,5 L"),
    CatalogProduct("coca-zero-2l", "Coca Cola", None, "Zero", "2 L"),
    CatalogProduct("arroz-gallo", "Arroz", "Gallo", None, "1 kg"),
    CatalogProduct("arroz-molinos", "Arroz", "Molinos", None, "1 kg"),
    CatalogProduct("leche-serenisima", "Leche", "La Serenísima", None, "1 L"),
)

ResolverFactory = Callable[[Sequence[CatalogProduct]], ProductResolver]

# Every ProductResolver implementation must pass the contract tests below.
RESOLVER_FACTORIES: dict[str, ResolverFactory] = {
    "in_memory": InMemoryProductResolver,
}


@pytest.fixture(params=sorted(RESOLVER_FACTORIES))
def resolver(request: pytest.FixtureRequest) -> ProductResolver:
    return RESOLVER_FACTORIES[request.param](ATTRIBUTE_CATALOG)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Serenísima", "serenisima"),
        ("Coca-Cola", "coca cola"),
        ("  COCA   cola ", "coca cola"),
        ("1,5 L", "1 5 l"),
        ("Ñandú", "nandu"),
        ("", None),
        ("  -- ", None),
        (None, None),
    ],
)
def test_normalization_follows_adr_0006(value: str | None, expected: str | None):
    assert normalize_attribute(value) == expected


def test_normalization_does_not_join_tokens() -> None:
    assert normalize_attribute("1 kg") != normalize_attribute("1kg")


def test_resolver_implements_the_port(resolver: ProductResolver) -> None:
    assert isinstance(resolver, ProductResolver)


@pytest.mark.parametrize(
    ("query", "product_id"),
    [
        (ProductQuery("coca-cola", variant="zero"), "coca-zero-2l"),
        (
            ProductQuery("Coca Cola", variant="Original", presentation="2 L"),
            "coca-original-2l",
        ),
        (ProductQuery("arroz", brand="GALLO"), "arroz-gallo"),
        (ProductQuery("Leche", brand="la serenisima"), "leche-serenisima"),
        (ProductQuery("leche"), "leche-serenisima"),
    ],
)
def test_unique_match_is_identified(
    resolver: ProductResolver, query: ProductQuery, product_id: str
) -> None:
    resolution = resolver.resolve(query)

    assert resolution.status == ResolutionStatus.IDENTIFIED
    assert resolution.product is not None
    assert resolution.product.product_id == product_id


@pytest.mark.parametrize(
    ("query", "candidates"),
    [
        (
            ProductQuery("Coca Cola"),
            {"coca-original-2l", "coca-original-15l", "coca-zero-2l"},
        ),
        (
            ProductQuery("Coca Cola", variant="Original"),
            {"coca-original-2l", "coca-original-15l"},
        ),
        (ProductQuery("arroz"), {"arroz-gallo", "arroz-molinos"}),
        (ProductQuery("arroz", presentation="1 kg"), {"arroz-gallo", "arroz-molinos"}),
    ],
)
def test_several_matches_are_ambiguous_without_tie_breaking(
    resolver: ProductResolver, query: ProductQuery, candidates: set[str]
) -> None:
    resolution = resolver.resolve(query)

    assert resolution.status == ResolutionStatus.AMBIGUOUS
    assert resolution.product is None
    assert set(resolution.candidate_ids) == candidates


@pytest.mark.parametrize(
    "query",
    [
        ProductQuery("Coca Cola", variant="Light"),
        ProductQuery("Pepsi"),
        ProductQuery("Coca"),
        ProductQuery("Coca Cola Zero"),
        ProductQuery("arroz", brand="Gallo", variant="integral"),
        ProductQuery("arroz", presentation="1kg"),
    ],
)
def test_no_match_is_unknown(resolver: ProductResolver, query: ProductQuery) -> None:
    resolution = resolver.resolve(query)

    assert resolution.status == ResolutionStatus.UNKNOWN
    assert resolution.product is None


@pytest.mark.parametrize(
    "query",
    [ProductQuery(None), ProductQuery(""), ProductQuery(" - ", brand="Gallo")],
)
def test_missing_name_is_insufficient(
    resolver: ProductResolver, query: ProductQuery
) -> None:
    resolution = resolver.resolve(query)

    assert resolution.status == ResolutionStatus.INSUFFICIENT_ATTRIBUTES


def test_catalog_rejects_a_product_hidden_by_another() -> None:
    with pytest.raises(ValueError, match="coca"):
        InMemoryProductResolver(
            [
                CatalogProduct("coca", "Coca Cola"),
                CatalogProduct("coca-zero", "Coca Cola", variant="Zero"),
            ]
        )


def test_catalog_rejects_products_with_equal_normalized_attributes() -> None:
    with pytest.raises(ValueError, match="not identifiable"):
        InMemoryProductResolver(
            [CatalogProduct("a", "Coca-Cola"), CatalogProduct("b", "coca cola")]
        )


def test_catalog_rejects_duplicated_ids() -> None:
    with pytest.raises(ValueError, match="duplicated"):
        InMemoryProductResolver(
            [CatalogProduct("a", "Sprite"), CatalogProduct("a", "Fanta")]
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"product_id": "", "name": "Sprite"},
        {"product_id": "sprite", "name": "  "},
        {"product_id": "sprite", "name": "Sprite", "units": ()},
    ],
)
def test_catalog_product_requires_id_name_and_units(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        CatalogProduct(**kwargs)


def test_display_name_comes_from_catalog_attributes() -> None:
    assert ATTRIBUTE_CATALOG[2].display_name == "Coca Cola Zero 2 L"
    assert ATTRIBUTE_CATALOG[5].display_name == "Leche La Serenísima 1 L"


def test_october_catalog_satisfies_the_invariant() -> None:
    products = load_catalog(CATALOG_PATH)

    resolver = InMemoryProductResolver(products)

    assert len(products) == 10
    for product in products:
        resolution = resolver.resolve(ProductQuery(product.name))
        assert resolution.status == ResolutionStatus.IDENTIFIED
        assert resolution.product == product


@pytest.mark.parametrize(
    ("name", "product_id"),
    [
        ("Coca Cola Zero 2L", "coca-cola-zero-2l"),
        ("coca-cola zero 2l", "coca-cola-zero-2l"),
        ("Leche La Serenisima 1L", "leche-la-serenisima-1l"),
        ("Coca Cola 1.5L", "coca-cola-1-5l"),
    ],
)
def test_october_catalog_resolves_model_names(name: str, product_id: str) -> None:
    resolver = InMemoryProductResolver(load_catalog(CATALOG_PATH))

    resolution = resolver.resolve(ProductQuery(name))

    assert resolution.product is not None
    assert resolution.product.product_id == product_id


@pytest.mark.parametrize("name", ["Coca Cola", "Coca Cola Zero", "Sprite"])
def test_october_catalog_rejects_names_without_presentation(name: str) -> None:
    resolver = InMemoryProductResolver(load_catalog(CATALOG_PATH))

    assert resolver.resolve(ProductQuery(name)).status == ResolutionStatus.UNKNOWN
