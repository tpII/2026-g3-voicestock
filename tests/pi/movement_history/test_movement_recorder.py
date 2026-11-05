"""Tests for recording inventory movements in the caller's transaction."""

import itertools
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from pi.inventory import InventoryService, create_stock_record
from pi.movement_history import (
    CausationConflictError,
    InvalidMovementError,
    MovementOrigin,
    MovementRecorder,
    NoUnitOfWorkError,
    SQLiteMovementRecorder,
)
from pi.storage import apply_migrations, connect, transaction

COCA = "coca-cola-zero-2l"
START = datetime(2026, 11, 4, 18, 30, tzinfo=UTC)


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "voicestock.sqlite3"
    connection = connect(path)
    apply_migrations(connection)
    connection.executemany(
        "INSERT INTO catalog_products (product_id, stock_unit) VALUES (?, 'unit')",
        [(COCA,), ("arroz-gallo-1kg",)],
    )
    with transaction(connection):
        create_stock_record(connection, COCA, 5)
        create_stock_record(connection, "arroz-gallo-1kg", 2)
    connection.close()
    return path


@pytest.fixture
def connection(database: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(database)
    yield connection
    connection.close()


@pytest.fixture
def recorder(connection: sqlite3.Connection) -> SQLiteMovementRecorder:
    ticks = itertools.count()
    ids = itertools.count(1)
    return SQLiteMovementRecorder(
        connection,
        clock=lambda: START + timedelta(seconds=next(ticks)),
        new_movement_id=lambda: f"mov-{next(ids)}",
    )


def _voice(**changes) -> dict:
    values = {
        "product_id": COCA,
        "delta": 3,
        "unit": "unit",
        "quantity_before": 5,
        "quantity_after": 8,
        "origin": MovementOrigin.VOICE_OPERATION,
        "cause": {"recognized_text": "agregá tres coca zero"},
        "operation_id": "op-1",
    }
    values.update(changes)
    return values


def _history(connection: sqlite3.Connection) -> list[tuple]:
    return connection.execute(
        "SELECT sequence, movement_id, origin, operation_id, causation_key "
        "FROM inventory_movements ORDER BY sequence"
    ).fetchall()


def _committed_history(database: Path) -> list[tuple]:
    reader = connect(database)
    try:
        return _history(reader)
    finally:
        reader.close()


def _stock(database: Path, product_id: str = COCA) -> int:
    reader = connect(database)
    try:
        return InventoryService(reader).get_stock(product_id).level.quantity
    finally:
        reader.close()


def test_the_recorder_implements_the_port(recorder) -> None:
    assert isinstance(recorder, MovementRecorder)


def test_a_voice_movement_is_recorded_with_its_causation(
    database, connection, recorder
) -> None:
    with transaction(connection):
        result = recorder.record(**_voice())

    assert result.created is True
    movement = result.movement
    assert movement.sequence == 1
    assert movement.movement_id == "mov-1"
    assert movement.causation_key == "op-1"
    assert movement.recorded_at == START
    assert _committed_history(database) == [
        (1, "mov-1", "voice_operation", "op-1", "op-1")
    ]


@pytest.mark.parametrize(
    "origin", [MovementOrigin.MANUAL_ADJUSTMENT, MovementOrigin.INITIALIZATION]
)
def test_other_origins_are_recorded_without_an_operation(
    database, connection, recorder, origin
) -> None:
    with transaction(connection):
        recorder.record(
            **_voice(origin=origin, operation_id=None, cause={"reason": "conteo"})
        )
        recorder.record(
            **_voice(origin=origin, operation_id=None, cause={"reason": "conteo"})
        )

    assert _committed_history(database) == [
        (1, "mov-1", origin.value, None, None),
        (2, "mov-2", origin.value, None, None),
    ]


def test_a_stored_movement_reads_back_the_same(connection, recorder) -> None:
    with transaction(connection):
        recorded = recorder.record(**_voice(cause={"recognized_text": "x", "n": 3}))

    found = recorder.find_by_causation("voice_operation", "op-1")
    assert found == recorded.movement
    assert found.sequence == recorded.movement.sequence
    assert dict(found.cause) == {"recognized_text": "x", "n": 3}


def test_recording_outside_a_transaction_is_refused(connection, recorder) -> None:
    with pytest.raises(NoUnitOfWorkError):
        recorder.record(**_voice())

    assert _history(connection) == []


def test_the_recorder_never_commits_on_its_own(database, connection, recorder):
    connection.execute("BEGIN IMMEDIATE")
    recorder.record(**_voice())

    assert connection.in_transaction is True
    assert _committed_history(database) == []
    connection.execute("ROLLBACK")
    assert _history(connection) == []


def test_replaying_a_cause_returns_the_existing_movement(
    database, connection, recorder
) -> None:
    with transaction(connection):
        first = recorder.record(**_voice())
    with transaction(connection):
        # Stock moved meanwhile: the balance differs, the intent does not.
        replay = recorder.record(
            **_voice(
                quantity_before=8, quantity_after=11, cause={"recognized_text": "y"}
            )
        )

    assert replay.created is False
    assert replay.movement == first.movement
    assert len(_committed_history(database)) == 1


def test_replaying_a_manual_causation_key_is_idempotent(connection, recorder):
    manual = _voice(
        origin="manual_adjustment",
        operation_id=None,
        causation_key="ajuste-42",
        cause={"reason": "conteo"},
    )
    with transaction(connection):
        first = recorder.record(**manual)
        second = recorder.record(**manual)

    assert second == type(second)(first.movement, created=False)
    assert len(_history(connection)) == 1


@pytest.mark.parametrize(
    "changes",
    [{"delta": 4, "quantity_after": 9}, {"product_id": "arroz-gallo-1kg"}],
)
def test_reusing_a_cause_for_another_change_is_rejected(
    connection, recorder, changes
) -> None:
    with transaction(connection):
        recorder.record(**_voice())
    before = _history(connection)

    with pytest.raises(CausationConflictError), transaction(connection):
        recorder.record(**_voice(**changes))

    assert _history(connection) == before


def test_the_same_key_in_another_origin_is_another_cause(connection, recorder):
    with transaction(connection):
        for origin in ("manual_adjustment", "initialization"):
            recorder.record(
                **_voice(
                    origin=origin,
                    operation_id=None,
                    causation_key="carga-1",
                    cause={"reason": "x"},
                )
            )

    assert len(_history(connection)) == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"product_id": "fernet-750ml"},
        {"unit": "kg"},
        {"delta": 0, "quantity_after": 5},
        {"quantity_after": 9},
        {"operation_id": None},
        {"origin": "llm"},
        {"cause": {}},
        {"cause": {"reason": "falta el texto reconocido"}},
    ],
)
def test_untraceable_movements_are_rejected(connection, recorder, changes):
    with pytest.raises(InvalidMovementError), transaction(connection):
        recorder.record(**_voice(**changes))

    assert _history(connection) == []


