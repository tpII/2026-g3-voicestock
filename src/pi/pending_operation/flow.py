"""Operation cycle of the Raspberry Pi: capture, PC response, confirm, cancel.

The flow owns the only pending operation and the phase that exposes it.
Confirm and cancel go through ``PendingOperationGateway``. Sending audio and
validating the contract stay in their own objects; this module only orders
them and keeps the phase consistent.
"""

import logging
import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from pi.audio.errors import AudioCaptureError
from pi.communication import AudioInterpretationClient
from pi.operation_contract import OperationValidator
from pi.pending_operation.executor import (
    OperationExecutor,
    ProvisionalOperationExecutor,
)
from pi.pending_operation.gateway import PendingOperationGateway
from pi.pending_operation.operation import PendingOperation
from pi.pending_operation.ports import (
    PendingOperationQueryPort,
    PendingOperationResolutionPort,
)
from pi.pending_operation.response import (
    OutcomeKind,
    PcResponseInterpreter,
)
from pi.pending_operation.status import (
    OperationCycleStatus,
    OperationPhase,
    describe_phase,
)
from pi.pending_operation.view import PendingOperationView
from pi.push_to_talk import RecordingSender
from pi.push_to_talk.result import AudioCaptureResult
from shared.communication import TransportEnvelope

logger = logging.getLogger(__name__)

CAPTURE_FAILED = "No se pudo grabar el audio. Presioná el botón para intentar de nuevo."
_OPERATOR_MESSAGES = {
    OutcomeKind.TRANSPORT_ERROR: (
        "No se pudo comunicar con la PC. Presioná el botón para intentar de nuevo."
    ),
    OutcomeKind.SERVICE_ERROR: (
        "La PC no pudo interpretar el pedido. Presioná el botón para intentar de nuevo."
    ),
    OutcomeKind.CONTRACT_REJECTION: (
        "El pedido no es una operación válida. "
        "Presioná el botón para intentar de nuevo."
    ),
}
UNEXPECTED = "Ocurrió un error inesperado. Presioná el botón para intentar de nuevo."


