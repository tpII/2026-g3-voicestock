"""Open a SQLite connection on the thread that is about to use the catalog.

``SqliteProductResolver`` and ``CatalogService`` use the connection they are
given. The integrated runtime calls them from the audio worker and from the
HTTP server, which are not the thread that started the process. Each call
opens its own connection to the same file, uses it, and closes it. Connections
are not shared, and ``check_same_thread`` stays enabled.
"""

import sqlite3
from pathlib import Path

from pi.catalog.resolver import SqliteProductResolver
from pi.catalog.snapshot import CatalogSnapshot
from pi.catalog.store import CatalogService
from pi.operation_contract.products import ProductQuery, ProductResolution
from pi.storage import VOLATILE_ROOTS, connect, open_database


class CatalogNotInitializedError(RuntimeError):
    """The database has a schema and no active products.

    The operational runtime does not load the seed and does not fall back to
    a JSON file. ``voicestock-pi-database init`` is the preparation command.
    """

    def __init__(self) -> None:
        super().__init__(
            "the product catalog has no active products. "
            "Run `voicestock-pi-database init` before `voicestock-pi`. "
            "The runtime does not load the seed."
        )


class OpeningProductResolver:
    """``ProductResolver`` that opens the Pi database on the calling thread."""

    def __init__(self, database_path: Path) -> None:
        self._path = database_path

    def resolve(self, query: ProductQuery) -> ProductResolution:
        """Identify ``query`` and close the connection, including on error."""
        connection = connect(self._path)
        try:
            return _resolve(connection, query)
        finally:
            connection.close()


class OpeningSnapshotReader:
    """``CatalogSnapshotReader`` that opens the Pi database per read."""

    def __init__(self, database_path: Path) -> None:
        self._path = database_path

    def read_snapshot(self) -> CatalogSnapshot:
        """Return the active snapshot and close the connection."""
        connection = connect(self._path)
        try:
            return CatalogService(connection).read_snapshot()
        finally:
            connection.close()


def _resolve(connection: sqlite3.Connection, query: ProductQuery) -> ProductResolution:
    return SqliteProductResolver(connection).resolve(query)


def require_initialized_catalog(
    database_path: Path,
    *,
    volatile_roots: tuple[Path, ...] = VOLATILE_ROOTS,
) -> Path:
    """Migrate ``database_path`` and refuse to start without active products.

    The connection used for the check is closed before returning. Later reads
    open their own connections. This function does not load the seed or stock.
    """
    connection = open_database(database_path, volatile_roots)
    try:
        if not CatalogService(connection).list_active_product_ids():
            raise CatalogNotInitializedError
    finally:
        connection.close()
    return database_path
