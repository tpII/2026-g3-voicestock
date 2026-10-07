"""Confirm and cancel outcomes, including retries and executor failure."""

import pytest
from fakes import (
    MemorySlot,
    ScriptedExecutor,
    coca_cola_view,
    other_view,
)

from pi.pending_operation import (
    ExecutionResult,
    ExecutionStatus,
    PendingOperationGateway,
    PendingOperationResolutionPort,
    ProvisionalOperationExecutor,
    ResolutionStatus,
    ResolvedAction,
)


def test_confirm_succeeds_and_clears_only_after_execution() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(slot, executor)

    result = gateway.confirm(view.operation_id)

    assert isinstance(gateway, PendingOperationResolutionPort)
    assert result.status is ResolutionStatus.SUCCESS
    assert result.operation_id == view.operation_id
    assert result.resolved_action is ResolvedAction.CONFIRM
    assert executor.calls == 1
    assert executor.seen == [view]
    assert slot.current_view is None
    assert slot.clear_count == 1
    assert gateway.get_current() is None


def test_provisional_executor_reports_success_without_clearing_by_itself() -> None:
    view = coca_cola_view()
    execution = ProvisionalOperationExecutor().execute(view)

    assert execution == ExecutionResult(status=ExecutionStatus.SUCCESS)


def test_confirm_with_provisional_executor_resolves_the_pending_operation() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    gateway = PendingOperationGateway(slot, ProvisionalOperationExecutor())

    result = gateway.confirm(view.operation_id)

    assert result.status is ResolutionStatus.SUCCESS
    assert slot.current_view is None


def test_confirm_when_nothing_is_pending() -> None:
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(MemorySlot(None), executor)

    result = gateway.confirm("op-aaa")

    assert result.status is ResolutionStatus.NO_PENDING
    assert result.operation_id is None
    assert result.resolved_action is None
    assert executor.calls == 0


def test_confirm_rejects_a_stale_operation_id_and_keeps_the_current_one() -> None:
    current = other_view()
    slot = MemorySlot(current)
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(slot, executor)

    result = gateway.confirm(coca_cola_view().operation_id)

    assert result.status is ResolutionStatus.STALE_OPERATION
    assert result.operation_id == "op-aaa"
    assert result.resolved_action is None
    assert executor.calls == 0
    assert slot.current_view == current
    assert slot.clear_count == 0


def test_confirm_retry_does_not_execute_again() -> None:
    view = coca_cola_view()
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(MemorySlot(view), executor)

    first = gateway.confirm(view.operation_id)
    second = gateway.confirm(view.operation_id)

    assert first.status is ResolutionStatus.SUCCESS
    assert second.status is ResolutionStatus.ALREADY_RESOLVED
    assert second.operation_id == view.operation_id
    assert second.resolved_action is ResolvedAction.CONFIRM
    assert executor.calls == 1


def test_confirm_after_cancel_conflicts_and_does_not_execute() -> None:
    view = coca_cola_view()
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(MemorySlot(view), executor)

    cancelled = gateway.cancel(view.operation_id)
    confirmed = gateway.confirm(view.operation_id)

    assert cancelled.status is ResolutionStatus.SUCCESS
    assert cancelled.resolved_action is ResolvedAction.CANCEL
    assert confirmed.status is ResolutionStatus.CONFLICT
    assert confirmed.operation_id == view.operation_id
    assert confirmed.resolved_action is ResolvedAction.CANCEL
    assert executor.calls == 0


def test_executor_failure_keeps_the_pending_operation() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = ScriptedExecutor(
        result=ExecutionResult(status=ExecutionStatus.FAILED),
    )
    gateway = PendingOperationGateway(slot, executor)

    result = gateway.confirm(view.operation_id)

    assert result.status is ResolutionStatus.EXECUTION_FAILED
    assert result.operation_id == view.operation_id
    assert result.resolved_action is None
    assert executor.calls == 1
    assert slot.current_view == view
    assert slot.clear_count == 0
    assert gateway.get_current() == view


def test_executor_exception_keeps_the_pending_operation() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = ScriptedExecutor(error=RuntimeError("inventory unavailable"))
    gateway = PendingOperationGateway(slot, executor)

    result = gateway.confirm(view.operation_id)

    assert result.status is ResolutionStatus.EXECUTION_FAILED
    assert slot.current_view == view
    assert gateway.get_current() == view


