"""HTTP bodies for the pending-operation API.

These models are the web contract. They are not the application dataclasses.
"""

from pydantic import BaseModel, ConfigDict

from pi.pending_operation import (
    OperationCycleStatus,
    OperationPhase,
    PendingOperationView,
    ResolutionResult,
)
from pi.pending_operation.resolution import ResolutionStatus, ResolvedAction


class PendingOperationResponse(BaseModel):
    """Public snapshot returned when a pending operation exists."""

    model_config = ConfigDict(extra="forbid")

    operation_id: str
    recognized_text: str
    product: str
    operation: str
    quantity: int
    unit: str
    confirmation_message: str

    @classmethod
    def from_view(cls, view: PendingOperationView) -> "PendingOperationResponse":
        """Copy only the fields the view publishes."""
        return cls(
            operation_id=view.operation_id,
            recognized_text=view.recognized_text,
            product=view.product,
            operation=view.operation,
            quantity=view.quantity,
            unit=view.unit,
            confirmation_message=view.confirmation_message,
        )


class ResolutionResponse(BaseModel):
    """HTTP view of one ``ResolutionResult``."""

    model_config = ConfigDict(extra="forbid")

    status: ResolutionStatus
    operation_id: str | None = None
    resolved_action: ResolvedAction | None = None

    @classmethod
    def from_result(cls, result: ResolutionResult) -> "ResolutionResponse":
        """Copy the application outcome without adding fields."""
        return cls(
            status=result.status,
            operation_id=result.operation_id,
            resolved_action=result.resolved_action,
        )


class SystemStatusResponse(BaseModel):
    """Public phase of the Raspberry Pi operation cycle."""

    model_config = ConfigDict(extra="forbid")

    phase: OperationPhase
    headline: str
    detail: str
    operator_message: str | None = None
    pending_operation: PendingOperationResponse | None = None

    @classmethod
    def from_status(cls, status: OperationCycleStatus) -> "SystemStatusResponse":
        """Copy the cycle snapshot. The pending view stays the existing contract."""
        pending = status.pending_operation
        return cls(
            phase=status.phase,
            headline=status.headline,
            detail=status.detail,
            operator_message=status.operator_message,
            pending_operation=(
                None if pending is None else PendingOperationResponse.from_view(pending)
            ),
        )


class ErrorResponse(BaseModel):
    """Stable HTTP error that is not a resolution outcome."""

    model_config = ConfigDict(extra="forbid")

    code: str
    detail: str
