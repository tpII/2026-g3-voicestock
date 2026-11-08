"""SQLite product resolution and equivalence with the in-memory resolver."""

from pi.catalog import CatalogService, Product, SqliteProductResolver
from pi.operation_contract import (
    InMemoryProductResolver,
    ProductQuery,
    ResolutionStatus,
)


def _load(catalog: CatalogService) -> None:
    catalog.add_product(
        Product(
            product_id="gaseosa-zero",
            name="Gaseosa",
            brand="Coca-Cola",
            variant="Zero",
            presentation="2.25 L",
            category_id="bebidas",
            aliases=("Coca Zero de dos veinticinco",),
        )
    )
    catalog.add_product(
        Product(
            product_id="gaseosa-original",
            name="Gaseosa",
            brand="Coca-Cola",
            variant="Original",
            presentation="2.25 L",
            category_id="bebidas",
        )
    )
    catalog.add_product(
        Product(
            product_id="arroz-gallo",
            name="Arroz",
            brand="Gallo",
            presentation="1 kg",
            category_id="almacen",
        )
    )


def test_resolution_covers_the_four_statuses(
    connection, catalog: CatalogService
) -> None:
    _load(catalog)
    resolver = SqliteProductResolver(connection)

    identified = resolver.resolve(
        ProductQuery("gaseosa", brand="COCA COLA", variant="zero")
    )
    ambiguous = resolver.resolve(ProductQuery("Gaseosa", brand="Coca-Cola"))
    unknown = resolver.resolve(ProductQuery("Gaseosa", variant="Light"))
    insufficient = resolver.resolve(ProductQuery(None))

    assert identified.status is ResolutionStatus.IDENTIFIED
    assert identified.product is not None
    assert identified.product.product_id == "gaseosa-zero"
    assert identified.product.units == ("unit",)
    assert ambiguous.status is ResolutionStatus.AMBIGUOUS
    assert set(ambiguous.candidate_ids) == {"gaseosa-zero", "gaseosa-original"}
    assert unknown.status is ResolutionStatus.UNKNOWN
    assert insufficient.status is ResolutionStatus.INSUFFICIENT_ATTRIBUTES


def test_sqlite_and_memory_resolvers_agree(connection, catalog: CatalogService) -> None:
    _load(catalog)
    active = catalog.read_active_catalog()
    sqlite_resolver = SqliteProductResolver(connection)
    memory_resolver = InMemoryProductResolver(active)
    queries = (
        ProductQuery("Gaseosa", brand="Coca-Cola", variant="Zero"),
        ProductQuery("Gaseosa"),
        ProductQuery("Arroz", brand="Gallo"),
        ProductQuery("Fideos"),
        ProductQuery(""),
        ProductQuery("Coca Zero de dos veinticinco"),
    )

    for query in queries:
        sqlite_result = sqlite_resolver.resolve(query)
        memory_result = memory_resolver.resolve(query)
        assert sqlite_result.status is memory_result.status
        sqlite_id = (
            None if sqlite_result.product is None else sqlite_result.product.product_id
        )
        memory_id = (
            None if memory_result.product is None else memory_result.product.product_id
        )
        assert sqlite_id == memory_id
        assert set(sqlite_result.candidate_ids) == set(memory_result.candidate_ids)


def test_a_retired_product_is_not_a_candidate(
    connection, catalog: CatalogService
) -> None:
    _load(catalog)
    catalog.retire_product("gaseosa-original")

    resolution = SqliteProductResolver(connection).resolve(
        ProductQuery("Gaseosa", brand="Coca-Cola")
    )

    assert resolution.status is ResolutionStatus.IDENTIFIED
    assert resolution.product is not None
    assert resolution.product.product_id == "gaseosa-zero"


def test_changing_the_category_does_not_change_resolution(
    connection, catalog: CatalogService
) -> None:
    _load(catalog)
    before = SqliteProductResolver(connection).resolve(
        ProductQuery("Arroz", brand="Gallo")
    )
    connection.execute(
        "UPDATE catalog_products SET category_id = 'bebidas' "
        "WHERE product_id = 'arroz-gallo'"
    )

    after = SqliteProductResolver(connection).resolve(
        ProductQuery("Arroz", brand="Gallo")
    )

    assert before.status is ResolutionStatus.IDENTIFIED
    assert after.product == before.product
    assert catalog.get_product("arroz-gallo").category_id == "bebidas"
