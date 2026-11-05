"""Deterministic, paginated queries over the inventory movement history.

Queries read only the history: they never compute or correct stock. Every
result is ordered by ``sequence``, the history's total order, so the same
filter over the same stored movements always returns the same movements in
the same order. Pages are cut with a cursor, never an offset, so movements
appended while a client pages never shift or repeat what it already read.

Filters combine with AND:

- ``product_id``, ``operation_id`` and ``origin`` match exactly. Movements
  without an operation (manual and initialization) never match an
  ``operation_id``; select them by origin.
- ``recorded_from`` and ``recorded_to`` select the half-open UTC interval
  ``[recorded_from, recorded_to)``. They compare the time the Pi recorded,
  which can be wrong when the Pi has no network time; the order of results
  still follows ``sequence``.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from pi.movement_history.model import InventoryMovement, MovementOrigin, format_utc
from pi.movement_history.recorder import MOVEMENT_COLUMNS, movement_from_row

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class InvalidMovementQueryError(ValueError):
    """The filter, limit or cursor is not valid. It is not a storage failure."""


@dataclass(frozen=True)
class MovementQuery:
    """Filters, order and page of one history query."""

    product_id: str | None = None
    operation_id: str | None = None
    origin: MovementOrigin | str | None = None
    recorded_from: datetime | None = None
    recorded_to: datetime | None = None
    newest_first: bool = False
    limit: int = DEFAULT_PAGE_SIZE
    cursor: str | None = None

    def __post_init__(self) -> None:
        for name in ("product_id", "operation_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise InvalidMovementQueryError(f"{name} must be a non-blank string")
        if self.origin is not None:
            try:
                object.__setattr__(self, "origin", MovementOrigin(self.origin))
            except ValueError:
                raise InvalidMovementQueryError(
                    f"unknown origin {self.origin!r}"
                ) from None
        for name in ("recorded_from", "recorded_to"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, datetime) or value.utcoffset() is None
            ):
                raise InvalidMovementQueryError(
                    f"{name} must be a timezone-aware datetime"
                )
        if (
            self.recorded_from is not None
            and self.recorded_to is not None
            and self.recorded_from >= self.recorded_to
        ):
            raise InvalidMovementQueryError("recorded_from must be before recorded_to")
        if type(self.newest_first) is not bool:
            raise InvalidMovementQueryError("newest_first must be a boolean")
        if type(self.limit) is not int or not 1 <= self.limit <= MAX_PAGE_SIZE:
            raise InvalidMovementQueryError(
                f"limit must be an integer from 1 to {MAX_PAGE_SIZE}"
            )
        if self.cursor is not None:
            _decode_cursor(self.cursor)


@dataclass(frozen=True)
class MovementPage:
    """One page of results. ``next_cursor`` is None on the last page."""

    movements: tuple[InventoryMovement, ...]
    next_cursor: str | None = None


@runtime_checkable
class MovementHistoryReader(Protocol):
    """Port InventoryWebApp and the end-to-end validation read history through."""

    def find_movements(self, query: MovementQuery) -> MovementPage:
        """Return one page of the movements matching ``query``."""


class SQLiteMovementHistory:
    """``MovementHistoryReader`` over the Raspberry Pi database.

    Each page is a single query on the caller's connection; it never opens or
    commits a transaction.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def find_movements(self, query: MovementQuery) -> MovementPage:
        conditions: list[str] = []
        parameters: list[object] = []
        for column, value in (
            ("product_id", query.product_id),
            ("operation_id", query.operation_id),
            ("origin", query.origin and query.origin.value),
        ):
            if value is not None:
                conditions.append(f"{column} = ?")
                parameters.append(value)
        if query.recorded_from is not None:
            conditions.append("recorded_at >= ?")
            parameters.append(format_utc(query.recorded_from))
        if query.recorded_to is not None:
            conditions.append("recorded_at < ?")
            parameters.append(format_utc(query.recorded_to))
        if query.cursor is not None:
            conditions.append("sequence < ?" if query.newest_first else "sequence > ?")
            parameters.append(_decode_cursor(query.cursor))

        where = f"WHERE {' AND '.join(conditions)} " if conditions else ""
        direction = "DESC" if query.newest_first else "ASC"
        rows = self._connection.execute(
            f"SELECT {', '.join(MOVEMENT_COLUMNS)} FROM inventory_movements "
            f"{where}ORDER BY sequence {direction} LIMIT ?",
            (*parameters, query.limit + 1),
        ).fetchall()

        movements = tuple(movement_from_row(row) for row in rows[: query.limit])
        has_more = len(rows) > query.limit
        next_cursor = _encode_cursor(movements[-1].sequence) if has_more else None
        return MovementPage(movements, next_cursor)


def _encode_cursor(sequence: int) -> str:
    return f"s{sequence}"


def _decode_cursor(cursor: object) -> int:
    """Read a cursor made by ``_encode_cursor``. Clients treat it as opaque."""
    if (
        isinstance(cursor, str)
        and cursor.startswith("s")
        and cursor[1:].isascii()
        and cursor[1:].isdigit()
        and int(cursor[1:]) > 0
    ):
        return int(cursor[1:])
    raise InvalidMovementQueryError(f"invalid cursor {cursor!r}")
