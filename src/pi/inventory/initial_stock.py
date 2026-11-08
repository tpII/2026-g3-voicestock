"""Initial stock of the test supermarket, loaded once per product.

``INITIAL_STOCK`` gives one exact quantity to every product of the closed
catalog seed (``pi.catalog.seed``). ``load_initial_stock`` creates the stock
record of each active product that has none yet and records the matching
``initialization`` movement in the history, both in one unit of work.

The load is idempotent and never destructive: a product that already has a
record is skipped, whatever its quantity is now, so running it again never
resets stock that operations already changed. There is no reset. Stock
records are never deleted and the history is append-only, so starting over is
deleting the database file on a development machine, explicitly, with
``voicestock-pi`` stopped.
"""

import sqlite3
from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from types import MappingProxyType

from pi.catalog import CatalogService
from pi.inventory.service import InventoryService, StockStatus
from pi.inventory.stock import (
    StockRecordError,
    check_quantity,
    create_stock_record,
)
from pi.movement_history import MovementOrigin, SQLiteMovementRecorder
from pi.storage import transaction

INITIAL_STOCK_REASON = "carga inicial de existencias del supermercado de prueba"

# Representative quantities for the demonstrations and tests of November.
# Fast movers get more units, bulky or expensive products fewer. A few
# products start low or at zero so a removal can be rejected for lack of stock.
INITIAL_STOCK: Mapping[str, int] = MappingProxyType(
    {
        # bebidas
        "agua-villa-del-sur-sin-gas-1500": 24,
        "agua-villavicencio-con-gas-1500": 18,
        "agua-villavicencio-sin-gas-1500": 24,
        "cerveza-andes-roja-473": 18,
        "cerveza-quilmes-clasica-1000": 12,
        "cerveza-quilmes-clasica-473": 36,
        "cerveza-quilmes-stout-473": 12,
        "gaseosa-coca-cola-original-1500": 18,
        "gaseosa-coca-cola-original-2250": 24,
        "gaseosa-coca-cola-original-500": 30,
        "gaseosa-coca-cola-zero-1500": 12,
        "gaseosa-coca-cola-zero-2250": 12,
        "gaseosa-fanta-naranja-1500": 10,
        "gaseosa-fanta-naranja-2250": 12,
        "gaseosa-sprite-lima-limon-1500": 10,
        "gaseosa-sprite-lima-limon-2250": 12,
        "jugo-baggio-manzana-1000": 15,
        "jugo-baggio-naranja-1000": 15,
        "soda-cunnington-1500": 12,
        "soda-schweppes-1500": 8,
        # almacen
        "aceite-cocinero-girasol-900": 10,
        "aceite-natura-girasol-1500": 8,
        "aceite-natura-girasol-900": 14,
        "arroz-dos-hermanos-1000": 10,
        "arroz-gallo-1000": 20,
        "arroz-gallo-500": 15,
        "arroz-marolio-1000": 15,
        "arroz-marolio-500": 12,
        "azucar-chango-1000": 10,
        "azucar-ledesma-1000": 20,
        "azucar-ledesma-500": 12,
        "cafe-la-virginia-250": 10,
        "cafe-nescafe-clasico-170": 8,
        "cafe-nescafe-gold-170": 4,
        "fideos-lucchetti-spaghetti-500": 20,
        "fideos-matarazzo-spaghetti-500": 25,
        "fideos-matarazzo-tirabuzon-500": 20,
        "harina-blancaflor-000-1000": 12,
        "harina-pureza-0000-1000": 12,
        "harina-pureza-000-1000": 15,
        "sal-celusal-fina-500": 12,
        "yerba-playadito-1000": 18,
        "yerba-playadito-500": 12,
        "yerba-taragui-1000": 15,
        # lacteos
        "dulce-leche-la-serenisima-1000": 4,
        "dulce-leche-la-serenisima-400": 10,
        "leche-ilolay-descremada-1000": 10,
        "leche-ilolay-entera-1000": 12,
        "leche-sancor-entera-1000": 12,
        "leche-serenisima-descremada-1000": 18,
        "leche-serenisima-entera-1000": 24,
        "manteca-la-serenisima-200": 8,
        "queso-la-serenisima-cremoso-500": 5,
        "queso-la-serenisima-tybo-500": 3,
        "yogur-serenisima-frutilla-120": 16,
        "yogur-serenisima-natural-120": 0,
        "yogur-serenisima-vainilla-120": 16,
        # limpieza
        "detergente-ala-limon-500": 10,
        "detergente-magistral-limon-500": 15,
        "detergente-magistral-limon-750": 10,
        "detergente-magistral-manzana-500": 8,
        "jabon-polvo-ala-800": 6,
        "jabon-polvo-skip-800": 8,
        "lavandina-ayudin-1000": 15,
        "lavandina-ayudin-2000": 8,
        "lavandina-querubin-1000": 10,
        # higiene
        "dentifrico-colgate-180": 6,
        "dentifrico-colgate-90": 12,
        "jabon-dove-90": 12,
        "jabon-lux-90": 15,
        "papel-higienico-elite-4": 20,
        "shampoo-pantene-340": 6,
        "shampoo-sedal-200": 8,
        "shampoo-sedal-340": 10,
        # snacks
        "chocolate-cofler-aireado-55": 20,
        "chocolate-milka-leche-150": 8,
        "chocolate-milka-leche-55": 20,
        "galletitas-oreo-original-117": 24,
        "galletitas-oreo-original-354": 10,
        "papas-fritas-lays-clasicas-40": 30,
        "papas-fritas-lays-clasicas-85": 15,
        "papas-fritas-lays-jamon-85": 10,
        # conservas
        "atun-gomes-da-costa-natural-170": 8,
        "atun-la-campagnola-aceite-170": 10,
        "atun-la-campagnola-natural-170": 12,
        "tomate-arcor-perita-400": 18,
        "tomate-molto-triturado-520": 12,
        # congelados
        "hamburguesa-paty-clasica-4": 8,
        "hamburguesa-paty-queso-4": 2,
        "papas-congeladas-mccain-700": 6,
        "pizza-sibarita-muzzarella-450": 5,
    }
)


