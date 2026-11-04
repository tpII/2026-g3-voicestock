"""Test doubles for the pending-operation slot and executor.

These are not a second production pending-operation model.
"""

import threading
from dataclasses import dataclass

from pi.pending_operation import (
    ExecutionResult,
    ExecutionStatus,
    PendingOperationView,
)


def coca_cola_view() -> PendingOperationView:
    """Fixed snapshot used as the stand-in for a future pending operation."""
    return PendingOperationView(
        operation_id="op-aaa",
        recognized_text="agregar diez unidades de coca cola",
        product="Coca-Cola",
        operation="agregar",
        quantity=10,
        unit="unidad",
        confirmation_message="Agregar 10 unidades de Coca-Cola",
    )


def other_view() -> PendingOperationView:
    """A different pending operation, used for stale-id cases."""
    return PendingOperationView(
        operation_id="op-bbb",
        recognized_text="sacar dos paquetes de arroz",
        product="Arroz",
        operation="sacar",
        quantity=2,
        unit="paquete",
        confirmation_message="Sacar 2 paquetes de Arroz",
    )


@dataclass
class MemorySlot:
    """In-test slot. Production state stays with PendingOperationFlow."""

    current_view: PendingOperationView | None
    clear_count: int = 0

    def current(self) -> PendingOperationView | None:
        return self.current_view

    def clear(self, operation_id: str) -> bool:
        self.clear_count += 1
        if self.current_view is None or self.current_view.operation_id != operation_id:
            return False
        self.current_view = None
        return True


class ScriptedExecutor:
    """Returns a prepared result, or raises, and counts calls."""

    def __init__(
        self,
        result: ExecutionResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or ExecutionResult(status=ExecutionStatus.SUCCESS)
        self.error = error
        self.calls = 0
        self.seen: list[PendingOperationView] = []

    def execute(self, operation: PendingOperationView) -> ExecutionResult:
        self.calls += 1
        self.seen.append(operation)
        if self.error is not None:
            raise self.error
        return self.result


class BlockingExecutor:
    """Blocks inside the first execute so another request can overlap it."""

    def __init__(self) -> None:
        self.calls = 0
        self.entered = threading.Event()
        self.release = threading.Event()

    def execute(self, operation: PendingOperationView) -> ExecutionResult:
        del operation
        self.calls += 1
        self.entered.set()
        if not self.release.wait(2):
            raise TimeoutError("executor was not released")
        return ExecutionResult(status=ExecutionStatus.SUCCESS)
