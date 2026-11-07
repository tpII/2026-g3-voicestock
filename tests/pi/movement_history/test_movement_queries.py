"""Tests for the deterministic, paginated queries over movement history."""

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from pi.movement_history import (
    MAX_PAGE_SIZE,
    InvalidMovementQueryError,
    MovementHistoryReader,
    MovementOrigin,
    MovementQuery,
    SQLiteMovementHistory,
    SQLiteMovementRecorder,
)
from pi.storage import apply_migrations, connect, transaction

COCA = "coca-cola-zero-2l"
ARROZ = "arroz-gallo-1kg"
T0 = datetime(2026, 11, 4, 18, 0, tzinfo=UTC)

# (product, delta, origin, operation_id, minutes after T0). The fourth movement
# carries an earlier time than the third, as when the Pi clock jumps back.
MOVEMENTS = [
    (COCA, 10, "initialization", None, 0),
    (ARROZ, 4, "initialization", None, 1),
    (COCA, -2, "voice_operation", "op-1", 10),
    (ARROZ, 3, "voice_operation", "op-2", 5),
    (COCA, 1, "manual_adjustment", None, 20),
    (COCA, -3, "voice_operation", "op-3", 30),
]


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(tmp_path / "voicestock.sqlite3")
    apply_migrations(connection)
    connection.executemany(
        "INSERT INTO catalog_products (product_id, stock_unit) VALUES (?, 'unit')",
        [(COCA,), (ARROZ,)],
    )
    balances = {COCA: 0, ARROZ: 0}
    times = iter(T0 + timedelta(minutes=m) for *_, m in MOVEMENTS)
    numbers = iter(range(1, 100))
    recorder = SQLiteMovementRecorder(
        connection,
        clock=lambda: next(times),
        new_movement_id=lambda: f"mov-{next(numbers)}",
    )
    with transaction(connection):
        for product, delta, origin, operation_id, _ in MOVEMENTS:
            before = balances[product]
            balances[product] += delta
            key = "recognized_text" if origin == "voice_operation" else "reason"
            recorder.record(
                product_id=product,
                delta=delta,
                unit="unit",
                quantity_before=before,
                quantity_after=balances[product],
                origin=origin,
                cause={key: f"{origin} {product} {delta}"},
                operation_id=operation_id,
            )
    yield connection
    connection.close()


@pytest.fixture
def history(connection) -> SQLiteMovementHistory:
    return SQLiteMovementHistory(connection)


def _ids(page) -> list[str]:
    return [movement.movement_id for movement in page.movements]


def test_the_history_implements_the_reader_port(history) -> None:
    assert isinstance(history, MovementHistoryReader)


def test_without_filters_every_movement_comes_in_sequence_order(history) -> None:
    page = history.find_movements(MovementQuery())

    assert _ids(page) == ["mov-1", "mov-2", "mov-3", "mov-4", "mov-5", "mov-6"]
    assert [m.sequence for m in page.movements] == [1, 2, 3, 4, 5, 6]
    assert page.next_cursor is None


def test_newest_first_reverses_the_sequence(history) -> None:
    page = history.find_movements(MovementQuery(newest_first=True))

    assert _ids(page) == ["mov-6", "mov-5", "mov-4", "mov-3", "mov-2", "mov-1"]


def test_movements_by_product(history) -> None:
    page = history.find_movements(MovementQuery(product_id=COCA))

    assert _ids(page) == ["mov-1", "mov-3", "mov-5", "mov-6"]


def test_movements_by_operation(history) -> None:
    page = history.find_movements(MovementQuery(operation_id="op-2"))

    assert _ids(page) == ["mov-4"]


def test_movements_without_operation_are_selected_by_origin(history) -> None:
    initialization = history.find_movements(MovementQuery(origin="initialization"))
    manual = history.find_movements(
        MovementQuery(origin=MovementOrigin.MANUAL_ADJUSTMENT)
    )

    assert _ids(initialization) == ["mov-1", "mov-2"]
    assert _ids(manual) == ["mov-5"]
    assert all(
        m.operation_id is None for m in (*initialization.movements, *manual.movements)
    )


def test_filters_combine(history) -> None:
    page = history.find_movements(
        MovementQuery(product_id=COCA, origin="voice_operation")
    )

    assert _ids(page) == ["mov-3", "mov-6"]


def test_the_interval_includes_its_start_and_excludes_its_end(history) -> None:
    page = history.find_movements(
        MovementQuery(
            recorded_from=T0 + timedelta(minutes=5),
            recorded_to=T0 + timedelta(minutes=20),
        )
    )

    # 5 is included, 20 is excluded; results keep the sequence order even
    # though mov-4 was recorded at an earlier time than mov-3.
    assert _ids(page) == ["mov-3", "mov-4"]


def test_open_ended_intervals(history) -> None:
    since = history.find_movements(
        MovementQuery(recorded_from=T0 + timedelta(minutes=20))
    )
    until = history.find_movements(MovementQuery(recorded_to=T0 + timedelta(minutes=1)))

    assert _ids(since) == ["mov-5", "mov-6"]
    assert _ids(until) == ["mov-1"]


def test_interval_bounds_in_other_time_zones_mean_the_same_instant(history) -> None:
    argentina = timezone(timedelta(hours=-3))
    local_start = (T0 + timedelta(minutes=5)).astimezone(argentina)
    local_end = (T0 + timedelta(minutes=20)).astimezone(argentina)

    page = history.find_movements(
        MovementQuery(recorded_from=local_start, recorded_to=local_end)
    )

    assert _ids(page) == ["mov-3", "mov-4"]


