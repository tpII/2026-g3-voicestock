"""Prepare and inspect the Raspberry Pi database: ``voicestock-pi-database``.

``init`` opens the database on its persistent path, applies the migrations,
loads the closed catalog and creates the missing initial stock. Every step is
idempotent, so running it again only adds what is missing and never resets
stock. ``status`` reports what the database holds without changing it.

Stop ``voicestock-pi`` before running ``init``: only one process may own the
file while it writes.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

from pi.catalog import CatalogService, load_initial_catalog
from pi.inventory import find_active_products_without_stock, load_initial_stock
from pi.storage import (
    VolatileDatabasePathError,
    default_database_path,
    open_database,
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    path = args.database or default_database_path()
    try:
        connection = open_database(path)
    except VolatileDatabasePathError as error:
        print(f"voicestock-pi-database: {error}", file=sys.stderr)
        return 2
    try:
        if args.command == "init":
            load_initial_catalog(connection)
            result = load_initial_stock(connection)
            print(
                f"initial stock: {len(result.created)} created, "
                f"{len(result.skipped)} already present"
            )
        _print_status(connection, path)
    finally:
        connection.close()
    return 0


def _print_status(connection: sqlite3.Connection, path: Path) -> None:
    (version,) = connection.execute(
        "SELECT max(version) FROM schema_migrations"
    ).fetchone()
    stock_rows, units = connection.execute(
        "SELECT count(*), coalesce(sum(quantity), 0) FROM inventory_stock"
    ).fetchone()
    (movements,) = connection.execute(
        "SELECT count(*) FROM inventory_movements"
    ).fetchone()
    active = CatalogService(connection).list_active_product_ids()
    without_stock = find_active_products_without_stock(connection)
    print(f"database: {path}")
    print(f"schema version: {version}")
    print(f"active products: {len(active)}")
    print(f"stock records: {stock_rows} ({units} units)")
    print(f"movements: {movements}")
    print(f"active products without stock: {len(without_stock)}")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare and inspect the VoiceStock database on the Raspberry Pi",
    )
    parser.add_argument(
        "command",
        choices=("init", "status"),
        help="init: migrate, load the catalog and the initial stock; "
        "status: report what the database holds",
    )
    parser.add_argument(
        "--database",
        type=Path,
        help="database file (default: VOICESTOCK_DATABASE or the user data directory)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
