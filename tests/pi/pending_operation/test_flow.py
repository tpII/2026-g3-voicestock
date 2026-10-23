"""Operation cycle: one pending operation, then back to idle."""

import threading
import wave
from pathlib import Path

import pytest
from fakes import ScriptedExecutor

from pi.audio.artifact import AudioArtifact
from pi.audio.errors import AudioStreamError
from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    load_catalog,
)
from pi.pending_operation import (
    ExecutionResult,
    ExecutionStatus,
    OperationPhase,
    PendingOperationFlow,
    ResolutionStatus,
)
from pi.pending_operation.flow import (
    _OPERATOR_MESSAGES,
    CAPTURE_FAILED,
    UNEXPECTED,
)
from pi.pending_operation.response import OutcomeKind
from pi.push_to_talk import (
    AudioCaptureResult,
    PushToTalkController,
    TerminationReason,
)
from pi.push_to_talk.result import CAPTURED_AUDIO_FORMAT
from shared.communication import TransportEnvelope

CATALOG = (
    Path(__file__).parents[2]
    / "fixtures"
    / "operation_contract"
    / "october_catalog.json"
)


class CountingValidator(OperationValidator):
    def __init__(self) -> None:
        self.inner = OperationValidator(InMemoryProductResolver(load_catalog(CATALOG)))
        self.calls = 0

    def validate(self, payload: object):  # type: ignore[override]
        self.calls += 1
        return self.inner.validate(payload)


class EnvelopeClient:
    def __init__(self, *envelopes: TransportEnvelope) -> None:
        self._envelopes = list(envelopes)
        self.calls = 0
        self.started = threading.Event()
        self.release = threading.Event()
        self.block = False

    def interpret_audio(self, wav_path: Path) -> TransportEnvelope:
        self.calls += 1
        wav_path.read_bytes()
        self.started.set()
        if self.block and not self.release.wait(2):
            raise TimeoutError("client was not released")
        return self._envelopes.pop(0)


class ExplodingClient:
    def interpret_audio(self, wav_path: Path) -> TransportEnvelope:
        wav_path.read_bytes()
        raise RuntimeError("socket exploded")


def _contract(recognized_text: str | None = "sumá dos coca zero") -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "1",
        "operations": [
            {
                "operation": "add_stock",
                "product": {"name": "Coca Cola Zero 2L"},
                "quantity": 2,
                "unit": "unit",
            }
        ],
    }
    if recognized_text is not None:
        payload["recognized_text"] = recognized_text
    return payload


def _success(payload: object | None = None) -> TransportEnvelope:
    return TransportEnvelope.success(
        {
            "status": "success",
            "payload": _contract() if payload is None else payload,
            "error": None,
        }
    )


def _service_error() -> TransportEnvelope:
    return TransportEnvelope.success(
        {
            "status": "error",
            "payload": None,
            "error": {"code": "provider_failure", "detail": "model down"},
        }
    )


def _wav(path: Path) -> AudioCaptureResult:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16_000)
        wav_file.writeframes(b"\x00\x00" * 1600)
    return AudioCaptureResult(
        artifact=AudioArtifact(path.stem, path),
        duration=0.1,
        format=CAPTURED_AUDIO_FORMAT,
        termination_reason=TerminationReason.RELEASED,
    )


def _flow(
    client: object,
    validator: CountingValidator | None = None,
    **kwargs: object,
) -> PendingOperationFlow:
    return PendingOperationFlow(
        client,  # type: ignore[arg-type]
        validator or CountingValidator(),
        delete_after_send=True,
        **kwargs,  # type: ignore[arg-type]
    )


def _finish(flow: PendingOperationFlow, result: AudioCaptureResult) -> None:
    assert flow.try_begin_recording() is True
    flow.on_capture_completed(result)
    flow.wait_until_settled()


def test_idle_accepts_one_capture_and_recording_rejects_another(
    tmp_path: Path,
) -> None:
    flow = _flow(EnvelopeClient(_success()))
    try:
        status = flow.get_status()
        assert status.phase is OperationPhase.IDLE
        assert status.headline == "Listo para escuchar"
        assert status.detail == "Presioná el botón para hablar"
        assert status.pending_operation is None
        assert flow.query_port.get_current() is None

        assert flow.try_begin_recording() is True
        recording = flow.get_status()
        assert recording.phase is OperationPhase.RECORDING
        assert recording.headline == "Escuchando..."
        assert recording.detail == "Soltá el botón para terminar"
        assert flow.try_begin_recording() is False
        assert flow.query_port.get_current() is None
    finally:
        flow.close()