class InitialStockMismatchError(StockRecordError):
    """The quantity table and the active catalog name different products."""

    def __init__(self, missing: tuple[str, ...], unknown: tuple[str, ...]) -> None:
        super().__init__(
            f"initial stock does not match the active catalog: "
            f"without quantity {list(missing)}, not in the catalog {list(unknown)}"
        )
        self.missing = missing
        self.unknown = unknown


@dataclass(frozen=True)
class InitialStockResult:
    """Products whose stock was created now, and those that already had it."""

    created: tuple[str, ...]
    skipped: tuple[str, ...]


def load_initial_stock(
    connection: sqlite3.Connection,
    quantities: Mapping[str, int] = INITIAL_STOCK,
) -> InitialStockResult:
    """Create the missing stock records of the active catalog.

    Every active catalog product must have a quantity and every quantity must
    name an active product; otherwise nothing is written. Each created record
    with a positive quantity gets one ``initialization`` movement whose
    causation key is ``initial-stock:<product_id>``. A record created with zero
    gets no movement, because a movement always changes stock.

    Inside a transaction already open on the connection, the load joins it and
    does not commit. Otherwise it runs in its own transaction. Run it after
    ``pi.catalog.load_initial_catalog`` and never while ``voicestock-pi`` has
    the file open.
    """
    active = CatalogService(connection).list_active_product_ids()
    for quantity in quantities.values():
        check_quantity(quantity)
    missing = tuple(sorted(set(active) - set(quantities)))
    unknown = tuple(sorted(set(quantities) - set(active)))
    if missing or unknown:
        raise InitialStockMismatchError(missing, unknown)

    stock = InventoryService(connection)
    recorder = SQLiteMovementRecorder(connection)
    created: list[str] = []
    skipped: list[str] = []
    joined = connection.in_transaction
    with nullcontext() if joined else transaction(connection):
        for product_id in active:
            if stock.get_stock(product_id).status is not StockStatus.NOT_INITIALIZED:
                skipped.append(product_id)
                continue
            quantity = quantities[product_id]
            create_stock_record(connection, product_id, quantity)
            created.append(product_id)
            if quantity == 0:
                continue
            recorder.record(
                product_id=product_id,
                delta=quantity,
                unit=stock.get_stock(product_id).level.unit,
                quantity_before=0,
                quantity_after=quantity,
                origin=MovementOrigin.INITIALIZATION,
                causation_key=f"initial-stock:{product_id}",
                cause={"reason": INITIAL_STOCK_REASON, "source": __name__},
            )
    return InitialStockResult(tuple(created), tuple(skipped))