class PendingOperationFlow:
    """Single in-process cycle from an idle device back to an idle device.

    Push-to-talk callbacks return as soon as the phase changes. The PC request
    runs on a worker so a GPIO notification and a status read are not stuck
    behind the network timeout. The gateway is the only object that clears a
    pending operation.
    """

    def __init__(
        self,
        client: AudioInterpretationClient,
        validator: OperationValidator,
        executor: OperationExecutor | None = None,
        *,
        delete_after_send: bool = True,
        operation_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._interpreter = PcResponseInterpreter(validator)
        self._delete_after_send = delete_after_send
        self._sender = RecordingSender(
            client,
            self._on_sent,
            delete_after_send=delete_after_send,
        )
        self._operation_ids = operation_id_factory or (lambda: str(uuid.uuid4()))
        self._jobs_pool = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="voicestock-operation-cycle",
        )
        self._phase = OperationPhase.IDLE
        self._pending: PendingOperation | None = None
        self._operator_message: str | None = None
        self._jobs = 0
        self._closed = False
        self._lock = threading.Condition()
        self._gateway = PendingOperationGateway(
            self,
            executor if executor is not None else ProvisionalOperationExecutor(),
        )

    @property
    def query_port(self) -> PendingOperationQueryPort:
        """Read the current pending operation through the gateway."""
        return self._gateway

    @property
    def resolution_port(self) -> PendingOperationResolutionPort:
        """Confirm or cancel through the gateway, without a second policy."""
        return self._gateway

    def try_begin_recording(self) -> bool:
        """Move from idle to recording. Return False when a cycle is already open."""
        with self._lock:
            if (
                self._closed
                or self._phase is not OperationPhase.IDLE
                or self._pending is not None
            ):
                return False
            self._phase = OperationPhase.RECORDING
            self._operator_message = None
            return True

    def on_capture_completed(self, result: AudioCaptureResult) -> None:
        """Accept one finished recording and process it away from the caller."""
        with self._lock:
            accepted = self._accept_recording()
            if accepted:
                self._jobs += 1
        if not accepted:
            self._discard(result)
            return
        try:
            self._jobs_pool.submit(self._process, result)
        except RuntimeError:
            logger.exception("operation cycle could not be scheduled")
            self._abandon(UNEXPECTED)
            with self._lock:
                self._jobs -= 1
                self._lock.notify_all()
            self._discard(result)

    def on_capture_error(self, error: AudioCaptureError) -> None:
        """Drop a failed capture and return to idle. No operation is created."""
        logger.warning("audio capture failed: %s", error)
        with self._lock:
            if self._phase is not OperationPhase.RECORDING:
                return
            self._phase = OperationPhase.IDLE
            self._operator_message = CAPTURE_FAILED

    def get_status(self) -> OperationCycleStatus:
        """Return the phase and the text the operator UI should show."""
        with self._lock:
            phase = self._phase
            operator_message = self._operator_message
            pending = None if self._pending is None else self._pending.to_view()
        headline, detail = describe_phase(phase)
        return OperationCycleStatus(
            phase=phase,
            headline=headline,
            detail=detail,
            operator_message=operator_message,
            pending_operation=pending,
        )

    def current(self) -> PendingOperationView | None:
        """Slot read used by the gateway. Returns a view, not the domain object."""
        with self._lock:
            if self._pending is None:
                return None
            return self._pending.to_view()

    def clear(self, operation_id: str) -> bool:
        """Drop the pending operation when the gateway resolved this id.

        A successful clear is the return to idle. A failed confirm never
        reaches this method, so the operation stays pending.
        """
        with self._lock:
            pending = self._pending
            if pending is None or pending.operation_id != operation_id:
                return False
            if self._phase is not OperationPhase.WAIT_CONFIRMATION:
                return False
            self._pending = None
            self._phase = OperationPhase.IDLE
            self._operator_message = None
            return True

    def wait_until_settled(self, timeout: float = 2.0) -> None:
        """Block until the current PC request has finished. For tests and shutdown."""
        with self._lock:
            finished = self._lock.wait_for(lambda: self._jobs == 0, timeout)
        if not finished:
            raise TimeoutError("operation cycle did not settle")

    def close(self) -> None:
        """Stop accepting work and wait for the current PC request to finish."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self._jobs_pool.shutdown(wait=True)

    def _accept_recording(self) -> bool:
        if self._closed or self._phase is not OperationPhase.RECORDING:
            return False
        if self._pending is not None:
            return False
        self._phase = OperationPhase.PROCESSING
        self._operator_message = None
        return True

    def _process(self, result: AudioCaptureResult) -> None:
        try:
            try:
                self._sender(result)
            except Exception:
                logger.exception("operation cycle failed while sending the recording")
                self._abandon(UNEXPECTED)
        finally:
            with self._lock:
                self._jobs -= 1
                self._lock.notify_all()

    def _on_sent(self, result: AudioCaptureResult, envelope: TransportEnvelope) -> None:
        del result
        try:
            outcome = self._interpreter.interpret(envelope)
        except Exception:
            logger.exception("operation cycle failed while reading the PC response")
            self._abandon(UNEXPECTED)
            return
        if (
            outcome.kind is not OutcomeKind.ACCEPTED
            or outcome.validated_operation is None
        ):
            logger.warning(
                "operation cycle ended without a pending operation: %s (%s)",
                outcome.kind,
                outcome.detail,
            )
            self._abandon(_OPERATOR_MESSAGES.get(outcome.kind, UNEXPECTED))
            return
        try:
            pending = PendingOperation.from_validated(
                outcome.validated_operation,
                outcome.recognized_text,
                operation_id=self._operation_ids(),
            )
        except (TypeError, ValueError):
            logger.exception("validated operation could not become a pending operation")
            self._abandon(UNEXPECTED)
            return
        with self._lock:
            if (
                self._phase is not OperationPhase.PROCESSING
                or self._pending is not None
            ):
                logger.error("refusing to replace the current operation")
                return
            if self._closed:
                self._phase = OperationPhase.IDLE
                self._operator_message = None
                return
            self._pending = pending
            self._phase = OperationPhase.WAIT_CONFIRMATION
            self._operator_message = None

    def _abandon(self, message: str) -> None:
        with self._lock:
            if (
                self._phase is not OperationPhase.PROCESSING
                or self._pending is not None
            ):
                return
            self._phase = OperationPhase.IDLE
            self._operator_message = message

    def _discard(self, result: AudioCaptureResult) -> None:
        if self._delete_after_send:
            result.artifact.cleanup()
