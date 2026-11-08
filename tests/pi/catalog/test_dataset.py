"""The seeded supermarket exercises ADR-0006, including real ambiguity."""

import json

from pi.catalog import CatalogService, SqliteProductResolver, load_initial_catalog
from pi.catalog.seed import SEED_CATEGORIES, SEED_PRODUCTS
from pi.inventory import InventoryService, create_stock_record
from pi.movement_history import MovementOrigin, SQLiteMovementRecorder
from pi.operation_contract import (
    ProductQuery,
    ResolutionStatus,
    ensure_catalog_identifiable,
)
from pi.storage import transaction

# Canonical attributes of the original seed. Aliases may grow; these may not.
ORIGINAL_IDENTITIES = {
    "agua-villavicencio-con-gas-1500": (
        "Agua",
        "Villavicencio",
        "Con gas",
        "1.5 L",
        "bebidas",
    ),
    "agua-villavicencio-sin-gas-1500": (
        "Agua",
        "Villavicencio",
        "Sin gas",
        "1.5 L",
        "bebidas",
    ),
    "cerveza-quilmes-clasica-473": (
        "Cerveza",
        "Quilmes",
        "Clásica",
        "473 ml",
        "bebidas",
    ),
    "cerveza-quilmes-stout-473": ("Cerveza", "Quilmes", "Stout", "473 ml", "bebidas"),
    "gaseosa-coca-cola-original-500": (
        "Gaseosa",
        "Coca-Cola",
        "Original",
        "500 ml",
        "bebidas",
    ),
    "gaseosa-coca-cola-original-2250": (
        "Gaseosa",
        "Coca-Cola",
        "Original",
        "2.25 L",
        "bebidas",
    ),
    "gaseosa-coca-cola-zero-2250": (
        "Gaseosa",
        "Coca-Cola",
        "Zero",
        "2.25 L",
        "bebidas",
    ),
    "gaseosa-sprite-lima-limon-2250": (
        "Gaseosa",
        "Sprite",
        "Lima-Limón",
        "2.25 L",
        "bebidas",
    ),
    "aceite-natura-girasol-900": ("Aceite", "Natura", "Girasol", "900 ml", "almacen"),
    "arroz-gallo-1000": ("Arroz", "Gallo", None, "1 kg", "almacen"),
    "arroz-marolio-1000": ("Arroz", "Marolio", None, "1 kg", "almacen"),
    "azucar-ledesma-1000": ("Azúcar", "Ledesma", None, "1 kg", "almacen"),
    "cafe-la-virginia-250": ("Café", "La Virginia", None, "250 g", "almacen"),
    "fideos-matarazzo-spaghetti-500": (
        "Fideos",
        "Matarazzo",
        "Spaghetti",
        "500 g",
        "almacen",
    ),
    "harina-pureza-000-1000": ("Harina", "Pureza", "000", "1 kg", "almacen"),
    "sal-celusal-fina-500": ("Sal", "Celusal", "Fina", "500 g", "almacen"),
    "yerba-playadito-1000": ("Yerba", "Playadito", None, "1 kg", "almacen"),
    "leche-serenisima-descremada-1000": (
        "Leche",
        "La Serenísima",
        "Descremada",
        "1 L",
        "lacteos",
    ),
    "leche-serenisima-entera-1000": (
        "Leche",
        "La Serenísima",
        "Entera",
        "1 L",
        "lacteos",
    ),
    "yogur-serenisima-vainilla-120": (
        "Yogur",
        "La Serenísima",
        "Vainilla",
        "120 g",
        "lacteos",
    ),
    "detergente-magistral-limon-500": (
        "Detergente",
        "Magistral",
        "Limón",
        "500 ml",
        "limpieza",
    ),
    "jabon-polvo-skip-800": ("Jabón en polvo", "Skip", None, "800 g", "limpieza"),
    "lavandina-ayudin-1000": ("Lavandina", "Ayudín", None, "1 L", "limpieza"),
    "jabon-dove-90": ("Jabón de tocador", "Dove", None, "90 g", "higiene"),
    "papel-higienico-elite-4": ("Papel higiénico", "Elite", None, "4 u", "higiene"),
    "shampoo-sedal-340": ("Shampoo", "Sedal", None, "340 ml", "higiene"),
}


def _identity(product) -> tuple[str, str | None, str | None, str | None, str]:
    return (
        product.name,
        product.brand,
        product.variant,
        product.presentation,
        product.category_id,
    )


def test_the_original_products_keep_their_identities() -> None:
    seeded = {product.product_id: product for product in SEED_PRODUCTS}

    assert ORIGINAL_IDENTITIES.keys() <= seeded.keys()
    for product_id, identity in ORIGINAL_IDENTITIES.items():
        assert _identity(seeded[product_id]) == identity
        assert seeded[product_id].stock_unit == "unit"


