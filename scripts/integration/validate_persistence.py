"""System validation of stock and history persistence across restarts.

Used by TC-PER-001 (InventoryPersistence-06) and TC-HIS-001
(InventoryMovementHistory-05) on the Raspberry Pi.

``prepare`` writes a known set of changes into a database: initial catalog
and stock, then two voice operations and one manual adjustment, each applied
with ``apply_delta`` and recorded in the same unit of work. ``record`` only
reads a database. Both save the observed state to a JSON file: every stock
level, every movement with all its fields, and the answers of the history
queries by product, operation, origin, UTC interval and cursor pages.

``check`` reads the database again from a new process, computes the same
state and compares it with the file, field by field. It also replays the
voice causation and verifies that no movement is duplicated. It changes
nothing in a database that ``record`` captured.

Run it with the project's Python from the repository root::

    python scripts/integration/validate_persistence.py prepare \\
        --database ~/.local/share/voicestock/validation.sqlite3 \\
        --state validation-state.json
    python scripts/integration/validate_persistence.py check \\
        --database ~/.local/share/voicestock/validation.sqlite3 \\
        --state validation-state.json
"""

import argparse
import json
import sqlite3
import sys
import uuid
from pathlib import Path

from pi.catalog import load_initial_catalog
from pi.inventory import InventoryService, load_initial_stock
from pi.movement_history import (
    MovementQuery,
    SQLiteMovementHistory,
    SQLiteMovementRecorder,
    format_utc,
)
from pi.storage import open_database, transaction

VOICE_PRODUCT = "gaseosa-coca-cola-zero-2250"
MANUAL_PRODUCT = "arroz-gallo-1000"
PAGE_SIZE = 7


def prepare(connection: sqlite3.Connection) -> dict:
    """Write the known changes and return the identifiers they produced."""
    load_initial_catalog(connection)
    load_initial_stock(connection)
    stock = InventoryService(connection)
    recorder = SQLiteMovementRecorder(connection)
    run = uuid.uuid4().hex[:8]
    operations = [str(uuid.uuid4()), str(uuid.uuid4())]
    changes = [
        (VOICE_PRODUCT, 5, "voice_operation", operations[0], "agregá cinco coca zero"),
        (VOICE_PRODUCT, -3, "voice_operation", operations[1], "sacá tres coca zero"),
        (MANUAL_PRODUCT, -2, "manual_adjustment", None, f"conteo físico {run}"),
    ]
    for product_id, delta, origin, operation_id, text in changes:
        with transaction(connection):
            level = stock.apply_delta(product_id, delta, "unit")
            key = "recognized_text" if origin == "voice_operation" else "reason"
            recorder.record(
                product_id=product_id,
                delta=delta,
                unit="unit",
                quantity_before=level.quantity - delta,
                quantity_after=level.quantity,
                origin=origin,
                operation_id=operation_id,
                causation_key=None if operation_id else f"validation-{run}",
                cause={key: text, "validation_run": run},
            )
    return {"run": run, "operations": operations}


def observe(connection: sqlite3.Connection, context: dict) -> dict:
    """Return everything the validation compares, without writing."""
    history = SQLiteMovementHistory(connection)
    movements = _all(history, MovementQuery(limit=200))
    state = {
        "stock": {
            level.product_id: [level.quantity, level.unit, level.retired]
            for level in InventoryService(connection).list_stock(include_retired=True)
        },
        "movements": [_movement(m) for m in movements],
        "pages": _pages(history),
        "by_origin": {
            origin: [m.movement_id for m in _all(history, MovementQuery(origin=origin))]
            for origin in ("voice_operation", "manual_adjustment", "initialization")
        },
        "by_product": {
            product_id: [
                m.movement_id
                for m in _all(history, MovementQuery(product_id=product_id))
            ]
            for product_id in (VOICE_PRODUCT, MANUAL_PRODUCT)
        },
        "by_operation": {
            operation_id: [
                m.movement_id
                for m in _all(history, MovementQuery(operation_id=operation_id))
            ]
            for operation_id in context.get("operations", [])
        },
    }
    if len(movements) >= 2:
        start, end = movements[0].recorded_at, movements[-1].recorded_at
        if start < end:
            state["interval"] = {
                "from": format_utc(start),
                "to": format_utc(end),
                "movement_ids": [
                    m.movement_id
                    for m in _all(
                        history, MovementQuery(recorded_from=start, recorded_to=end)
                    )
                ],
            }
    return state


