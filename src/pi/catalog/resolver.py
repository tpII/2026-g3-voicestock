"""SQLite adapter of the product resolution port (ADR-0006).

The adapter only identifies a product. It does not accept or reject an
operation, it does not create products, and it does not read aliases or
stock. ``OperationValidator`` remains responsible for the operation.
"""

import sqlite3

from pi.catalog.store import CatalogService
from pi.operation_contract.products import (
    ProductQuery,
    ProductResolution,
    match_products,
)


class SqliteProductResolver:
    """Resolve ``ProductQuery`` against the active rows of the Pi database.

    The connection belongs to the caller. Resolution does not open a
    transaction and does not commit one that is already open, so it sees the
    caller's uncommitted catalog changes.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._catalog = CatalogService(connection)

    def resolve(self, query: ProductQuery) -> ProductResolution:
        """Apply ADR-0006 matching to complete, non-retired products."""
        return match_products(query, self._catalog.read_active_catalog())
