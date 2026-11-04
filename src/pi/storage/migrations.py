"""Single, ordered schema history of the Raspberry Pi database.

Catalog, stock and history share one list of migrations. A migration is never
edited once it reaches ``develop``: a schema change is a new migration at the
end of the list. ``apply_migrations`` can run on every start: it applies only
what is missing, all in one transaction, and refuses a database whose history
does not match this list.
"""

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from pi.storage.database import (
    VOLATILE_ROOTS,
    connect,
    ensure_persistent_path,
    transaction,
)


@dataclass(frozen=True)
class Migration:
    """One schema step, identified by its position and name."""

    version: int
    name: str
    statements: tuple[str, ...]


class MigrationHistoryError(RuntimeError):
    """The database was migrated with a history this code does not know."""


# Minimal catalog table for stock to reference. ProductCatalog-02 extends it
# with the identity attributes through later migrations; product_id is the
# stable key stock and history refer to and is never reused.
_CATALOG_PRODUCTS = Migration(
    version=1,
    name="create_catalog_products",
    statements=(
        """
        CREATE TABLE catalog_products (
            product_id TEXT NOT NULL PRIMARY KEY
                CHECK (typeof(product_id) = 'text'
                       AND length(trim(product_id)) > 0),
            stock_unit TEXT NOT NULL
                CHECK (typeof(stock_unit) = 'text'
                       AND length(trim(stock_unit)) > 0),
            retired INTEGER NOT NULL DEFAULT 0 CHECK (retired IN (0, 1)),
            UNIQUE (product_id, stock_unit)
        )
        """,
    ),
)

# Current quantity of each catalog product, counted in its stock unit. A
# missing row means the stock was never initialized, which is not zero.
_INVENTORY_STOCK = Migration(
    version=2,
    name="create_inventory_stock",
    statements=(
        """
        CREATE TABLE inventory_stock (
            product_id TEXT NOT NULL PRIMARY KEY,
            quantity INTEGER NOT NULL
                CHECK (typeof(quantity) = 'integer' AND quantity >= 0),
            unit TEXT NOT NULL,
            FOREIGN KEY (product_id, unit)
                REFERENCES catalog_products (product_id, stock_unit)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        )
        """,
        """
        CREATE TRIGGER inventory_stock_requires_active_product
        BEFORE INSERT ON inventory_stock
        WHEN (SELECT retired FROM catalog_products
              WHERE product_id = NEW.product_id) = 1
        BEGIN
            SELECT RAISE(ABORT, 'product is retired');
        END
        """,
        """
        CREATE TRIGGER inventory_stock_keeps_identity
        BEFORE UPDATE OF product_id, unit ON inventory_stock
        WHEN NEW.product_id IS NOT OLD.product_id OR NEW.unit IS NOT OLD.unit
        BEGIN
            SELECT RAISE(ABORT, 'stock product and unit cannot change');
        END
        """,
        """
        CREATE TRIGGER inventory_stock_is_never_deleted
        BEFORE DELETE ON inventory_stock
        BEGIN
            SELECT RAISE(ABORT, 'stock records are never deleted');
        END
        """,
    ),
)