def test_a_valid_response_creates_one_pending_operation(tmp_path: Path) -> None:
    validator = CountingValidator()
    client = EnvelopeClient(_success())
    flow = _flow(client, validator)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))

        status = flow.get_status()
        assert status.phase is OperationPhase.WAIT_CONFIRMATION
        assert status.headline == "Operación pendiente de confirmación"
        assert status.pending_operation is not None
        assert status.pending_operation.recognized_text == "sumá dos coca zero"
        assert status.pending_operation.product == "Coca Cola Zero 2L"
        assert flow.query_port.get_current() == status.pending_operation
        assert validator.calls == 1
        assert client.calls == 1
        assert flow.try_begin_recording() is False
        assert not (tmp_path / "take.wav").exists()
    finally:
        flow.close()


def test_a_second_capture_cannot_replace_the_pending_operation(
    tmp_path: Path,
) -> None:
    client = EnvelopeClient(_success(), _success())
    flow = _flow(client)
    try:
        _finish(flow, _wav(tmp_path / "first.wav"))
        current = flow.query_port.get_current()
        assert current is not None

        assert flow.try_begin_recording() is False
        flow.on_capture_completed(_wav(tmp_path / "second.wav"))
        flow.wait_until_settled()

        assert client.calls == 1
        assert flow.query_port.get_current() == current
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION
    finally:
        flow.close()


@pytest.mark.parametrize(
    ("envelope", "kind"),
    [
        (TransportEnvelope.failure("timeout", "slow"), OutcomeKind.TRANSPORT_ERROR),
        (_service_error(), OutcomeKind.SERVICE_ERROR),
        (
            _success({"received_audio": {"size_bytes": 4}}),
            OutcomeKind.CONTRACT_REJECTION,
        ),
    ],
)
def test_failed_responses_return_to_idle_without_a_pending_operation(
    tmp_path: Path,
    envelope: TransportEnvelope,
    kind: OutcomeKind,
) -> None:
    validator = CountingValidator()
    flow = _flow(EnvelopeClient(envelope), validator)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))

        status = flow.get_status()
        assert status.phase is OperationPhase.IDLE
        assert status.pending_operation is None
        assert status.operator_message == _OPERATOR_MESSAGES[kind]
        assert flow.try_begin_recording() is True
        if kind is OutcomeKind.CONTRACT_REJECTION:
            assert validator.calls == 1
        else:
            assert validator.calls == 0
    finally:
        flow.close()


def test_a_failed_capture_returns_to_idle(tmp_path: Path) -> None:
    del tmp_path
    flow = _flow(EnvelopeClient())
    try:
        assert flow.try_begin_recording() is True
        flow.on_capture_error(AudioStreamError("microphone unavailable"))

        status = flow.get_status()
        assert status.phase is OperationPhase.IDLE
        assert status.operator_message == CAPTURE_FAILED
        assert status.pending_operation is None
        assert flow.try_begin_recording() is True
    finally:
        flow.close()


def test_an_unexpected_send_error_does_not_stick_in_processing(
    tmp_path: Path,
) -> None:
    flow = _flow(ExplodingClient())
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))

        status = flow.get_status()
        assert status.phase is OperationPhase.IDLE
        assert status.operator_message == UNEXPECTED
        assert status.pending_operation is None
        assert flow.try_begin_recording() is True
    finally:
        flow.close()


def test_confirm_uses_the_gateway_and_returns_to_idle(tmp_path: Path) -> None:
    executor = ScriptedExecutor()
    flow = _flow(EnvelopeClient(_success()), executor=executor)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None

        result = flow.resolution_port.confirm(current.operation_id)

        assert result.status is ResolutionStatus.SUCCESS
        assert executor.calls == 1
        assert executor.seen == [current]
        assert flow.get_status().phase is OperationPhase.IDLE
        assert flow.query_port.get_current() is None
        assert flow.resolution_port.confirm(current.operation_id).status is (
            ResolutionStatus.ALREADY_RESOLVED
        )
    finally:
        flow.close()


def test_cancel_returns_to_idle_without_executing(tmp_path: Path) -> None:
    executor = ScriptedExecutor()
    flow = _flow(EnvelopeClient(_success()), executor=executor)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None

        result = flow.resolution_port.cancel(current.operation_id)

        assert result.status is ResolutionStatus.SUCCESS
        assert executor.calls == 0
        assert flow.get_status().phase is OperationPhase.IDLE
        assert flow.query_port.get_current() is None
    finally:
        flow.close()


