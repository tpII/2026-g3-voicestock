"""Tests for the single migration order of the Pi database."""

from pathlib import Path

import pytest

from pi.storage import (
    MIGRATIONS,
    Migration,
    MigrationHistoryError,
    VolatileDatabasePathError,
    apply_migrations,
    connect,
    open_database,
)


def _tables(connection) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    return {name for (name,) in rows}


def test_migrations_create_the_catalog_and_stock_tables(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        applied = apply_migrations(connection)

        assert applied == tuple(migration.version for migration in MIGRATIONS)
        assert _tables(connection) == {
            "schema_migrations",
            "catalog_products",
            "catalog_categories",
            "catalog_aliases",
            "inventory_stock",
            "inventory_movements",
            "sqlite_sequence",
        }
    finally:
        connection.close()


def test_reapplying_migrations_changes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    first = connect(path)
    apply_migrations(first)
    first.close()

    second = connect(path)
    try:
        assert apply_migrations(second) == ()
        assert second.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall() == [
            (migration.version, migration.name) for migration in MIGRATIONS
        ]
    finally:
        second.close()


def test_only_pending_migrations_are_applied(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        apply_migrations(connection, MIGRATIONS[:1])

        assert apply_migrations(connection) == (2, 3, 4, 5)
        assert "inventory_stock" in _tables(connection)
    finally:
        connection.close()


def test_a_failing_migration_leaves_the_schema_untouched(tmp_path: Path) -> None:
    broken = (
        *MIGRATIONS,
        Migration(len(MIGRATIONS) + 1, "broken", ("CREATE TABLE broken (",)),
    )
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        with pytest.raises(Exception):
            apply_migrations(connection, broken)

        assert _tables(connection) == set()
    finally:
        connection.close()


def test_an_unknown_history_is_refused(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        apply_migrations(connection)
        renamed = (Migration(1, "something_else", ()), *MIGRATIONS[1:])

        with pytest.raises(MigrationHistoryError):
            apply_migrations(connection, renamed)
    finally:
        connection.close()


def test_a_database_newer_than_the_code_is_refused(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        apply_migrations(connection)

        with pytest.raises(MigrationHistoryError):
            apply_migrations(connection, MIGRATIONS[:1])
    finally:
        connection.close()


def test_migration_versions_must_be_consecutive(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    try:
        with pytest.raises(ValueError):
            apply_migrations(connection, (Migration(2, "skips_one", ()),))
    finally:
        connection.close()


def test_open_database_rejects_a_volatile_path(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"

    with pytest.raises(VolatileDatabasePathError):
        open_database(path, (tmp_path,))

    assert not path.exists()


def test_open_database_returns_a_migrated_connection(tmp_path: Path) -> None:
    connection = open_database(tmp_path / "voicestock.sqlite3", volatile_roots=())
    try:
        assert "inventory_stock" in _tables(connection)
    finally:
        connection.close()