def replay_voice(connection: sqlite3.Connection, context: dict) -> list[str]:
    """Replay each voice causation; return the ones that were not deduplicated."""
    recorder = SQLiteMovementRecorder(connection)
    failures = []
    for operation_id in context.get("operations", []):
        existing = recorder.find_by_causation("voice_operation", operation_id)
        if existing is None:
            failures.append(f"{operation_id}: not found")
            continue
        with transaction(connection):
            result = recorder.record(
                product_id=existing.product_id,
                delta=existing.delta,
                unit=existing.unit,
                quantity_before=existing.quantity_before,
                quantity_after=existing.quantity_after,
                origin=existing.origin,
                operation_id=operation_id,
                cause=existing.cause,
            )
        if result.created or result.movement != existing:
            failures.append(f"{operation_id}: replay created a new movement")
    return failures


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    connection = open_database(args.database)
    try:
        if args.command == "prepare":
            context = prepare(connection)
        elif args.command == "record":
            context = {}
        else:
            saved = json.loads(args.state.read_text(encoding="utf-8"))
            return _check(connection, saved)
        state = observe(connection, context)
        args.state.write_text(
            json.dumps(
                {"database": str(args.database), "context": context, "state": state},
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(
            f"{args.command}: {len(state['stock'])} stock records, "
            f"{len(state['movements'])} movements saved to {args.state}"
        )
        return 0
    finally:
        connection.close()


def _check(connection: sqlite3.Connection, saved: dict) -> int:
    context = saved["context"]
    expected = saved["state"]
    actual = observe(connection, context)
    failures = [
        f"{key} differs"
        for key in sorted(set(expected) | set(actual))
        if expected.get(key) != actual.get(key)
    ]
    count_before = len(actual["movements"])
    failures += replay_voice(connection, context)
    if len(observe(connection, context)["movements"]) != count_before:
        failures.append("replay changed the number of movements")

    print(
        f"check: {len(actual['stock'])} stock records, "
        f"{len(actual['movements'])} movements, "
        f"{len(actual['pages'])} pages of {PAGE_SIZE}"
    )
    for key in ("by_origin", "by_product", "by_operation"):
        sizes = {name: len(ids) for name, ids in actual[key].items()}
        print(f"  {key}: {sizes}")
    if "interval" in actual:
        print(
            f"  interval [{actual['interval']['from']}, {actual['interval']['to']}): "
            f"{len(actual['interval']['movement_ids'])} movements"
        )
    if failures:
        print("FAIL")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("PASS")
    return 0


def _all(history: SQLiteMovementHistory, query: MovementQuery) -> list:
    movements, cursor = [], None
    while True:
        page = history.find_movements(
            MovementQuery(
                product_id=query.product_id,
                operation_id=query.operation_id,
                origin=query.origin,
                recorded_from=query.recorded_from,
                recorded_to=query.recorded_to,
                limit=query.limit,
                cursor=cursor,
            )
        )
        movements += page.movements
        if page.next_cursor is None:
            return movements
        cursor = page.next_cursor


def _pages(history: SQLiteMovementHistory) -> list[list[int]]:
    pages, cursor = [], None
    while True:
        page = history.find_movements(MovementQuery(limit=PAGE_SIZE, cursor=cursor))
        pages.append([m.sequence for m in page.movements])
        if page.next_cursor is None:
            return pages
        cursor = page.next_cursor


def _movement(movement) -> dict:
    return {
        "sequence": movement.sequence,
        "movement_id": movement.movement_id,
        "product_id": movement.product_id,
        "delta": movement.delta,
        "unit": movement.unit,
        "quantity_before": movement.quantity_before,
        "quantity_after": movement.quantity_after,
        "origin": movement.origin.value,
        "operation_id": movement.operation_id,
        "causation_key": movement.causation_key,
        "recorded_at": format_utc(movement.recorded_at),
        "cause": dict(movement.cause),
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("prepare", "record", "check"))
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args(argv)
    args.database = args.database.expanduser()
    return args


if __name__ == "__main__":
    sys.exit(main())
