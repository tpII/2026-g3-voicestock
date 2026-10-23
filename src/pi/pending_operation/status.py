"""Public snapshot of the operation cycle. It is not the FSM itself."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from pi.pending_operation.view import PendingOperationView


class OperationPhase(StrEnum):
    """Phase a caller can show without driving the cycle."""

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    WAIT_CONFIRMATION = "wait_confirmation"


_PHASE_TEXT = {
    OperationPhase.IDLE: ("Listo para escuchar", "Presioná el botón para hablar"),
    OperationPhase.RECORDING: ("Escuchando...", "Soltá el botón para terminar"),
    OperationPhase.PROCESSING: ("Procesando solicitud...", ""),
    OperationPhase.WAIT_CONFIRMATION: ("Operación pendiente de confirmación", ""),
}


@dataclass(frozen=True, slots=True)
class OperationCycleStatus:
    """What the operator UI may display for the current phase.

    ``pending_operation`` is present only while the phase is
    ``wait_confirmation``. ``operator_message`` explains the previous attempt
    when the cycle returned to idle without an operation.
    """

    phase: OperationPhase
    headline: str
    detail: str
    operator_message: str | None
    pending_operation: PendingOperationView | None


def describe_phase(phase: OperationPhase) -> tuple[str, str]:
    """Return the headline and the secondary line for ``phase``."""
    return _PHASE_TEXT[phase]


@runtime_checkable
class OperationCycleQueryPort(Protocol):
    """Read the public phase. Callers cannot change it through this port."""

    def get_status(self) -> OperationCycleStatus:
        """Return the current phase and the text that describes it."""
