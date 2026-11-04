"""Read access to the current stock without knowing the SQLite schema.

Consumers such as the confirmation executor or the inventory web page depend
on ``StockReader``. ``InventoryService`` implements it on the connection it
receives, so a read can take part in the caller's unit of work. The service
knows nothing about HTTP, the operation cycle or the language model.
"""

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable


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


class InventoryService:
    """``StockReader`` over the Raspberry Pi database.

    It uses the connection it is given and never commits or opens a
    transaction, so reads observe the caller's unit of work when there is one.
    The connection belongs to the caller and must not be shared between
    threads.
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