def test_every_active_product_is_identifiable_by_its_own_attributes(
    connection,
) -> None:
    load_initial_catalog(connection)
    catalog = CatalogService(connection)
    active = catalog.read_active_catalog()
    resolver = SqliteProductResolver(connection)

    ensure_catalog_identifiable(active)
    assert 70 <= len(active) <= 100
    assert len(catalog.list_active_product_ids()) == len(SEED_PRODUCTS)
    category_ids = {category.category_id for category in SEED_CATEGORIES}
    for product in SEED_PRODUCTS:
        assert product.category_id in category_ids
        assert product.stock_unit == "unit"
        resolution = resolver.resolve(
            ProductQuery(
                product.name,
                brand=product.brand,
                variant=product.variant,
                presentation=product.presentation,
            )
        )
        assert resolution.status is ResolutionStatus.IDENTIFIED
        assert resolution.product is not None
        assert resolution.product.product_id == product.product_id


def test_the_seed_contains_the_required_identity_scenarios(connection) -> None:
    load_initial_catalog(connection)
    resolver = SqliteProductResolver(connection)

    brands = resolver.resolve(ProductQuery("Arroz", presentation="1 kg"))
    presentations = resolver.resolve(ProductQuery("Arroz", brand="Gallo"))
    variants = resolver.resolve(
        ProductQuery("Gaseosa", brand="Coca-Cola", presentation="1.5 L")
    )
    sizes = resolver.resolve(ProductQuery("Gaseosa", brand="Coca-Cola", variant="Zero"))
    combined = resolver.resolve(ProductQuery("Gaseosa", presentation="1.5 L"))
    underspecified = resolver.resolve(ProductQuery("Gaseosa", brand="Coca-Cola"))
    specified = resolver.resolve(
        ProductQuery(
            "Gaseosa",
            brand="Coca-Cola",
            variant="Zero",
            presentation="1.5 L",
        )
    )

    assert brands.status is ResolutionStatus.AMBIGUOUS
    assert {"arroz-gallo-1000", "arroz-marolio-1000", "arroz-dos-hermanos-1000"} <= set(
        brands.candidate_ids
    )
    assert presentations.status is ResolutionStatus.AMBIGUOUS
    assert set(presentations.candidate_ids) == {"arroz-gallo-1000", "arroz-gallo-500"}
    assert variants.status is ResolutionStatus.AMBIGUOUS
    assert set(variants.candidate_ids) == {
        "gaseosa-coca-cola-original-1500",
        "gaseosa-coca-cola-zero-1500",
    }
    assert sizes.status is ResolutionStatus.AMBIGUOUS
    assert {
        "gaseosa-coca-cola-zero-1500",
        "gaseosa-coca-cola-zero-2250",
    } <= set(sizes.candidate_ids)
    assert combined.status is ResolutionStatus.AMBIGUOUS
    assert len(combined.candidate_ids) >= 3
    assert underspecified.status is ResolutionStatus.AMBIGUOUS
    assert specified.status is ResolutionStatus.IDENTIFIED
    assert specified.product is not None
    assert specified.product.product_id == "gaseosa-coca-cola-zero-1500"


def test_a_retired_alias_leaves_the_snapshot_and_is_not_matched(connection) -> None:
    load_initial_catalog(connection)
    catalog = CatalogService(connection)
    catalog.retire_product("gaseosa-coca-cola-zero-1500")

    aliases = {
        alias
        for product in catalog.read_snapshot().products
        for alias in product.aliases
    }
    resolution = SqliteProductResolver(connection).resolve(
        ProductQuery("Coca Zero de litro y medio")
    )

    assert "Coca Zero de litro y medio" not in aliases
    assert resolution.status is ResolutionStatus.UNKNOWN
    assert catalog.get_product("gaseosa-coca-cola-zero-1500").retired is True


def test_expansion_keeps_the_original_seed_stock_and_history(connection) -> None:
    catalog = CatalogService(connection)
    original_categories = {"almacen", "bebidas", "higiene", "lacteos", "limpieza"}
    for category in SEED_CATEGORIES:
        if category.category_id in original_categories:
            catalog.add_category(category)
    for product in SEED_PRODUCTS:
        if product.product_id in ORIGINAL_IDENTITIES:
            catalog.add_product(product)
    with transaction(connection):
        create_stock_record(connection, "yerba-playadito-1000", 4)
        level = InventoryService(connection).apply_delta(
            "yerba-playadito-1000", 2, "unit"
        )
        SQLiteMovementRecorder(connection).record(
            product_id="yerba-playadito-1000",
            delta=2,
            unit="unit",
            quantity_before=4,
            quantity_after=level.quantity,
            origin=MovementOrigin.INITIALIZATION,
            cause={"reason": "carga inicial"},
            causation_key="init-yerba",
        )
    catalog.retire_product("shampoo-sedal-340")

    load_initial_catalog(connection)

    catalog = CatalogService(connection)
    stored = {
        product.product_id: product
        for product in catalog.list_products(include_retired=True)
    }
    assert set(stored) == {product.product_id for product in SEED_PRODUCTS}
    for product_id, identity in ORIGINAL_IDENTITIES.items():
        assert _identity(stored[product_id]) == identity
    assert stored["shampoo-sedal-340"].retired is True
    assert "arroz-dos-hermanos-1000" in catalog.list_active_product_ids()
    assert "shampoo-sedal-340" not in catalog.list_active_product_ids()
    assert (
        InventoryService(connection).get_stock("yerba-playadito-1000").level.quantity
        == 6
    )
    movement = connection.execute(
        "SELECT delta, cause FROM inventory_movements"
    ).fetchone()
    assert movement[0] == 2
    assert json.loads(movement[1]) == {"reason": "carga inicial"}
