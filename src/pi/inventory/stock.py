"""Stock records: one current quantity per catalog product.

A stock record holds an exact, non-negative integer quantity counted in the
product's stock unit. Every active product must have one. A product without a
record has never had its stock initialized, which is different from zero, so
records are created explicitly with their initial quantity and never by
default. A record outlives the retirement of its product and is never deleted.

These functions join the caller's unit of work: they never commit. The schema
holds no movements and no pending-operation data; those belong to
InventoryMovementHistory and OperationConfirmationExecution.
"""

import sqlite3


class StockRecordError(Exception):
    """A stock record could not be created or changed."""


class UnknownProductError(StockRecordError):
    """The product is not in the catalog."""


class RetiredProductError(StockRecordError):
    """The product was retired from the catalog."""


class StockRecordExistsError(StockRecordError):
    """The product already has a stock record."""


class InvalidQuantityError(StockRecordError, ValueError):
    """The quantity is not an exact, non-negative integer."""


class StockNotInitializedError(StockRecordError):
    """The product is in the catalog but has no stock record yet."""


class IncompatibleUnitError(StockRecordError):
    """The unit is not the stock unit of the product. Nothing is converted."""


class InsufficientStockError(StockRecordError):
    """Applying the delta would leave a negative quantity."""

    def __init__(self, product_id: str, available: int, delta: int) -> None:
        super().__init__(
            f"product {product_id!r} has {available}, cannot apply {delta}"
        )
        self.product_id = product_id
        self.available = available
        self.delta = delta


class InvalidDeltaError(StockRecordError, ValueError):
    """The delta is not an exact, non-zero integer."""


def create_stock_record(
    connection: sqlite3.Connection, product_id: str, quantity: int
) -> None:
    """Create the stock record of an active product with ``quantity``.

    The unit is the product's stock unit from the catalog, so a record can
    never be stored in a unit the product is not counted in.
    """
    check_quantity(quantity)
    row = connection.execute(
        "SELECT retired FROM catalog_products WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    if row is None:
        raise UnknownProductError(f"product {product_id!r} is not in the catalog")
    if row[0]:
        raise RetiredProductError(f"product {product_id!r} is retired")

    try:
        connection.execute(
            "INSERT INTO inventory_stock (product_id, quantity, unit) "
            "SELECT product_id, ?, stock_unit FROM catalog_products "
            "WHERE product_id = ?",
            (quantity, product_id),
        )
    except sqlite3.IntegrityError as error:
        exists = connection.execute(
            "SELECT 1 FROM inventory_stock WHERE product_id = ?", (product_id,)
        ).fetchone()
        if exists is None:
            # Another constraint failed; report it as it is.
            raise
        raise StockRecordExistsError(
            f"product {product_id!r} already has a stock record"
        ) from error


def find_active_products_without_stock(
    connection: sqlite3.Connection,
) -> tuple[str, ...]:
    """Return the active products that break the one-record-each invariant."""
    rows = connection.execute(
        "SELECT product.product_id FROM catalog_products AS product "
        "LEFT JOIN inventory_stock AS stock USING (product_id) "
        "WHERE product.retired = 0 AND stock.product_id IS NULL "
        "ORDER BY product.product_id"
    ).fetchall()
    return tuple(product_id for (product_id,) in rows)


def check_quantity(quantity: object) -> None:
    """Reject anything but an exact integer of zero or more.

    Floats, decimals, numeric strings and booleans are rejected rather than
    converted, so no quantity is ever rounded or reinterpreted.
    """
    if type(quantity) is not int:
        raise InvalidQuantityError(
            f"quantity must be an integer, got {type(quantity).__name__}"
        )
    if quantity < 0:
        raise InvalidQuantityError(f"quantity must not be negative, got {quantity}")


def check_delta(delta: object) -> None:
    """Reject anything but an exact, non-zero integer, positive or negative."""
    if type(delta) is not int:
        raise InvalidDeltaError(f"delta must be an integer, got {type(delta).__name__}")
    if delta == 0:
        raise InvalidDeltaError("delta must not be zero")