def test_pages_follow_the_cursor_until_the_end(history) -> None:
    seen: list[str] = []
    cursor = None
    pages = 0
    while True:
        page = history.find_movements(MovementQuery(limit=4, cursor=cursor))
        seen += _ids(page)
        pages += 1
        if page.next_cursor is None:
            break
        cursor = page.next_cursor

    assert pages == 2
    assert seen == ["mov-1", "mov-2", "mov-3", "mov-4", "mov-5", "mov-6"]


def test_a_page_that_ends_exactly_at_the_last_movement_has_no_cursor(history):
    page = history.find_movements(MovementQuery(limit=6))

    assert len(page.movements) == 6
    assert page.next_cursor is None


def test_newest_first_pages_with_a_filter(history) -> None:
    first = history.find_movements(
        MovementQuery(product_id=COCA, newest_first=True, limit=2)
    )
    second = history.find_movements(
        MovementQuery(
            product_id=COCA, newest_first=True, limit=2, cursor=first.next_cursor
        )
    )

    assert _ids(first) == ["mov-6", "mov-5"]
    assert _ids(second) == ["mov-3", "mov-1"]
    assert second.next_cursor is None


def test_movements_appended_while_paging_do_not_shift_pages(
    connection, history
) -> None:
    first = history.find_movements(MovementQuery(limit=3))
    with transaction(connection):
        connection.execute(
            "INSERT INTO inventory_movements (movement_id, product_id, delta, unit, "
            "quantity_before, quantity_after, origin, recorded_at, cause) VALUES "
            "('mov-7', ?, 1, 'unit', 6, 7, 'manual_adjustment', "
            "'2026-11-04T19:00:00.000000Z', '{\"reason\": \"x\"}')",
            (COCA,),
        )

    second = history.find_movements(MovementQuery(limit=3, cursor=first.next_cursor))

    assert _ids(first) == ["mov-1", "mov-2", "mov-3"]
    assert _ids(second) == ["mov-4", "mov-5", "mov-6"]
    assert second.next_cursor is not None


def test_the_same_query_gives_the_same_result(history) -> None:
    query = MovementQuery(product_id=COCA, limit=2)

    assert history.find_movements(query) == history.find_movements(query)


def test_an_empty_result_is_a_page_not_an_error(history) -> None:
    for query in (
        MovementQuery(product_id="fernet-750ml"),
        MovementQuery(operation_id="op-404"),
        MovementQuery(recorded_from=T0 + timedelta(days=1)),
        MovementQuery(cursor="s999"),
    ):
        page = history.find_movements(query)
        assert page.movements == ()
        assert page.next_cursor is None


def test_returned_movements_explain_what_happened(history) -> None:
    (movement,) = history.find_movements(MovementQuery(operation_id="op-3")).movements

    assert movement.movement_id == "mov-6"
    assert movement.product_id == COCA
    assert (movement.delta, movement.unit) == (-3, "unit")
    assert (movement.quantity_before, movement.quantity_after) == (9, 6)
    assert movement.origin is MovementOrigin.VOICE_OPERATION
    assert movement.causation_key == "op-3"
    assert movement.recorded_at == T0 + timedelta(minutes=30)
    assert movement.cause == {"recognized_text": f"voice_operation {COCA} -3"}


def test_queries_do_not_read_or_change_stock(connection, history) -> None:
    before = connection.total_changes

    history.find_movements(MovementQuery(product_id=COCA))

    assert connection.total_changes == before
    assert connection.in_transaction is False
    assert connection.execute("SELECT count(*) FROM inventory_stock").fetchone() == (0,)


@pytest.mark.parametrize(
    "changes",
    [
        {"product_id": ""},
        {"operation_id": "  "},
        {"origin": "llm"},
        {"recorded_from": datetime(2026, 11, 4)},
        {"recorded_to": "2026-11-04"},
        {"recorded_from": T0, "recorded_to": T0},
        {"recorded_from": T0 + timedelta(minutes=1), "recorded_to": T0},
        {"limit": 0},
        {"limit": MAX_PAGE_SIZE + 1},
        {"limit": 2.0},
        {"limit": True},
        {"newest_first": "yes"},
        {"cursor": ""},
        {"cursor": "12"},
        {"cursor": "s0"},
        {"cursor": "s-1"},
        {"cursor": "s1.5"},
        {"cursor": "s١"},
    ],
)
def test_invalid_queries_are_rejected_before_reading(changes) -> None:
    with pytest.raises(InvalidMovementQueryError):
        MovementQuery(**changes)


def test_invalid_query_errors_are_not_storage_errors() -> None:
    assert not issubclass(InvalidMovementQueryError, sqlite3.Error)


def test_the_exact_filters_use_their_indexes(connection) -> None:
    # A time range ordered by sequence may be served by walking the sequence
    # instead; that choice is left to SQLite's planner.
    for where in (
        "product_id = 'x'",
        "operation_id = 'x'",
        "origin = 'manual_adjustment'",
    ):
        plan = " ".join(
            row[-1]
            for row in connection.execute(
                f"EXPLAIN QUERY PLAN SELECT * FROM inventory_movements WHERE {where} "
                "ORDER BY sequence"
            )
        )
        assert "USING INDEX inventory_movements_by_" in plan, (where, plan)
