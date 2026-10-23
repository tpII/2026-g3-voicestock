"""The integrated Raspberry Pi process shares one flow with the web app."""

import wave
from pathlib import Path

import pytest
from fastapi import FastAPI

from pi.audio.artifact import AudioArtifact
from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    load_catalog,
)
from pi.pending_operation import OperationPhase, ResolutionStatus
from pi.runtime import build_runtime, main
from pi.web.settings import WebServerSettings
from shared.communication import TransportEnvelope

CATALOG = (
    Path(__file__).parents[1]
    / "fixtures"
    / "operation_contract"
    / "october_catalog.json"
)


class FakeButton:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeClient:
    def __init__(self, envelope: TransportEnvelope) -> None:
        self.envelope = envelope
        self.closed = False
        self.calls = 0

    def interpret_audio(self, wav_path: Path) -> TransportEnvelope:
        self.calls += 1
        wav_path.read_bytes()
        return self.envelope

    def close(self) -> None:
        self.closed = True


class OneTake:
    def __init__(self, path: Path) -> None:
        self._path = path
        self.starts = 0

    def start(self) -> None:
        self.starts += 1

    def stop(self) -> AudioArtifact:
        with wave.open(str(self._path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16_000)
            wav_file.writeframes(b"\x00\x00" * 1600)
        return AudioArtifact(self._path.stem, self._path)


def _envelope() -> TransportEnvelope:
    return TransportEnvelope.success(
        {
            "status": "success",
            "payload": {
                "contract_version": "1",
                "recognized_text": "sumá dos",
                "operations": [
                    {
                        "operation": "add_stock",
                        "product": {"name": "Coca Cola Zero 2L"},
                        "quantity": 2,
                        "unit": "unit",
                    }
                ],
            },
            "error": None,
        }
    )


def test_main_requires_the_device_arguments() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2


def test_one_process_confirms_through_the_shared_flow(tmp_path: Path) -> None:
    client = FakeClient(_envelope())
    button = FakeButton()
    runtime = build_runtime(
        client=client,  # type: ignore[arg-type]
        validator=OperationValidator(InMemoryProductResolver(load_catalog(CATALOG))),
        capture=OneTake(tmp_path / "take.wav"),  # type: ignore[arg-type]
        button_factory=lambda controller: button,
        web_settings=WebServerSettings(host="127.0.0.1", port=8123),
        delete_after_send=True,
    )
    seen: dict[str, object] = {}

    def runner(application: FastAPI, host: str, port: int) -> None:
        seen["host"] = host
        seen["port"] = port
        seen["same_flow"] = application.state.status_port is runtime.flow
        seen["same_gateway"] = (
            application.state.query_port is application.state.resolution_port
        )
        runtime.controller.notify_pressed()
        runtime.controller.notify_released()
        runtime.controller.wait_until_caught_up()
        runtime.flow.wait_until_settled()
        status = application.state.status_port.get_status()
        seen["phase"] = status.phase
        operation_id = status.pending_operation.operation_id
        seen["confirm"] = application.state.resolution_port.confirm(operation_id).status
        seen["after"] = application.state.status_port.get_status().phase

    runtime.serve(runner=runner)

    assert seen == {
        "host": "127.0.0.1",
        "port": 8123,
        "same_flow": True,
        "same_gateway": True,
        "phase": OperationPhase.WAIT_CONFIRMATION,
        "confirm": ResolutionStatus.SUCCESS,
        "after": OperationPhase.IDLE,
    }
    assert client.calls == 1
    assert client.closed is True
    assert button.closed is True
