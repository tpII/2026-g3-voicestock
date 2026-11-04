"""SQLite storage shared by the catalog, the stock and the movement history.

``open_database`` is what the owner process calls: it checks that the file is
on a persistent path, opens it and applies the single migration order.
"""

from pi.storage.database import (
    DATABASE_ENV_VAR,
    VOLATILE_ROOTS,
    VolatileDatabasePathError,
    connect,
    default_database_path,
    ensure_persistent_path,
    transaction,
)
from pi.storage.migrations import (
    MIGRATIONS,
    Migration,
    MigrationHistoryError,
    apply_migrations,
    open_database,
)

__all__ = [
    "DATABASE_ENV_VAR",
    "MIGRATIONS",
    "VOLATILE_ROOTS",
    "Migration",
    "MigrationHistoryError",
    "VolatileDatabasePathError",
    "apply_migrations",
    "connect",
    "default_database_path",
    "ensure_persistent_path",
    "open_database",
    "transaction",
]
