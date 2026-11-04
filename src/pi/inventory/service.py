"""Access to the current stock without knowing the SQLite schema.

Consumers such as the confirmation executor or the inventory web page depend
on ``StockReader`` and ``StockWriter``. ``InventoryService`` implements both
on the connection it receives, so reads and changes can take part in the
caller's unit of work. The service applies deltas it is given: it does not
map operations to deltas, record history or touch pending operations, and it
knows nothing about HTTP, the operation cycle or the language model.
"""

import sqlite3
from contextlib import nullcontext
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from pi.inventory.stock import (
    IncompatibleUnitError,
    InsufficientStockError,
    RetiredProductError,
    StockNotInitializedError,
    UnknownProductError,
    check_delta,
)
from pi.storage import transaction


@dataclass(frozen=True)
class StockLevel:
    """Current quantity of one product, counted in its stock unit."""

    product_id: str
    quantity: int
    unit: str
    retired: bool = False


class StockStatus(StrEnum):
    """Outcome of looking up the stock of one product."""

    FOUND = "found"
    UNKNOWN_PRODUCT = "unknown_product"
    NOT_INITIALIZED = "not_initialized"


@dataclass(frozen=True)
class StockLookup:
    """Result of ``get_stock``. Only ``found`` carries a level.

    ``not_initialized`` means the product is in the catalog but its stock was
    never created; it is not reported as zero.
    """

    status: StockStatus
    level: StockLevel | None = None


@runtime_checkable
class StockReader(Protocol):
    """Port the rest of the Raspberry Pi uses to read stock."""

    def get_stock(self, product_id: str) -> StockLookup:
        """Return the stock of one product, or why there is none."""

    def list_stock(self, *, include_retired: bool = False) -> tuple[StockLevel, ...]:
        """Return every stock record, ordered by product id."""


@runtime_checkable
class StockWriter(Protocol):
    """Port that changes stock by an exact, signed delta."""

    def apply_delta(self, product_id: str, delta: int, unit: str) -> StockLevel:
        """Add ``delta`` to the stock of one product and return the new level."""


class InventoryService:
    """``StockReader`` and ``StockWriter`` over the Raspberry Pi database.

    It uses the connection it is given. Reads never open a transaction, so they
    observe the caller's unit of work when there is one. The connection
    belongs to the caller and must not be shared between threads.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get_stock(self, product_id: str) -> StockLookup:
        row = self._connection.execute(
            "SELECT product.retired, stock.quantity, stock.unit "
            "FROM catalog_products AS product "
            "LEFT JOIN inventory_stock AS stock USING (product_id) "
            "WHERE product.product_id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            return StockLookup(StockStatus.UNKNOWN_PRODUCT)
        retired, quantity, unit = row
        if quantity is None:
            return StockLookup(StockStatus.NOT_INITIALIZED)
        return StockLookup(
            StockStatus.FOUND,
            StockLevel(product_id, quantity, unit, bool(retired)),
        )

    def list_stock(self, *, include_retired: bool = False) -> tuple[StockLevel, ...]:
        rows = self._connection.execute(
            "SELECT stock.product_id, stock.quantity, stock.unit, product.retired "
            "FROM inventory_stock AS stock "
            "JOIN catalog_products AS product USING (product_id) "
            "WHERE ? OR product.retired = 0 "
            "ORDER BY stock.product_id",
            (include_retired,),
        ).fetchall()
        return tuple(
            StockLevel(product_id, quantity, unit, bool(retired))
            for product_id, quantity, unit, retired in rows
        )

    def apply_delta(self, product_id: str, delta: int, unit: str) -> StockLevel:
        """Add ``delta`` to the stock of an active product, atomically.

        The change is one conditional ``UPDATE``: it only applies when the
        product is active, ``unit`` is its stock unit and the result is not
        negative, so concurrent changes can never lose an update or go below
        zero. When it does not apply, nothing changes and the error says why.

        Inside a transaction already open on the connection, the change joins
        it and is not committed here: the caller commits or rolls back stock
        and history together, and should open it with
        ``pi.storage.transaction``. Without one, the change runs in its own
        transaction and is committed before returning.
        """
        check_delta(delta)
        if not isinstance(unit, str):
            raise IncompatibleUnitError(f"unit must be a string, got {unit!r}")

        joined = self._connection.in_transaction
        with nullcontext() if joined else transaction(self._connection):
            updated = self._connection.execute(
                "UPDATE inventory_stock SET quantity = quantity + ? "
                "WHERE product_id = ? AND unit = ? AND quantity + ? >= 0 "
                "AND EXISTS (SELECT 1 FROM catalog_products "
                "WHERE product_id = inventory_stock.product_id AND retired = 0)",
                (delta, product_id, unit, delta),
            ).rowcount
            lookup = self.get_stock(product_id)
            if updated != 1:
                raise _rejection(product_id, delta, unit, lookup)
        return lookup.level


def _rejection(
    product_id: str, delta: int, unit: str, lookup: StockLookup
) -> Exception:
    if lookup.status is StockStatus.UNKNOWN_PRODUCT:
        return UnknownProductError(f"product {product_id!r} is not in the catalog")
    if lookup.status is StockStatus.NOT_INITIALIZED:
        return StockNotInitializedError(f"product {product_id!r} has no stock record")
    level = lookup.level
    if level.retired:
        return RetiredProductError(f"product {product_id!r} is retired")
    if unit != level.unit:
        return IncompatibleUnitError(
            f"product {product_id!r} is counted in {level.unit!r}, not {unit!r}"
        )
    return InsufficientStockError(product_id, level.quantity, delta)