def test_a_failed_execution_keeps_the_pending_operation(tmp_path: Path) -> None:
    executor = ScriptedExecutor(ExecutionResult(status=ExecutionStatus.FAILED))
    flow = _flow(EnvelopeClient(_success()), executor=executor)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None

        result = flow.resolution_port.confirm(current.operation_id)

        assert result.status is ResolutionStatus.EXECUTION_FAILED
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION
        assert flow.query_port.get_current() == current
    finally:
        flow.close()


def test_a_stale_id_does_not_clear_the_current_operation(tmp_path: Path) -> None:
    flow = _flow(EnvelopeClient(_success()))
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))

        result = flow.resolution_port.confirm("op-other")

        assert result.status is ResolutionStatus.STALE_OPERATION
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION
        assert flow.query_port.get_current() is not None
    finally:
        flow.close()


def test_confirmation_does_not_write_an_inventory_file(tmp_path: Path) -> None:
    flow = _flow(EnvelopeClient(_success()))
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None
        flow.resolution_port.confirm(current.operation_id)

        assert list(tmp_path.iterdir()) == []
        assert flow.get_status().phase is OperationPhase.IDLE
    finally:
        flow.close()


def test_a_new_cycle_can_start_after_confirmation(tmp_path: Path) -> None:
    ids = iter(["op-1", "op-2"])
    flow = _flow(
        EnvelopeClient(_success(), _success()),
        operation_id_factory=lambda: next(ids),
    )
    try:
        _finish(flow, _wav(tmp_path / "first.wav"))
        assert flow.query_port.get_current() is not None
        assert flow.query_port.get_current().operation_id == "op-1"  # type: ignore[union-attr]
        flow.resolution_port.confirm("op-1")

        _finish(flow, _wav(tmp_path / "second.wav"))

        current = flow.query_port.get_current()
        assert current is not None
        assert current.operation_id == "op-2"
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION
    finally:
        flow.close()


def test_status_can_be_read_while_the_pc_request_is_in_flight(
    tmp_path: Path,
) -> None:
    client = EnvelopeClient(_success())
    client.block = True
    flow = _flow(client)
    queried = threading.Event()

    def read_status() -> None:
        status = flow.get_status()
        assert status.phase is OperationPhase.PROCESSING
        assert status.headline == "Procesando solicitud..."
        assert status.pending_operation is None
        queried.set()

    try:
        assert flow.try_begin_recording() is True
        flow.on_capture_completed(_wav(tmp_path / "take.wav"))
        assert client.started.wait(2)
        reader = threading.Thread(target=read_status)
        reader.start()
        assert queried.wait(0.5)
        client.release.set()
        reader.join(2)
        assert not reader.is_alive()
        flow.wait_until_settled()
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION
    finally:
        client.release.set()
        flow.close()


def test_only_one_begin_wins_under_concurrent_presses() -> None:
    flow = _flow(EnvelopeClient())
    results: list[bool] = []
    results_lock = threading.Lock()

    def begin() -> None:
        won = flow.try_begin_recording()
        with results_lock:
            results.append(won)

    try:
        threads = [threading.Thread(target=begin) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(2)
        assert results.count(True) == 1
        assert flow.get_status().phase is OperationPhase.RECORDING
    finally:
        flow.close()


class _IdleTimer:
    def start(self, delay_seconds: float, callback: object) -> None:
        del delay_seconds, callback

    def cancel(self) -> None:
        return None


class _OneTake:
    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self.takes = 0

    def start(self) -> None:
        return None

    def stop(self) -> AudioArtifact:
        self.takes += 1
        path = self._directory / f"take-{self.takes}.wav"
        _wav(path)
        return AudioArtifact(path.stem, path)


def test_push_to_talk_ignores_a_press_while_an_operation_is_pending(
    tmp_path: Path,
) -> None:
    client = EnvelopeClient(_success(), _success())
    flow = _flow(client)
    capture = _OneTake(tmp_path)
    controller = PushToTalkController(
        capture,  # type: ignore[arg-type]
        on_capture_completed=flow.on_capture_completed,
        on_capture_error=flow.on_capture_error,
        timer=_IdleTimer(),  # type: ignore[arg-type]
        can_start_capture=flow.try_begin_recording,
    )
    controller.start()
    try:
        controller.notify_pressed()
        controller.notify_released()
        controller.wait_until_caught_up()
        flow.wait_until_settled()
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION

        controller.notify_pressed()
        controller.notify_released()
        controller.wait_until_caught_up()
        flow.wait_until_settled()

        assert capture.takes == 1
        assert client.calls == 1
        assert flow.query_port.get_current() is not None
    finally:
        controller.close()
        flow.close()
