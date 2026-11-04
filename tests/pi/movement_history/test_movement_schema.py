"""Tests for the SQLite schema of the inventory movement history."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from pi.storage import apply_migrations, connect

COLUMNS = (
    "movement_id",
    "product_id",
    "delta",
    "unit",
    "quantity_before",
    "quantity_after",
    "origin",
    "operation_id",
    "causation_key",
    "recorded_at",
    "cause",
)
INSERT = (
    f"INSERT INTO inventory_movements ({', '.join(COLUMNS)}) "
    f"VALUES ({', '.join('?' for _ in COLUMNS)})"
)


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "voicestock.sqlite3")
    apply_migrations(connection)
    connection.executemany(
        "INSERT INTO catalog_products (product_id, stock_unit) VALUES (?, 'unit')",
        [("coca-cola-zero-2l",), ("arroz-gallo-1kg",)],
    )
    yield connection
    connection.close()


def _voice(**changes) -> dict:
    row = {
        "movement_id": "mov-1",
        "product_id": "coca-cola-zero-2l",
        "delta": 3,
        "unit": "unit",
        "quantity_before": 5,
        "quantity_after": 8,
        "origin": "voice_operation",
        "operation_id": "op-1",
        "causation_key": "op-1",
        "recorded_at": "2026-11-04T18:30:05.123456Z",
        "cause": json.dumps({"recognized_text": "agregá tres coca zero"}),
    }
    row.update(changes)
    return row


def _manual(**changes) -> dict:
    values = {
        "movement_id": "mov-2",
        "origin": "manual_adjustment",
        "operation_id": None,
        "causation_key": None,
        "cause": json.dumps({"reason": "conteo físico"}),
    }
    values.update(changes)
    return _voice(**values)


def _insert(connection: sqlite3.Connection, row: dict) -> None:
    connection.execute(INSERT, tuple(row[column] for column in COLUMNS))


def test_a_complete_voice_movement_is_stored_in_the_same_database(
    connection,
) -> None:
    _insert(connection, _voice())

    stored = connection.execute(
        "SELECT sequence, movement_id, operation_id FROM inventory_movements"
    ).fetchall()
    assert stored == [(1, "mov-1", "op-1")]


@pytest.mark.parametrize("origin", ["manual_adjustment", "initialization"])
def test_other_origins_are_stored_without_an_operation_id(connection, origin):
    _insert(connection, _manual(origin=origin, movement_id=f"mov-{origin}"))
    _insert(connection, _manual(origin=origin, movement_id=f"mov-{origin}-2"))

    assert connection.execute(
        "SELECT count(*) FROM inventory_movements WHERE operation_id IS NULL"
    ).fetchone() == (2,)


def test_the_sequence_is_a_total_order_independent_of_the_clock(connection):
    _insert(connection, _voice(recorded_at="2026-11-04T18:30:05.000000Z"))
    # The Pi has no real-time clock: a later movement can carry an earlier time.
    _insert(connection, _manual(recorded_at="2001-01-01T00:00:00.000000Z"))

    assert connection.execute(
        "SELECT movement_id FROM inventory_movements ORDER BY sequence"
    ).fetchall() == [("mov-1",), ("mov-2",)]


def test_one_operation_cannot_produce_two_movements(connection) -> None:
    _insert(connection, _voice())

    with pytest.raises(sqlite3.IntegrityError):
        _insert(connection, _voice(movement_id="mov-2"))


def test_a_causation_key_is_unique_within_its_origin(connection) -> None:
    _insert(connection, _manual(causation_key="seed:coca"))

    with pytest.raises(sqlite3.IntegrityError):
        _insert(connection, _manual(movement_id="mov-3", causation_key="seed:coca"))

    _insert(
        connection,
        _manual(
            movement_id="mov-4", origin="initialization", causation_key="seed:coca"
        ),
    )


def test_movement_ids_are_unique(connection) -> None:
    _insert(connection, _voice())

    with pytest.raises(sqlite3.IntegrityError):
        _insert(connection, _manual(movement_id="mov-1"))


@pytest.mark.parametrize(
    "changes",
    [
        {"movement_id": None},
        {"movement_id": " "},
        {"product_id": "fernet-750ml"},
        {"unit": "kg"},
        {"unit": None},
        {"delta": 0},
        {"delta": 1.5, "quantity_after": 6.5},
        {"quantity_before": -1, "quantity_after": 2},
        {"quantity_before": 2, "delta": -3, "quantity_after": -1},
        {"quantity_after": 9},
        {"origin": "llm"},
        {"origin": None},
        {"operation_id": None, "causation_key": None},
        {"causation_key": "op-2"},
        {"causation_key": None},
        {"recorded_at": None},
        {"recorded_at": "2026-11-04 18:30:05"},
        {"recorded_at": "2026-11-04T18:30:05.123456-03:00"},
        {"recorded_at": "2026-11-04T18:30:05Z"},
        {"cause": None},
        {"cause": "{}"},
        {"cause": "[]"},
        {"cause": "not json"},
    ],
    ids=lambda changes: ",".join(f"{k}={v!r}" for k, v in changes.items()),
)
def test_untraceable_voice_movements_are_rejected(connection, changes) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert(connection, _voice(**changes))


def test_a_manual_movement_cannot_carry_an_operation_id(connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        _insert(connection, _manual(operation_id="op-1"))


def test_movements_are_never_updated(connection) -> None:
    _insert(connection, _voice())

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute("UPDATE inventory_movements SET delta = 4")


def test_movements_are_never_deleted(connection) -> None:
    _insert(connection, _voice())

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute("DELETE FROM inventory_movements")


def test_a_product_with_history_cannot_be_deleted_or_change_unit(connection):
    _insert(connection, _voice())

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "DELETE FROM catalog_products WHERE product_id = 'coca-cola-zero-2l'"
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE catalog_products SET stock_unit = 'pack' "
            "WHERE product_id = 'coca-cola-zero-2l'"
        )


def test_recording_a_movement_does_not_touch_stock(connection) -> None:
    connection.execute(
        "INSERT INTO inventory_stock VALUES ('coca-cola-zero-2l', 5, 'unit')"
    )

    _insert(connection, _voice())

    assert connection.execute("SELECT quantity FROM inventory_stock").fetchall() == [
        (5,)
    ]


def test_the_queries_of_the_history_have_indexes(connection) -> None:
    indexes = {
        name: [
            column
            for (_, _, column) in connection.execute(f"PRAGMA index_info({name})")
        ]
        for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index' "
            "AND tbl_name = 'inventory_movements' AND sql IS NOT NULL"
        )
    }

    assert sorted(indexes.values()) == [
        ["operation_id", "sequence"],
        ["origin", "sequence"],
        ["product_id", "sequence"],
        ["recorded_at", "sequence"],
    ]


def test_the_history_does_not_redefine_catalog_or_operations(connection) -> None:
    columns = [
        row[1] for row in connection.execute("PRAGMA table_info(inventory_movements)")
    ]

    assert columns == ["sequence", *COLUMNS]
    assert (
        connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name LIKE '%operation%'"
        ).fetchall()
        == []
    )