# Append-only history of stock movements. ``sequence`` is the total order:
# the Pi has no real-time clock, so ``recorded_at`` can go backwards and is
# never used to order. A movement carries its balance before and after and a
# JSON snapshot of its cause, so it explains itself without reading stock or
# the pending operation. ``causation_key`` makes a cause idempotent; for voice
# it is the operation id, for other origins it is optional.
_INVENTORY_MOVEMENTS = Migration(
    version=3,
    name="create_inventory_movements",
    statements=(
        """
        CREATE TABLE inventory_movements (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            movement_id TEXT NOT NULL UNIQUE
                CHECK (typeof(movement_id) = 'text'
                       AND length(trim(movement_id)) > 0),
            product_id TEXT NOT NULL,
            delta INTEGER NOT NULL
                CHECK (typeof(delta) = 'integer' AND delta <> 0),
            unit TEXT NOT NULL,
            quantity_before INTEGER NOT NULL
                CHECK (typeof(quantity_before) = 'integer'
                       AND quantity_before >= 0),
            quantity_after INTEGER NOT NULL
                CHECK (typeof(quantity_after) = 'integer'
                       AND quantity_after >= 0),
            origin TEXT NOT NULL
                CHECK (origin IN
                       ('voice_operation', 'manual_adjustment', 'initialization')),
            operation_id TEXT
                CHECK (operation_id IS NULL
                       OR (typeof(operation_id) = 'text'
                           AND length(trim(operation_id)) > 0)),
            causation_key TEXT
                CHECK (causation_key IS NULL
                       OR (typeof(causation_key) = 'text'
                           AND length(trim(causation_key)) > 0)),
            recorded_at TEXT NOT NULL
                CHECK (recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T'
                                        || '[0-2][0-9]:[0-5][0-9]:[0-5][0-9].'
                                        || '[0-9][0-9][0-9][0-9][0-9][0-9]Z'),
            cause TEXT NOT NULL
                CHECK (json_valid(cause) AND json_type(cause) = 'object'
                       AND cause <> '{}'),
            CHECK (quantity_after = quantity_before + delta),
            CHECK ((origin = 'voice_operation') = (operation_id IS NOT NULL)),
            CHECK (origin <> 'voice_operation' OR causation_key IS operation_id),
            UNIQUE (origin, causation_key),
            FOREIGN KEY (product_id, unit)
                REFERENCES catalog_products (product_id, stock_unit)
                ON UPDATE RESTRICT ON DELETE RESTRICT
        )
        """,
        "CREATE INDEX inventory_movements_by_product "
        "ON inventory_movements (product_id, sequence)",
        "CREATE INDEX inventory_movements_by_operation "
        "ON inventory_movements (operation_id, sequence) "
        "WHERE operation_id IS NOT NULL",
        "CREATE INDEX inventory_movements_by_origin "
        "ON inventory_movements (origin, sequence)",
        "CREATE INDEX inventory_movements_by_time "
        "ON inventory_movements (recorded_at, sequence)",
        """
        CREATE TRIGGER inventory_movements_are_never_updated
        BEFORE UPDATE ON inventory_movements
        BEGIN
            SELECT RAISE(ABORT, 'inventory movements are append-only');
        END
        """,
        """
        CREATE TRIGGER inventory_movements_are_never_deleted
        BEFORE DELETE ON inventory_movements
        BEGIN
            SELECT RAISE(ABORT, 'inventory movements are append-only');
        END
        """,
    ),
)

MIGRATIONS: tuple[Migration, ...] = (
    _CATALOG_PRODUCTS,
    _INVENTORY_STOCK,
    _INVENTORY_MOVEMENTS,
)


def apply_migrations(
    connection: sqlite3.Connection,
    migrations: Sequence[Migration] = MIGRATIONS,
) -> tuple[int, ...]:
    """Bring the schema up to date and return the versions applied now.

    Either every pending migration is applied or none is.
    """
    _check_sequence(migrations)
    with transaction(connection):
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER NOT NULL PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """
        )
        applied = connection.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
        known = [(migration.version, migration.name) for migration in migrations]
        if applied != known[: len(applied)]:
            raise MigrationHistoryError(
                f"database history {applied} does not match the known "
                f"migrations {known}"
            )

        pending = migrations[len(applied) :]
        for migration in pending:
            for statement in migration.statements:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) "
                "VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
                (migration.version, migration.name),
            )
    return tuple(migration.version for migration in pending)


def open_database(
    path: Path | str, volatile_roots: tuple[Path, ...] = VOLATILE_ROOTS
) -> sqlite3.Connection:
    """Open the owner process's database on a persistent path, migrated.

    It is the entry point of ``voicestock-pi``. A path in memory or under a
    temporary directory is rejected before any file is created.
    """
    connection = connect(ensure_persistent_path(path, volatile_roots))
    try:
        apply_migrations(connection)
    except BaseException:
        connection.close()
        raise
    return connection


def _check_sequence(migrations: Sequence[Migration]) -> None:
    versions = [migration.version for migration in migrations]
    if versions != list(range(1, len(versions) + 1)):
        raise ValueError(f"migration versions must be 1..n in order: {versions}")
