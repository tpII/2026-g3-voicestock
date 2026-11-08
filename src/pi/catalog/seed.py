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
    Category("congelados", "Congelados"),
    Category("conservas", "Conservas"),
    Category("higiene", "Higiene"),
    Category("lacteos", "Lácteos"),
    Category("limpieza", "Limpieza"),
    Category("snacks", "Snacks"),
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
        aliases=("Leche Serenísima descremada",),
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
    _product(
        "gaseosa-coca-cola-original-1500",
        "Gaseosa",
        "bebidas",
        brand="Coca-Cola",
        variant="Original",
        presentation="1.5 L",
        aliases=("Coca común de litro y medio",),
    ),
    _product(
        "gaseosa-coca-cola-zero-1500",
        "Gaseosa",
        "bebidas",
        brand="Coca-Cola",
        variant="Zero",
        presentation="1.5 L",
        aliases=(
            "Coca Zero de litro y medio",
            "Coca sin azúcar de litro y medio",
        ),
    ),
    _product(
        "gaseosa-sprite-lima-limon-1500",
        "Gaseosa",
        "bebidas",
        brand="Sprite",
        variant="Lima-Limón",
        presentation="1.5 L",
    ),
    _product(
        "gaseosa-fanta-naranja-2250",
        "Gaseosa",
        "bebidas",
        brand="Fanta",
        variant="Naranja",
        presentation="2.25 L",
        aliases=("Fanta de naranja",),
    ),
    _product(
        "gaseosa-fanta-naranja-1500",
        "Gaseosa",
        "bebidas",
        brand="Fanta",
        variant="Naranja",
        presentation="1.5 L",
    ),
    _product(
        "agua-villa-del-sur-sin-gas-1500",
        "Agua",
        "bebidas",
        brand="Villa del Sur",
        variant="Sin gas",
        presentation="1.5 L",
    ),
    _product(
        "cerveza-quilmes-clasica-1000",
        "Cerveza",
        "bebidas",
        brand="Quilmes",
        variant="Clásica",
        presentation="1 L",
    ),
    _product(
        "cerveza-andes-roja-473",
        "Cerveza",
        "bebidas",
        brand="Andes",
        variant="Roja",
        presentation="473 ml",
    ),
    _product(
        "jugo-baggio-naranja-1000",
        "Jugo",
        "bebidas",
        brand="Baggio",
        variant="Naranja",
        presentation="1 L",
    ),
    _product(
        "jugo-baggio-manzana-1000",
        "Jugo",
        "bebidas",
        brand="Baggio",
        variant="Manzana",
        presentation="1 L",
    ),
    _product(
        "soda-schweppes-1500",
        "Soda",
        "bebidas",
        brand="Schweppes",
        presentation="1.5 L",
    ),
    _product(
        "soda-cunnington-1500",
        "Soda",
        "bebidas",
        brand="Cunnington",
        presentation="1.5 L",
    ),
    _product(
        "arroz-dos-hermanos-1000",
        "Arroz",
        "almacen",
        brand="Dos Hermanos",
        presentation="1 kg",
    ),
    _product(
        "arroz-gallo-500",
        "Arroz",
        "almacen",
        brand="Gallo",
        presentation="500 g",
        aliases=("Arroz Gallo de medio kilo",),
    ),
    _product(
        "arroz-marolio-500",
        "Arroz",
        "almacen",
        brand="Marolio",
        presentation="500 g",
    ),
    _product(
        "fideos-matarazzo-tirabuzon-500",
        "Fideos",
        "almacen",
        brand="Matarazzo",
        variant="Tirabuzón",
        presentation="500 g",
    ),
    _product(
        "fideos-lucchetti-spaghetti-500",
        "Fideos",
        "almacen",
        brand="Lucchetti",
        variant="Spaghetti",
        presentation="500 g",
    ),
    _product(
        "aceite-natura-girasol-1500",
        "Aceite",
        "almacen",
        brand="Natura",
        variant="Girasol",
        presentation="1.5 L",
    ),
    _product(
        "aceite-cocinero-girasol-900",
        "Aceite",
        "almacen",
        brand="Cocinero",
        variant="Girasol",
        presentation="900 ml",
    ),
    _product(
        "azucar-ledesma-500",
        "Azúcar",
        "almacen",
        brand="Ledesma",
        presentation="500 g",
    ),
    _product(
        "azucar-chango-1000",
        "Azúcar",
        "almacen",
        brand="Chango",
        presentation="1 kg",
    ),
    _product(
        "yerba-playadito-500",
        "Yerba",
        "almacen",
        brand="Playadito",
        presentation="500 g",
    ),
    _product(
        "yerba-taragui-1000",
        "Yerba",
        "almacen",
        brand="Taragüí",
        presentation="1 kg",
        aliases=("Yerba Taragüí",),
    ),
    _product(
        "cafe-nescafe-clasico-170",
        "Café",
        "almacen",
        brand="Nescafé",
        variant="Clásico",
        presentation="170 g",
    ),
    _product(
        "cafe-nescafe-gold-170",
        "Café",
        "almacen",
        brand="Nescafé",
        variant="Gold",
        presentation="170 g",
    ),
    _product(
        "harina-pureza-0000-1000",
        "Harina",
        "almacen",
        brand="Pureza",
        variant="0000",
        presentation="1 kg",
    ),
    _product(
        "harina-blancaflor-000-1000",
        "Harina",
        "almacen",
        brand="Blancaflor",
        variant="000",
        presentation="1 kg",
    ),
    _product(
        "leche-ilolay-entera-1000",
        "Leche",
        "lacteos",
        brand="Ilolay",
        variant="Entera",
        presentation="1 L",
        aliases=("Leche Ilolay entera",),
    ),
    _product(
        "leche-ilolay-descremada-1000",
        "Leche",
        "lacteos",
        brand="Ilolay",
        variant="Descremada",
        presentation="1 L",
    ),
    _product(
        "leche-sancor-entera-1000",
        "Leche",
        "lacteos",
        brand="Sancor",
        variant="Entera",
        presentation="1 L",
    ),
    _product(
        "yogur-serenisima-frutilla-120",
        "Yogur",
        "lacteos",
        brand="La Serenísima",
        variant="Frutilla",
        presentation="120 g",
    ),
    _product(
        "yogur-serenisima-natural-120",
        "Yogur",
        "lacteos",
        brand="La Serenísima",
        variant="Natural",
        presentation="120 g",
    ),
    _product(
        "manteca-la-serenisima-200",
        "Manteca",
        "lacteos",
        brand="La Serenísima",
        presentation="200 g",
    ),
    _product(
        "queso-la-serenisima-cremoso-500",
        "Queso",
        "lacteos",
        brand="La Serenísima",
        variant="Cremoso",
        presentation="500 g",
    ),
    _product(
        "queso-la-serenisima-tybo-500",
        "Queso",
        "lacteos",
        brand="La Serenísima",
        variant="Tybo",
        presentation="500 g",
    ),
    _product(
        "dulce-leche-la-serenisima-400",
        "Dulce de leche",
        "lacteos",
        brand="La Serenísima",
        presentation="400 g",
    ),
    _product(
        "dulce-leche-la-serenisima-1000",
        "Dulce de leche",
        "lacteos",
        brand="La Serenísima",
        presentation="1 kg",
    ),
    _product(
        "detergente-magistral-limon-750",
        "Detergente",
        "limpieza",
        brand="Magistral",
        variant="Limón",
        presentation="750 ml",
    ),
    _product(
        "detergente-magistral-manzana-500",
        "Detergente",
        "limpieza",
        brand="Magistral",
        variant="Manzana",
        presentation="500 ml",
    ),
    _product(
        "detergente-ala-limon-500",
        "Detergente",
        "limpieza",
        brand="Ala",
        variant="Limón",
        presentation="500 ml",
    ),
    _product(
        "lavandina-ayudin-2000",
        "Lavandina",
        "limpieza",
        brand="Ayudín",
        presentation="2 L",
    ),
    _product(
        "lavandina-querubin-1000",
        "Lavandina",
        "limpieza",
        brand="Querubín",
        presentation="1 L",
    ),
    _product(
        "jabon-polvo-ala-800",
        "Jabón en polvo",
        "limpieza",
        brand="Ala",
        presentation="800 g",
    ),
    _product(
        "shampoo-sedal-200",
        "Shampoo",
        "higiene",
        brand="Sedal",
        presentation="200 ml",
    ),
    _product(
        "shampoo-pantene-340",
        "Shampoo",
        "higiene",
        brand="Pantene",
        presentation="340 ml",
    ),
    _product(
        "jabon-lux-90",
        "Jabón de tocador",
        "higiene",
        brand="Lux",
        presentation="90 g",
    ),
    _product(
        "dentifrico-colgate-90",
        "Dentífrico",
        "higiene",
        brand="Colgate",
        presentation="90 g",
    ),
    _product(
        "dentifrico-colgate-180",
        "Dentífrico",
        "higiene",
        brand="Colgate",
        presentation="180 g",
    ),
    _product(
        "galletitas-oreo-original-117",
        "Galletitas",
        "snacks",
        brand="Oreo",
        variant="Original",
        presentation="117 g",
        aliases=("Oreo clásicas",),
    ),
    _product(
        "galletitas-oreo-original-354",
        "Galletitas",
        "snacks",
        brand="Oreo",
        variant="Original",
        presentation="354 g",
    ),
    _product(
        "chocolate-milka-leche-55",
        "Chocolate",
        "snacks",
        brand="Milka",
        variant="Leche",
        presentation="55 g",
    ),
    _product(
        "chocolate-milka-leche-150",
        "Chocolate",
        "snacks",
        brand="Milka",
        variant="Leche",
        presentation="150 g",
    ),
    _product(
        "chocolate-cofler-aireado-55",
        "Chocolate",
        "snacks",
        brand="Cofler",
        variant="Aireado",
        presentation="55 g",
    ),
    _product(
        "papas-fritas-lays-clasicas-40",
        "Papas fritas",
        "snacks",
        brand="Lays",
        variant="Clásicas",
        presentation="40 g",
    ),
    _product(
        "papas-fritas-lays-clasicas-85",
        "Papas fritas",
        "snacks",
        brand="Lays",
        variant="Clásicas",
        presentation="85 g",
        aliases=("Lays clásicas",),
    ),
    _product(
        "papas-fritas-lays-jamon-85",
        "Papas fritas",
        "snacks",
        brand="Lays",
        variant="Jamón",
        presentation="85 g",
    ),
    _product(
        "atun-la-campagnola-natural-170",
        "Atún",
        "conservas",
        brand="La Campagnola",
        variant="Natural",
        presentation="170 g",
        aliases=("Atún al natural",),
    ),
    _product(
        "atun-la-campagnola-aceite-170",
        "Atún",
        "conservas",
        brand="La Campagnola",
        variant="Aceite",
        presentation="170 g",
    ),
    _product(
        "atun-gomes-da-costa-natural-170",
        "Atún",
        "conservas",
        brand="Gomes da Costa",
        variant="Natural",
        presentation="170 g",
    ),
    _product(
        "tomate-arcor-perita-400",
        "Tomate",
        "conservas",
        brand="Arcor",
        variant="Perita",
        presentation="400 g",
    ),
    _product(
        "tomate-molto-triturado-520",
        "Tomate",
        "conservas",
        brand="Molto",
        variant="Triturado",
        presentation="520 g",
    ),
    _product(
        "hamburguesa-paty-clasica-4",
        "Hamburguesa",
        "congelados",
        brand="Paty",
        variant="Clásica",
        presentation="4 u",
        aliases=("Paty de cuatro",),
    ),
    _product(
        "hamburguesa-paty-queso-4",
        "Hamburguesa",
        "congelados",
        brand="Paty",
        variant="Queso",
        presentation="4 u",
    ),
    _product(
        "papas-congeladas-mccain-700",
        "Papas congeladas",
        "congelados",
        brand="McCain",
        presentation="700 g",
    ),
    _product(
        "pizza-sibarita-muzzarella-450",
        "Pizza",
        "congelados",
        brand="Sibarita",
        variant="Muzzarella",
        presentation="450 g",
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
