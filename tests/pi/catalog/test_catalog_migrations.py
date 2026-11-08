"""Upgrade of a version-3 database and the new catalog constraints."""

import json
import sqlite3
from pathlib import Path

import pytest

from pi.inventory import InventoryService, StockStatus
from pi.storage import MIGRATIONS, Migration, apply_migrations, connect

LEGACY_ID = "legacy-product"


def _version_3(path: Path) -> sqlite3.Connection:
    connection = connect(path)
    apply_migrations(connection, MIGRATIONS[:3])
    connection.execute(
        "INSERT INTO catalog_products (product_id, stock_unit, retired) "
        "VALUES (?, 'unit', 0)",
        (LEGACY_ID,),
    )
    connection.execute(
        "INSERT INTO inventory_stock (product_id, quantity, unit) "
        "VALUES (?, 3, 'unit')",
        (LEGACY_ID,),
    )
    connection.execute(
        """
        INSERT INTO inventory_movements (
            movement_id, product_id, delta, unit, quantity_before, quantity_after,
            origin, operation_id, causation_key, recorded_at, cause
        ) VALUES (
            'mov-legacy', ?, 2, 'unit', 1, 3,
            'initialization', NULL, 'legacy-init',
            '2026-11-04T18:30:05.123456Z', ?
        )
        """,
        (LEGACY_ID, json.dumps({"reason": "carga previa"})),
    )
    return connection


def test_the_first_three_migrations_keep_their_identity() -> None:
    assert [(migration.version, migration.name) for migration in MIGRATIONS[:3]] == [
        (1, "create_catalog_products"),
        (2, "create_inventory_stock"),
        (3, "create_inventory_movements"),
    ]
    assert MIGRATIONS[3].version == 4
    assert MIGRATIONS[3].name == "extend_catalog_products"


def test_a_fresh_database_accepts_a_legacy_shaped_insert(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        apply_migrations(connection)
        connection.execute(
            "INSERT INTO catalog_products (product_id, stock_unit) "
            "VALUES ('still-provisional', 'unit')"
        )

        row = connection.execute(
            "SELECT name, category_id, retired FROM catalog_products "
            "WHERE product_id = 'still-provisional'"
        ).fetchone()
        assert row == (None, None, 0)
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    finally:
        connection.close()


def test_version_3_data_survives_the_catalog_migration(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    prepared = _version_3(path)
    prepared.close()

    connection = connect(path)
    try:
        assert apply_migrations(connection) == (4,)
        assert apply_migrations(connection) == ()

        product = connection.execute(
            "SELECT product_id, stock_unit, retired, name, category_id "
            "FROM catalog_products"
        ).fetchone()
        stock = connection.execute(
            "SELECT product_id, quantity, unit FROM inventory_stock"
        ).fetchone()
        movement = connection.execute(
            "SELECT movement_id, product_id, delta, cause FROM inventory_movements"
        ).fetchone()

        assert product == (LEGACY_ID, "unit", 0, None, None)
        assert stock == (LEGACY_ID, 3, "unit")
        assert movement[0] == "mov-legacy"
        assert movement[1:] == (LEGACY_ID, 2, json.dumps({"reason": "carga previa"}))
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        lookup = InventoryService(connection).get_stock(LEGACY_ID)
        assert lookup.status is StockStatus.FOUND
        assert lookup.level is not None
        assert lookup.level.quantity == 3
    finally:
        connection.close()


def test_a_failed_upgrade_rolls_back_and_keeps_version_3(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    connection = _version_3(path)
    broken = (
        *MIGRATIONS[:3],
        Migration(
            4,
            "extend_catalog_products",
            (
                "CREATE TABLE catalog_categories (category_id TEXT PRIMARY KEY)",
                "CREATE TABLE broken (",
            ),
        ),
    )

    with pytest.raises(sqlite3.OperationalError):
        apply_migrations(connection, broken)

    assert connection.execute(
        "SELECT version FROM schema_migrations ORDER BY version"
    ).fetchall() == [(1,), (2,), (3,)]
    assert connection.execute("SELECT quantity FROM inventory_stock").fetchone() == (3,)
    tables = {
        name
        for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert "catalog_categories" not in tables

    assert apply_migrations(connection) == (4,)
    assert connection.execute("SELECT quantity FROM inventory_stock").fetchone() == (3,)
    connection.close()


def test_a_complete_product_without_a_category_is_rejected(connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="incomplete"):
        connection.execute(
            "INSERT INTO catalog_products ("
            "product_id, stock_unit, name, name_key) "
            "VALUES ('gaseosa', 'unit', 'Gaseosa', 'gaseosa')"
        )


def test_two_complete_products_cannot_share_a_canonical_identity(connection) -> None:
    connection.execute(
        "INSERT INTO catalog_categories (category_id, name, name_key) "
        "VALUES ('bebidas', 'Bebidas', 'bebidas')"
    )
    connection.execute(
        "INSERT INTO catalog_products ("
        "product_id, stock_unit, name, name_key, category_id) "
        "VALUES ('coca', 'unit', 'Gaseosa', 'gaseosa', 'bebidas')"
    )

    with pytest.raises(sqlite3.IntegrityError, match="canonical_identity"):
        connection.execute(
            "INSERT INTO catalog_products ("
            "product_id, stock_unit, name, name_key, category_id) "
            "VALUES ('cola', 'unit', 'Gaseosa', 'gaseosa', 'bebidas')"
        )
