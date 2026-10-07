"""Typed outcomes of confirming or cancelling one pending operation.

These statuses belong to the application layer. They are not HTTP codes.
"""

from dataclasses import dataclass
from enum import StrEnum


class ResolutionStatus(StrEnum):
    """Why a confirm or cancel request ended the way it did."""

    SUCCESS = "success"
    NO_PENDING = "no_pending"
    STALE_OPERATION = "stale_operation"
    ALREADY_RESOLVED = "already_resolved"
    CONFLICT = "conflict"
    EXECUTION_FAILED = "execution_failed"


class ResolvedAction(StrEnum):
    """Resolution that was applied, or that already won for this id."""

    CONFIRM = "confirm"
    CANCEL = "cancel"


_ACTION_REQUIRED = {
    ResolutionStatus.SUCCESS,
    ResolutionStatus.ALREADY_RESOLVED,
    ResolutionStatus.CONFLICT,
}


@dataclass(frozen=True)
class ResolutionResult:
    """Outcome of one ``confirm`` or ``cancel`` call.

    ``resolved_action`` is the action that stands for ``operation_id``:
    the action just applied on success, or the action already recorded when
    the request is a retry or the opposite action. It is empty when nothing
    was resolved.
    """

    status: ResolutionStatus
    operation_id: str | None = None
    resolved_action: ResolvedAction | None = None

    def __post_init__(self) -> None:
        if self.status in _ACTION_REQUIRED:
            if not self.operation_id or self.resolved_action is None:
                raise ValueError(
                    f"{self.status} requires operation_id and resolved_action"
                )
        elif self.status is ResolutionStatus.STALE_OPERATION:
            if not self.operation_id or self.resolved_action is not None:
                raise ValueError("stale_operation carries only the requested id")
        elif self.status is ResolutionStatus.EXECUTION_FAILED:
            if not self.operation_id or self.resolved_action is not None:
                raise ValueError("execution_failed carries only the requested id")
        elif self.operation_id is not None or self.resolved_action is not None:
            raise ValueError("no_pending does not name a resolved operation")