def test_recording_does_not_change_stock(database, connection, recorder) -> None:
    with transaction(connection):
        recorder.record(**_voice())

    assert _stock(database) == 5


# The usage the confirmation executor will follow: check, apply, record.


def _confirm(connection, recorder, operation_id: str, delta: int):
    with transaction(connection):
        existing = recorder.find_by_causation("voice_operation", operation_id)
        if existing is not None:
            return existing
        level = InventoryService(connection).apply_delta(COCA, delta, "unit")
        return recorder.record(
            **_voice(
                delta=delta,
                quantity_before=level.quantity - delta,
                quantity_after=level.quantity,
                operation_id=operation_id,
            )
        ).movement


def test_stock_and_history_commit_together(database, connection, recorder):
    movement = _confirm(connection, recorder, "op-1", 3)

    assert (movement.quantity_before, movement.quantity_after) == (5, 8)
    assert _stock(database) == 8
    assert len(_committed_history(database)) == 1


def test_confirming_the_same_operation_twice_changes_stock_once(
    database, connection, recorder
) -> None:
    first = _confirm(connection, recorder, "op-1", 3)
    second = _confirm(connection, recorder, "op-1", 3)

    assert second == first
    assert _stock(database) == 8
    assert len(_committed_history(database)) == 1


def test_a_failed_recording_rolls_the_stock_change_back(
    database, connection, recorder
) -> None:
    with pytest.raises(InvalidMovementError), transaction(connection):
        InventoryService(connection).apply_delta(COCA, 3, "unit")
        recorder.record(**_voice(unit="kg"))

    assert _stock(database) == 5
    assert _committed_history(database) == []


def test_a_write_failure_rolls_the_stock_change_back(
    database, connection, recorder
) -> None:
    connection.execute(
        "CREATE TEMP TRIGGER fail_history_write BEFORE INSERT ON inventory_movements "
        "BEGIN SELECT RAISE(FAIL, 'disk I/O error'); END"
    )

    with pytest.raises(InvalidMovementError), transaction(connection):
        InventoryService(connection).apply_delta(COCA, 3, "unit")
        recorder.record(**_voice())

    assert _stock(database) == 5
    assert _committed_history(database) == []
