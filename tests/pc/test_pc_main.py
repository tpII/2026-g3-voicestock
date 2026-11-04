"""Component tests for the PC entry point: text and audio handlers wired to HTTP."""

import io
import wave
from pathlib import Path
from typing import Any

import httpx
import pytest

from pc.communication import ReceivedAudio
from pc.interpretation import (
    ProviderError,
    ProviderRegistry,
    ServiceResult,
    StubProvider,
    default_registry,
)
from pc.main import create_pc_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


class FailingProvider:
    def interpret(self, text: str) -> Any:
        raise ProviderError("model timed out")


async def _post(
    registry: ProviderRegistry, provider_name: str | None, body: Any
) -> httpx.Response:
    transport = httpx.ASGITransport(
        app=create_pc_app(registry, provider_name), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.post("/api/v1/interpret", json=body)


@pytest.fixture
def registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("stub", StubProvider)
    registry.register("failing", FailingProvider)
    return registry


async def test_stub_success_travels_inside_the_envelope() -> None:
    response = await _post(
        default_registry(), "stub", {"text": "agregá dos paquetes de arroz"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "payload": {
            "status": "success",
            "payload": {"recognized_text": "agregá dos paquetes de arroz"},
            "error": None,
        },
        "error": None,
    }


@pytest.mark.parametrize(
    ("provider_name", "expected_code"),
    [
        (None, "provider_not_configured"),
        ("gpt", "provider_not_configured"),
        ("failing", "provider_failure"),
    ],
)
async def test_service_errors_are_transported_successfully(
    registry: ProviderRegistry, provider_name: str | None, expected_code: str
) -> None:
    response = await _post(registry, provider_name, {"text": "arroz"})

    assert response.status_code == 200
    envelope = response.json()
    assert envelope["status"] == "success"
    assert envelope["error"] is None
    assert envelope["payload"]["status"] == "error"
    assert envelope["payload"]["payload"] is None
    assert envelope["payload"]["error"]["code"] == expected_code


async def test_transport_errors_stay_outside_the_service(
    registry: ProviderRegistry,
) -> None:
    response = await _post(registry, "stub", {"text": "   "})

    assert response.status_code == 422
    assert response.json()["status"] == "error"
    assert response.json()["payload"] is None
    assert response.json()["error"]["code"] == "invalid_request"


async def test_stub_audio_handler_answers_inside_a_service_result() -> None:
    wav_path = (
        Path(__file__).parents[1]
        / "fixtures"
        / "speech_to_text"
        / "wav"
        / "basico"
        / "solo_agregar.wav"
    )
    content = wav_path.read_bytes()
    transport = httpx.ASGITransport(
        app=create_pc_app(default_registry(), "stub"), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/v1/interpret-audio",
            content=content,
            headers={"content-type": "audio/wav"},
        )

    assert response.status_code == 200
    service_result = response.json()["payload"]
    assert service_result["status"] == "success"
    received = service_result["payload"]["received_audio"]
    assert received["size_bytes"] == len(content)
    assert received["sample_rate_hz"] == 16_000
    assert received["channels"] == 1
    assert received["duration_seconds"] > 0


async def test_audio_handler_is_replaceable_at_composition() -> None:
    def transcribe_and_interpret(audio: ReceivedAudio) -> ServiceResult:
        return ServiceResult.success({"transcribed_bytes": len(audio.wav)})

    transport = httpx.ASGITransport(
        app=create_pc_app(
            default_registry(), "stub", audio_handler=transcribe_and_interpret
        ),
        raise_app_exceptions=False,
    )
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/api/v1/interpret-audio",
            content=_wav_bytes(),
            headers={"content-type": "audio/wav"},
        )

    assert response.json()["payload"]["payload"] == {
        "transcribed_bytes": len(_wav_bytes())
    }


def _wav_bytes() -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00\x00" * 1_600)
    return buffer.getvalue()