def test_failed_confirm_can_be_retried() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = ScriptedExecutor(
        result=ExecutionResult(status=ExecutionStatus.FAILED),
    )
    gateway = PendingOperationGateway(slot, executor)

    failed = gateway.confirm(view.operation_id)
    executor.result = ExecutionResult(status=ExecutionStatus.SUCCESS)
    retried = gateway.confirm(view.operation_id)

    assert failed.status is ResolutionStatus.EXECUTION_FAILED
    assert retried.status is ResolutionStatus.SUCCESS
    assert executor.calls == 2
    assert slot.current_view is None


def test_cancel_succeeds_without_executing() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(slot, executor)

    result = gateway.cancel(view.operation_id)

    assert result.status is ResolutionStatus.SUCCESS
    assert result.operation_id == view.operation_id
    assert result.resolved_action is ResolvedAction.CANCEL
    assert executor.calls == 0
    assert slot.current_view is None
    assert gateway.get_current() is None


def test_cancel_when_nothing_is_pending() -> None:
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(MemorySlot(None), executor)

    result = gateway.cancel("op-aaa")

    assert result.status is ResolutionStatus.NO_PENDING
    assert executor.calls == 0


def test_cancel_rejects_a_stale_operation_id() -> None:
    current = other_view()
    slot = MemorySlot(current)
    gateway = PendingOperationGateway(slot, ScriptedExecutor())

    result = gateway.cancel("op-aaa")

    assert result.status is ResolutionStatus.STALE_OPERATION
    assert result.operation_id == "op-aaa"
    assert slot.current_view == current


def test_cancel_retry_is_already_resolved() -> None:
    view = coca_cola_view()
    gateway = PendingOperationGateway(MemorySlot(view), ScriptedExecutor())

    first = gateway.cancel(view.operation_id)
    second = gateway.cancel(view.operation_id)

    assert first.status is ResolutionStatus.SUCCESS
    assert second.status is ResolutionStatus.ALREADY_RESOLVED
    assert second.resolved_action is ResolvedAction.CANCEL


def test_cancel_after_confirm_conflicts_and_does_not_execute_again() -> None:
    view = coca_cola_view()
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(MemorySlot(view), executor)

    confirmed = gateway.confirm(view.operation_id)
    cancelled = gateway.cancel(view.operation_id)

    assert confirmed.status is ResolutionStatus.SUCCESS
    assert cancelled.status is ResolutionStatus.CONFLICT
    assert cancelled.resolved_action is ResolvedAction.CONFIRM
    assert executor.calls == 1


def test_remembered_resolution_is_lost_with_the_gateway_instance() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    first = PendingOperationGateway(slot, ProvisionalOperationExecutor())
    assert first.confirm(view.operation_id).status is ResolutionStatus.SUCCESS

    executor = ScriptedExecutor()
    restarted = PendingOperationGateway(slot, executor)

    result = restarted.confirm(view.operation_id)

    assert result.status is ResolutionStatus.NO_PENDING
    assert executor.calls == 0


def test_a_later_operation_replaces_the_remembered_resolution() -> None:
    first_view = coca_cola_view()
    second_view = other_view()
    slot = MemorySlot(first_view)
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(slot, executor)
    gateway.confirm(first_view.operation_id)
    slot.current_view = second_view

    resolved = gateway.confirm(second_view.operation_id)
    forgotten = gateway.confirm(first_view.operation_id)

    assert resolved.status is ResolutionStatus.SUCCESS
    assert forgotten.status is ResolutionStatus.NO_PENDING
    assert executor.calls == 2


@pytest.mark.parametrize("method_name", ["confirm", "cancel"])
@pytest.mark.parametrize("operation_id", ["", "   "])
def test_resolution_requires_an_operation_id(
    method_name: str, operation_id: str
) -> None:
    gateway = PendingOperationGateway(MemorySlot(coca_cola_view()), ScriptedExecutor())

    with pytest.raises(ValueError, match="operation_id"):
        getattr(gateway, method_name)(operation_id)
