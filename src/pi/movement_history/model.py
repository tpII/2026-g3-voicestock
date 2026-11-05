"""Domain model of one inventory movement.

A movement records one change of stock: which product, by how much, from
which balance to which, when, from which origin and why. It is complete on
its own, so the history can be read without the current stock or the pending
operation that caused it. Movements are never edited or deleted.

The origin says what kind of cause produced the movement:

- ``voice_operation``: a confirmed voice command. It carries the
  ``operation_id`` of the pending operation, which is also its causation key,
  so one operation can never produce two movements.
- ``manual_adjustment`` and ``initialization``: no voice operation exists, so
  ``operation_id`` is absent. A causation key is optional and, when given,
  makes the cause idempotent within its origin.

``cause`` is a snapshot of why the movement happened, frozen when it was
recorded: the recognized text for a voice operation, a reason otherwise.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class MovementOrigin(StrEnum):
    """Kind of cause behind a movement."""

    VOICE_OPERATION = "voice_operation"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    INITIALIZATION = "initialization"


# Key the cause snapshot must contain for each origin to explain the movement.
REQUIRED_CAUSE_KEYS: Mapping[MovementOrigin, str] = MappingProxyType(
    {
        MovementOrigin.VOICE_OPERATION: "recognized_text",
        MovementOrigin.MANUAL_ADJUSTMENT: "reason",
        MovementOrigin.INITIALIZATION: "reason",
    }
)


class InvalidMovementError(ValueError):
    """The movement is incomplete or inconsistent and cannot be traced."""


@dataclass(frozen=True)
class InventoryMovement:
    """One stock change, with everything needed to explain it later.

    ``sequence`` is assigned by the database when the movement is stored and
    is the history's total order; it is ``None`` before that.
    """

    movement_id: str
    product_id: str
    delta: int
    unit: str
    quantity_before: int
    quantity_after: int
    origin: MovementOrigin
    recorded_at: datetime
    cause: Mapping[str, Any]
    operation_id: str | None = None
    causation_key: str | None = None
    sequence: int | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        for name in ("movement_id", "product_id", "unit"):
            _require_text(name, getattr(self, name))
        _require_integer("delta", self.delta)
        if self.delta == 0:
            raise InvalidMovementError("delta must not be zero")
        for name in ("quantity_before", "quantity_after"):
            _require_integer(name, getattr(self, name))
            if getattr(self, name) < 0:
                raise InvalidMovementError(f"{name} must not be negative")
        if self.quantity_after != self.quantity_before + self.delta:
            raise InvalidMovementError(
                "quantity_after must equal quantity_before plus delta"
            )

        try:
            origin = MovementOrigin(self.origin)
        except ValueError:
            raise InvalidMovementError(f"unknown origin {self.origin!r}") from None
        object.__setattr__(self, "origin", origin)
        self._check_causation(origin)

        if not isinstance(self.recorded_at, datetime):
            raise InvalidMovementError("recorded_at must be a datetime")
        if self.recorded_at.utcoffset() is None:
            raise InvalidMovementError("recorded_at must be timezone-aware")
        object.__setattr__(self, "recorded_at", self.recorded_at.astimezone(UTC))

        object.__setattr__(self, "cause", _frozen_cause(origin, self.cause))

    def _check_causation(self, origin: MovementOrigin) -> None:
        if self.operation_id is not None:
            _require_text("operation_id", self.operation_id)
        if self.causation_key is not None:
            _require_text("causation_key", self.causation_key)

        if origin is MovementOrigin.VOICE_OPERATION:
            if self.operation_id is None:
                raise InvalidMovementError("a voice movement needs its operation_id")
            if self.causation_key is None:
                object.__setattr__(self, "causation_key", self.operation_id)
            elif self.causation_key != self.operation_id:
                raise InvalidMovementError(
                    "a voice movement is caused by its operation_id"
                )
        elif self.operation_id is not None:
            raise InvalidMovementError(f"a {origin} movement has no voice operation_id")


def format_utc(moment: datetime) -> str:
    """Return the fixed-width UTC text stored in the database.

    Every value has the same width, so comparing the text compares the time.
    """
    return moment.astimezone(UTC).strftime(UTC_FORMAT)


def parse_utc(text: str) -> datetime:
    """Read a value written by ``format_utc``."""
    return datetime.strptime(text, UTC_FORMAT).replace(tzinfo=UTC)


def _require_text(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InvalidMovementError(f"{name} must be a non-blank string")


def _require_integer(name: str, value: object) -> None:
    if type(value) is not int:
        raise InvalidMovementError(
            f"{name} must be an integer, got {type(value).__name__}"
        )


def _frozen_cause(origin: MovementOrigin, cause: object) -> Mapping[str, Any]:
    if not isinstance(cause, Mapping) or not cause:
        raise InvalidMovementError("cause must be a non-empty mapping")
    required = REQUIRED_CAUSE_KEYS[origin]
    value = cause.get(required)
    if not isinstance(value, str) or not value.strip():
        raise InvalidMovementError(f"a {origin} cause needs a non-blank {required!r}")
    try:
        # Round-trip through JSON: the snapshot must be storable as is, and
        # the copy cannot change if the caller mutates its own mapping later.
        text = json.dumps(dict(cause), allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as error:
        raise InvalidMovementError(f"cause is not plain JSON: {error}") from None
    return MappingProxyType(json.loads(text))
