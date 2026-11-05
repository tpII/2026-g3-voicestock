"""Tests for the inventory movement domain model."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from pi.movement_history import (
    InvalidMovementError,
    InventoryMovement,
    MovementOrigin,
    format_utc,
    parse_utc,
)

MOMENT = datetime(2026, 11, 4, 18, 30, 5, 123456, tzinfo=UTC)


def _voice(**changes) -> InventoryMovement:
    values = {
        "movement_id": "mov-1",
        "product_id": "coca-cola-zero-2l",
        "delta": 3,
        "unit": "unit",
        "quantity_before": 5,
        "quantity_after": 8,
        "origin": MovementOrigin.VOICE_OPERATION,
        "recorded_at": MOMENT,
        "cause": {"recognized_text": "agregá tres coca zero", "operation": "add"},
        "operation_id": "op-1",
    }
    values.update(changes)
    return InventoryMovement(**values)


def _manual(**changes) -> InventoryMovement:
    values = {
        "origin": MovementOrigin.MANUAL_ADJUSTMENT,
        "operation_id": None,
        "cause": {"reason": "conteo físico"},
    }
    values.update(changes)
    return _voice(**values)


def test_a_voice_movement_is_caused_by_its_operation() -> None:
    movement = _voice()

    assert movement.causation_key == "op-1"
    assert movement.sequence is None


def test_a_voice_movement_needs_its_operation_id() -> None:
    with pytest.raises(InvalidMovementError, match="operation_id"):
        _voice(operation_id=None)


def test_a_voice_movement_cannot_use_another_causation_key() -> None:
    with pytest.raises(InvalidMovementError):
        _voice(causation_key="something-else")


@pytest.mark.parametrize(
    "origin", [MovementOrigin.MANUAL_ADJUSTMENT, MovementOrigin.INITIALIZATION]
)
def test_other_origins_are_valid_without_an_operation_id(origin) -> None:
    movement = _manual(origin=origin)

    assert movement.operation_id is None
    assert movement.causation_key is None


def test_other_origins_accept_their_own_causation_key() -> None:
    assert _manual(causation_key="seed:coca").causation_key == "seed:coca"


def test_other_origins_never_carry_a_voice_operation_id() -> None:
    with pytest.raises(InvalidMovementError):
        _manual(operation_id="op-1")


def test_origins_are_read_from_their_text() -> None:
    assert _manual(origin="initialization").origin is MovementOrigin.INITIALIZATION


def test_unknown_origins_are_rejected() -> None:
    with pytest.raises(InvalidMovementError, match="origin"):
        _manual(origin="llm")


@pytest.mark.parametrize("delta", [0, 1.0, Decimal("3"), "3", True])
def test_the_delta_is_an_exact_non_zero_integer(delta) -> None:
    with pytest.raises(InvalidMovementError):
        _voice(delta=delta)


def test_negative_deltas_are_valid() -> None:
    movement = _voice(delta=-5, quantity_before=5, quantity_after=0)

    assert movement.quantity_after == 0


@pytest.mark.parametrize(("before", "after"), [(5, 9), (-1, 2), (2, -1), (5.0, 8.0)])
def test_the_balance_must_follow_the_delta(before, after) -> None:
    with pytest.raises(InvalidMovementError):
        _voice(quantity_before=before, quantity_after=after)


@pytest.mark.parametrize("name", ["movement_id", "product_id", "unit"])
@pytest.mark.parametrize("value", ["", "  ", None, 7])
def test_identity_fields_are_required(name, value) -> None:
    with pytest.raises(InvalidMovementError, match=name):
        _voice(**{name: value})


def test_the_time_must_be_timezone_aware() -> None:
    with pytest.raises(InvalidMovementError, match="timezone"):
        _voice(recorded_at=datetime(2026, 11, 4, 18, 30))


def test_the_time_is_kept_in_utc() -> None:
    argentina = timezone(timedelta(hours=-3))
    local = datetime(2026, 11, 4, 15, 30, 5, 123456, tzinfo=argentina)

    assert _voice(recorded_at=local).recorded_at == MOMENT
    assert _voice(recorded_at=local).recorded_at.tzinfo is UTC


@pytest.mark.parametrize(
    "cause",
    [
        {},
        None,
        "agregá tres",
        {"operation": "add"},
        {"recognized_text": "  "},
        {"recognized_text": "ok", "when": datetime.now(UTC)},
        {"recognized_text": "ok", "amount": float("nan")},
    ],
)
def test_a_voice_cause_must_explain_the_movement_as_json(cause) -> None:
    with pytest.raises(InvalidMovementError, match="cause"):
        _voice(cause=cause)


def test_a_manual_cause_needs_a_reason() -> None:
    with pytest.raises(InvalidMovementError, match="reason"):
        _manual(cause={"recognized_text": "no aplica"})


def test_the_cause_is_a_frozen_copy() -> None:
    cause = {"recognized_text": "agregá tres", "lines": ["coca"]}
    movement = _voice(cause=cause)

    cause["recognized_text"] = "changed"
    cause["lines"].append("arroz")

    assert movement.cause == {"recognized_text": "agregá tres", "lines": ["coca"]}
    with pytest.raises(TypeError):
        movement.cause["recognized_text"] = "changed"


def test_the_sequence_does_not_change_equality() -> None:
    assert _voice(sequence=1) == _voice(sequence=2)


def test_utc_text_has_a_fixed_width_and_round_trips() -> None:
    text = format_utc(MOMENT)

    assert text == "2026-11-04T18:30:05.123456Z"
    assert format_utc(MOMENT.replace(microsecond=0)) == "2026-11-04T18:30:05.000000Z"
    assert parse_utc(text) == MOMENT
