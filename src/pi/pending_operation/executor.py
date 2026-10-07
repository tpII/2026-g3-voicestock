"""Inventory effect of a confirmed operation, behind a replaceable executor."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from pi.pending_operation.view import PendingOperationView


class ExecutionStatus(StrEnum):
    """Whether the inventory effect of one confirmation finished."""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class ExecutionResult:
    """Result of ``OperationExecutor.execute``.

    Failure means the pending operation must stay pending. The executor does
    not clear it.
    """

    status: ExecutionStatus


class OperationExecutor(Protocol):
    """Runs the inventory effect for a confirmation.

    A later ``InventoryOperationExecutor`` replaces the October stand-in
    without a change to the web adapter. Implementations must not confirm,
    cancel, or clear the pending operation, and must not call back into the
    gateway that invoked them.
    """

    def execute(self, operation: PendingOperationView) -> ExecutionResult:
        """Apply ``operation``. Return failure instead of clearing it."""


class ProvisionalOperationExecutor:
    """October stand-in that reports success and changes nothing.

    It does not modify inventory, write history, or persist the resolution.
    ``PendingOperationFlow`` is expected to replace this object with the real
    inventory executor. The web adapter depends on ``OperationExecutor``, not
    on this class.
    """

    def execute(self, operation: PendingOperationView) -> ExecutionResult:
        """Accept the snapshot and report success without applying it."""
        return ExecutionResult(status=ExecutionStatus.SUCCESS)
