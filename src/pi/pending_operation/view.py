"""Read model shown to callers outside the pending-operation owner."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PendingOperationView:
    """Snapshot a web client can render without holding the domain object.

    ``operation`` is an opaque label supplied by the future owner, not an FSM
    state and not an inventory command. ``operation_id`` is required so a
    later confirm or cancel names one operation instead of "whatever is
    current".
    """

    operation_id: str
    recognized_text: str
    product: str
    operation: str
    quantity: int
    unit: str
    confirmation_message: str

    def __post_init__(self) -> None:
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise ValueError("operation_id must be a non-blank string")


def copy_view(source: PendingOperationView) -> PendingOperationView:
    """Return a view that carries only the public snapshot fields."""
    return PendingOperationView(
        operation_id=source.operation_id,
        recognized_text=source.recognized_text,
        product=source.product,
        operation=source.operation,
        quantity=source.quantity,
        unit=source.unit,
        confirmation_message=source.confirmation_message,
    )
