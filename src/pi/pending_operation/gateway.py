"""Query and resolution policy for the single in-process pending operation.

``PendingOperationFlow`` will own the FSM and supply the slot. This gateway
is the policy that Flow should use, not a second flow and not an HTTP adapter.
One lock covers the whole resolution because VoiceStock has one pending
operation. Another adapter can call the same object and keep the same safety.
"""

import threading
from dataclasses import dataclass

from pi.pending_operation.executor import (
    ExecutionStatus,
    OperationExecutor,
)
from pi.pending_operation.resolution import (
    ResolutionResult,
    ResolutionStatus,
    ResolvedAction,
)
from pi.pending_operation.slot import PendingOperationSlot
from pi.pending_operation.view import PendingOperationView, copy_view


@dataclass(frozen=True)
class _LastResolution:
    """Previous resolution kept in this process, not a history log.

    Only the immediately previous id is remembered. The record disappears
    when the process stops. That is intentional for this increment: it stops
    a lost response from being executed twice, and it is not durable
    idempotency.
    """

    operation_id: str
    action: ResolvedAction


class PendingOperationGateway:
    """Implements the query and resolution ports against a slot and an executor.

    Confirm resolves the pending operation only after the executor reports
    success. A failed execution leaves the slot unchanged. Cancel never calls
    the executor.
    """

    def __init__(
        self,
        slot: PendingOperationSlot,
        executor: OperationExecutor,
    ) -> None:
        self._slot = slot
        self._executor = executor
        self._lock = threading.Lock()
        self._last_resolution: _LastResolution | None = None

    def get_current(self) -> PendingOperationView | None:
        """Return a copy of the public snapshot, or None."""
        with self._lock:
            current = self._slot.current()
            if current is None:
                return None
            return copy_view(current)

    def confirm(self, operation_id: str) -> ResolutionResult:
        """Validate, execute, and only then clear the pending operation."""
        operation_id = _require_operation_id(operation_id)
        with self._lock:
            remembered = self._remembered(operation_id, ResolvedAction.CONFIRM)
            if remembered is not None:
                return remembered
            current = self._current_if_matches(operation_id)
            if isinstance(current, ResolutionResult):
                return current
            snapshot = copy_view(current)
            try:
                execution = self._executor.execute(snapshot)
            except Exception:
                # The pending operation stays in the slot. Clearing it here
                # would drop the only copy of a confirmation that did not run.
                return _execution_failed(operation_id)
            if execution.status is not ExecutionStatus.SUCCESS:
                return _execution_failed(operation_id)
            if not self._slot.clear(operation_id):
                return _stale(operation_id)
            self._remember(operation_id, ResolvedAction.CONFIRM)
            return _success(operation_id, ResolvedAction.CONFIRM)

    def cancel(self, operation_id: str) -> ResolutionResult:
        """Clear a still-current operation without executing it."""
        operation_id = _require_operation_id(operation_id)
        with self._lock:
            remembered = self._remembered(operation_id, ResolvedAction.CANCEL)
            if remembered is not None:
                return remembered
            current = self._current_if_matches(operation_id)
            if isinstance(current, ResolutionResult):
                return current
            if not self._slot.clear(operation_id):
                return _stale(operation_id)
            self._remember(operation_id, ResolvedAction.CANCEL)
            return _success(operation_id, ResolvedAction.CANCEL)

    def _current_if_matches(
        self,
        operation_id: str,
    ) -> PendingOperationView | ResolutionResult:
        current = self._slot.current()
        if current is None:
            return ResolutionResult(status=ResolutionStatus.NO_PENDING)
        if current.operation_id != operation_id:
            return _stale(operation_id)
        return current

    def _remembered(
        self,
        operation_id: str,
        requested: ResolvedAction,
    ) -> ResolutionResult | None:
        last = self._last_resolution
        if last is None or last.operation_id != operation_id:
            return None
        if last.action is requested:
            return ResolutionResult(
                status=ResolutionStatus.ALREADY_RESOLVED,
                operation_id=operation_id,
                resolved_action=last.action,
            )
        return ResolutionResult(
            status=ResolutionStatus.CONFLICT,
            operation_id=operation_id,
            resolved_action=last.action,
        )

    def _remember(self, operation_id: str, action: ResolvedAction) -> None:
        self._last_resolution = _LastResolution(
            operation_id=operation_id,
            action=action,
        )


def _require_operation_id(operation_id: str) -> str:
    if not isinstance(operation_id, str) or not operation_id.strip():
        raise ValueError("operation_id must be a non-blank string")
    return operation_id


def _success(operation_id: str, action: ResolvedAction) -> ResolutionResult:
    return ResolutionResult(
        status=ResolutionStatus.SUCCESS,
        operation_id=operation_id,
        resolved_action=action,
    )


def _stale(operation_id: str) -> ResolutionResult:
    return ResolutionResult(
        status=ResolutionStatus.STALE_OPERATION,
        operation_id=operation_id,
    )


def _execution_failed(operation_id: str) -> ResolutionResult:
    return ResolutionResult(
        status=ResolutionStatus.EXECUTION_FAILED,
        operation_id=operation_id,
    )
