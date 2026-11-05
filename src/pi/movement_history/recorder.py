"""Append-only recording of inventory movements inside the caller's transaction.

The recorder only writes history: it never changes stock, confirms an
operation or decides a delta. It must run inside a transaction already open
on the caller's connection, so a movement is committed or rolled back
together with the stock change it describes, and it never commits.

A caller that applies a change and records it follows this order, all inside
one ``pi.storage.transaction``:

1. ``find_by_causation``: if the cause was already recorded, stop there and
   do not apply the change again;
2. apply the delta with the inventory service;
3. ``record`` the movement with the balance before and after.
"""

import json
import sqlite3
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable

from pi.movement_history.model import (
    InvalidMovementError,
    InventoryMovement,
    MovementOrigin,
    format_utc,
    parse_utc,
)

MOVEMENT_COLUMNS = (
    "sequence",
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
_SELECT_MOVEMENTS = f"SELECT {', '.join(MOVEMENT_COLUMNS)} FROM inventory_movements"


class NoUnitOfWorkError(RuntimeError):
    """The recorder was called without a transaction open on the connection."""


class CausationConflictError(InvalidMovementError):
    """A causation key was reused for a different movement."""


@dataclass(frozen=True)
class RecordResult:
    """Outcome of ``record``. ``created`` is false when the cause was replayed."""

    movement: InventoryMovement
    created: bool


@runtime_checkable
class MovementRecorder(Protocol):
    """Port the confirmation executor and manual adjustments record through."""

    def find_by_causation(
        self, origin: MovementOrigin | str, causation_key: str
    ) -> InventoryMovement | None:
        """Return the movement already recorded for this cause, if any."""

    def record(
        self,
        *,
        product_id: str,
        delta: int,
        unit: str,
        quantity_before: int,
        quantity_after: int,
        origin: MovementOrigin | str,
        cause: Mapping[str, Any],
        operation_id: str | None = None,
        causation_key: str | None = None,
    ) -> RecordResult:
        """Append one movement, or return the one its cause already produced."""


class SQLiteMovementRecorder:
    """``MovementRecorder`` over the Raspberry Pi database.

    ``clock`` and ``new_movement_id`` are replaceable for tests. The time comes
    from the Pi clock, which may be wrong without network time; the order of
    the history never depends on it.
    """

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        new_movement_id: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._connection = connection
        self._clock = clock
        self._new_movement_id = new_movement_id

    def find_by_causation(
        self, origin: MovementOrigin | str, causation_key: str
    ) -> InventoryMovement | None:
        row = self._connection.execute(
            f"{_SELECT_MOVEMENTS} WHERE origin = ? AND causation_key = ?",
            (MovementOrigin(origin).value, causation_key),
        ).fetchone()
        return None if row is None else movement_from_row(row)

    def record(
        self,
        *,
        product_id: str,
        delta: int,
        unit: str,
        quantity_before: int,
        quantity_after: int,
        origin: MovementOrigin | str,
        cause: Mapping[str, Any],
        operation_id: str | None = None,
        causation_key: str | None = None,
    ) -> RecordResult:
        if not self._connection.in_transaction:
            raise NoUnitOfWorkError(
                "record a movement inside the caller's transaction, "
                "together with the stock change it describes"
            )
        movement = InventoryMovement(
            movement_id=self._new_movement_id(),
            product_id=product_id,
            delta=delta,
            unit=unit,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            origin=origin,
            recorded_at=self._clock(),
            cause=cause,
            operation_id=operation_id,
            causation_key=causation_key,
        )

        if movement.causation_key is not None:
            existing = self.find_by_causation(movement.origin, movement.causation_key)
            if existing is not None:
                if _same_intent(existing, movement):
                    return RecordResult(existing, created=False)
                raise CausationConflictError(
                    f"{movement.origin} cause {movement.causation_key!r} already "
                    f"recorded movement {existing.movement_id!r} with other data"
                )

        try:
            cursor = self._connection.execute(
                f"INSERT INTO inventory_movements ({', '.join(MOVEMENT_COLUMNS[1:])}) "
                f"VALUES ({', '.join('?' for _ in MOVEMENT_COLUMNS[1:])})",
                _row_values(movement),
            )
        except sqlite3.IntegrityError as error:
            raise InvalidMovementError(
                f"movement for {product_id!r} in {unit!r} cannot be stored: {error}"
            ) from error
        stored = InventoryMovement(
            **{**_fields(movement), "sequence": cursor.lastrowid}
        )
        return RecordResult(stored, created=True)


def movement_from_row(row: tuple) -> InventoryMovement:
    """Build a movement from a row selected with ``MOVEMENT_COLUMNS``."""
    values = dict(zip(MOVEMENT_COLUMNS, row, strict=True))
    values["recorded_at"] = parse_utc(values["recorded_at"])
    values["cause"] = json.loads(values["cause"])
    return InventoryMovement(**values)


def _same_intent(existing: InventoryMovement, new: InventoryMovement) -> bool:
    """A replay is the same cause asking for the same change.

    The balance and the snapshot may differ on a replay, because stock moved
    since the first recording; the product, delta, unit and operation may not.
    """
    keys = ("product_id", "delta", "unit", "operation_id")
    return all(getattr(existing, key) == getattr(new, key) for key in keys)


def _fields(movement: InventoryMovement) -> dict[str, Any]:
    return {name: getattr(movement, name) for name in MOVEMENT_COLUMNS}


def _row_values(movement: InventoryMovement) -> tuple:
    values = _fields(movement)
    values["origin"] = movement.origin.value
    values["recorded_at"] = format_utc(movement.recorded_at)
    values["cause"] = json.dumps(dict(movement.cause), sort_keys=True)
    return tuple(values[name] for name in MOVEMENT_COLUMNS[1:])
