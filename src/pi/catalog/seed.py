"""Initial closed catalog for the test supermarket.

``load_initial_catalog`` inserts categories, products and aliases. Running it
again does not create duplicates, does not change a product id, does not
reset retirement, and does not write stock or movement history. A row that
already exists and does not match the seed is a conflict: nothing in that
call is committed.

The call is one transaction. It joins a transaction the caller already
opened and does not commit that transaction. It must not run while
``voicestock-pi`` has the database open.
"""

import sqlite3

from pi.catalog.errors import (
    AliasConflictError,
    CatalogConflictError,
    DuplicateCategoryError,
    DuplicateIdentityError,
    UnknownCategoryError,
    UnknownProductError,
)
from pi.catalog.model import STOCK_UNIT, Category, Product
from pi.catalog.store import CatalogService
from pi.storage import transaction

SEED_CATEGORIES: tuple[Category, ...] = (
    Category("almacen", "Almacén"),
    Category("bebidas", "Bebidas"),
    Category("higiene", "Higiene"),
    Category("lacteos", "Lácteos"),
    Category("limpieza", "Limpieza"),
)


def _product(
    product_id: str,
    name: str,
    category_id: str,
    *,
    brand: str,
    presentation: str,
    variant: str | None = None,
    aliases: tuple[str, ...] = (),
) -> Product:
    return Product(
        product_id=product_id,
        name=name,
        brand=brand,
        variant=variant,
        presentation=presentation,
        category_id=category_id,
        stock_unit=STOCK_UNIT,
        retired=False,
        aliases=aliases,
    )


SEED_PRODUCTS: tuple[Product, ...] = (
    _product(
        "agua-villavicencio-con-gas-1500",
        "Agua",
        "bebidas",
        brand="Villavicencio",
        variant="Con gas",
        presentation="1.5 L",
    ),
    _product(
        "agua-villavicencio-sin-gas-1500",
        "Agua",
        "bebidas",
        brand="Villavicencio",
        variant="Sin gas",
        presentation="1.5 L",
        aliases=("Villavicencio sin gas",),
    ),
    _product(
        "cerveza-quilmes-clasica-473",
        "Cerveza",
        "bebidas",
        brand="Quilmes",
        variant="Clásica",
        presentation="473 ml",
    ),
    _product(
        "cerveza-quilmes-stout-473",
        "Cerveza",
        "bebidas",
        brand="Quilmes",
        variant="Stout",
        presentation="473 ml",
    ),
    _product(
        "gaseosa-coca-cola-original-500",
        "Gaseosa",
        "bebidas",
        brand="Coca-Cola",
        variant="Original",
        presentation="500 ml",
        aliases=("Coca chica",),
    ),
    _product(
        "gaseosa-coca-cola-original-2250",
        "Gaseosa",
        "bebidas",
        brand="Coca-Cola",
        variant="Original",
        presentation="2.25 L",
        aliases=("Coca común de dos veinticinco",),
    ),
    _product(
        "gaseosa-coca-cola-zero-2250",
        "Gaseosa",
        "bebidas",
        brand="Coca-Cola",
        variant="Zero",
        presentation="2.25 L",
        aliases=(
            "Coca Zero de dos veinticinco",
            "Coca sin azúcar de dos litros y cuarto",
        ),
    ),
    _product(
        "gaseosa-sprite-lima-limon-2250",
        "Gaseosa",
        "bebidas",
        brand="Sprite",
        variant="Lima-Limón",
        presentation="2.25 L",
    ),
    _product(
        "aceite-natura-girasol-900",
        "Aceite",
        "almacen",
        brand="Natura",
        variant="Girasol",
        presentation="900 ml",
    ),
    _product(
        "arroz-gallo-1000",
        "Arroz",
        "almacen",
        brand="Gallo",
        presentation="1 kg",
    ),
    _product(
        "arroz-marolio-1000",
        "Arroz",
        "almacen",
        brand="Marolio",
        presentation="1 kg",
        aliases=("Arroz Marolio de un kilo",),
    ),
    _product(
        "azucar-ledesma-1000",
        "Azúcar",
        "almacen",
        brand="Ledesma",
        presentation="1 kg",
    ),
    _product(
        "cafe-la-virginia-250",
        "Café",
        "almacen",
        brand="La Virginia",
        presentation="250 g",
    ),
    _product(
        "fideos-matarazzo-spaghetti-500",
        "Fideos",
        "almacen",
        brand="Matarazzo",
        variant="Spaghetti",
        presentation="500 g",
    ),
    _product(
        "harina-pureza-000-1000",
        "Harina",
        "almacen",
        brand="Pureza",
        variant="000",
        presentation="1 kg",
    ),
    _product(
        "sal-celusal-fina-500",
        "Sal",
        "almacen",
        brand="Celusal",
        variant="Fina",
        presentation="500 g",
    ),
    _product(
        "yerba-playadito-1000",
        "Yerba",
        "almacen",
        brand="Playadito",
        presentation="1 kg",
        aliases=("Playadito",),
    ),
    _product(
        "leche-serenisima-descremada-1000",
        "Leche",
        "lacteos",
        brand="La Serenísima",
        variant="Descremada",
        presentation="1 L",
    ),
    _product(
        "leche-serenisima-entera-1000",
        "Leche",
        "lacteos",
        brand="La Serenísima",
        variant="Entera",
        presentation="1 L",
        aliases=("Leche entera de un litro",),
    ),
    _product(
        "yogur-serenisima-vainilla-120",
        "Yogur",
        "lacteos",
        brand="La Serenísima",
        variant="Vainilla",
        presentation="120 g",
    ),
    _product(
        "detergente-magistral-limon-500",
        "Detergente",
        "limpieza",
        brand="Magistral",
        variant="Limón",
        presentation="500 ml",
        aliases=("Magistral de medio litro",),
    ),
    _product(
        "jabon-polvo-skip-800",
        "Jabón en polvo",
        "limpieza",
        brand="Skip",
        presentation="800 g",
    ),
    _product(
        "lavandina-ayudin-1000",
        "Lavandina",
        "limpieza",
        brand="Ayudín",
        presentation="1 L",
    ),
    _product(
        "jabon-dove-90",
        "Jabón de tocador",
        "higiene",
        brand="Dove",
        presentation="90 g",
    ),
    _product(
        "papel-higienico-elite-4",
        "Papel higiénico",
        "higiene",
        brand="Elite",
        presentation="4 u",
    ),
    _product(
        "shampoo-sedal-340",
        "Shampoo",
        "higiene",
        brand="Sedal",
        presentation="340 ml",
    ),
)


