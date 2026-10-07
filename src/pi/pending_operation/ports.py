"""Application ports the future web adapter calls.

The ports do not mention HTTP. A route may call them. It may not own the
pending operation or change the FSM.
"""

from typing import Protocol, runtime_checkable

from pi.pending_operation.resolution import ResolutionResult
from pi.pending_operation.view import PendingOperationView


@runtime_checkable
class PendingOperationQueryPort(Protocol):
    """Read the current pending operation, if one exists."""

    def get_current(self) -> PendingOperationView | None:
        """Return a snapshot, or None when nothing is waiting for the operator."""


@runtime_checkable
class PendingOperationResolutionPort(Protocol):
    """Confirm or cancel one named pending operation.

    ``operation_id`` is mandatory. There is no ``confirm_current``: a stale
    page must not resolve whatever became current after it rendered.
    """

    def confirm(self, operation_id: str) -> ResolutionResult:
        """Execute and then resolve ``operation_id``, when it is still current."""

    def cancel(self, operation_id: str) -> ResolutionResult:
        """Resolve ``operation_id`` without executing an inventory operation."""