def load_initial_catalog(connection: sqlite3.Connection) -> None:
    """Load the seed into an already migrated database.

    Stop ``voicestock-pi`` before running this against the database that
    process owns. The function does not open a second database and does not
    apply migrations; the caller does both. A failure rolls back every row
    this call inserted.
    """
    service = CatalogService(connection)
    if connection.in_transaction:
        _apply_seed(service)
        return
    with transaction(connection):
        _apply_seed(service)


def _apply_seed(service: CatalogService) -> None:
    for category in SEED_CATEGORIES:
        _load_category(service, category)
    for product in SEED_PRODUCTS:
        _load_product(service, product)


def _load_category(service: CatalogService, category: Category) -> None:
    try:
        current = service.get_category(category.category_id)
    except UnknownCategoryError:
        try:
            service.add_category(category)
        except DuplicateCategoryError as error:
            raise CatalogConflictError(str(error)) from error
        return
    if current.name != category.name:
        raise CatalogConflictError(
            f"category {category.category_id!r} is named {current.name!r}, "
            f"not {category.name!r}"
        )


def _load_product(service: CatalogService, product: Product) -> None:
    try:
        current = service.get_product(product.product_id)
    except UnknownProductError as error:
        if error.provisional:
            raise CatalogConflictError(
                f"product {product.product_id!r} is a provisional catalog row "
                "and was not overwritten"
            ) from error
        try:
            service.add_product(product)
        except DuplicateIdentityError as error:
            raise CatalogConflictError(str(error)) from error
        return
    if not _same_definition(current, product):
        raise CatalogConflictError(
            f"product {product.product_id!r} does not match the seed identity"
        )
    for alias in product.aliases:
        try:
            service.add_alias(product.product_id, alias)
        except AliasConflictError as error:
            raise CatalogConflictError(str(error)) from error


def _same_definition(stored: Product, seeded: Product) -> bool:
    return (
        stored.name == seeded.name
        and stored.brand == seeded.brand
        and stored.variant == seeded.variant
        and stored.presentation == seeded.presentation
        and stored.category_id == seeded.category_id
        and stored.stock_unit == seeded.stock_unit
    )
