"""Component tests for the PC server's audio endpoint."""

import io
import wave
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest

from pc.communication import AudioHandler, ReceivedAudio, create_app
from shared.communication import MAX_AUDIO_BYTES, WAV_MEDIA_TYPE

pytestmark = pytest.mark.anyio

AUDIO_PATH = "/api/v1/interpret-audio"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _wav(seconds: float = 1.0) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x00\x00" * int(seconds * 16_000))
    return buffer.getvalue()


class RecordingHandler:
    def __init__(self) -> None:
        self.received: list[ReceivedAudio] = []

    def __call__(self, audio: ReceivedAudio) -> Any:
        self.received.append(audio)
        return {"seconds": audio.duration_seconds}


async def _post(
    audio_handler: AudioHandler | None,
    content: Any,
    content_type: str | None = WAV_MEDIA_TYPE,
) -> httpx.Response:
    app = create_app(lambda text: {"text": text}, audio_handler=audio_handler)
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    headers = {} if content_type is None else {"content-type": content_type}
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.post(AUDIO_PATH, content=content, headers=headers)


async def test_wav_reaches_the_handler_intact_and_its_result_is_opaque() -> None:
    handler = RecordingHandler()
    content = _wav(2.0)

    response = await _post(handler, content)

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "payload": {"seconds": 2.0},
        "error": None,
    }
    [audio] = handler.received
    assert audio.wav == content
    assert (audio.sample_rate_hz, audio.channels, audio.sample_width_bytes) == (
        16_000,
        1,
        2,
    )


async def test_media_type_parameters_are_ignored() -> None:
    response = await _post(RecordingHandler(), _wav(), "Audio/WAV; codecs=1")

    assert response.status_code == 200


@pytest.mark.parametrize(
    "content_type", ["application/json", "audio/mpeg", "application/octet-stream", None]
)
async def test_other_media_types_are_rejected(content_type: str | None) -> None:
    handler = RecordingHandler()

    response = await _post(handler, _wav(), content_type)

    assert response.status_code == 415
    assert response.json()["error"] == {
        "code": "unsupported_media_type",
        "detail": "Content-Type must be audio/wav",
    }
    assert handler.received == []


@pytest.mark.parametrize(
    ("content", "status_code", "code"),
    [
        (b"", 422, "empty_audio"),
        (b"agrega dos paquetes de arroz", 422, "invalid_audio"),
        (_wav()[:30], 422, "invalid_audio"),
        (b"\x00" * (MAX_AUDIO_BYTES + 1), 413, "audio_too_large"),
    ],
    ids=["empty", "not_wav", "truncated_header", "too_large"],
)
async def test_invalid_bodies_are_distinguishable_and_skip_the_handler(
    content: bytes, status_code: int, code: str
) -> None:
    handler = RecordingHandler()

    response = await _post(handler, content)

    assert response.status_code == status_code
    assert response.json()["status"] == "error"
    assert response.json()["payload"] is None
    assert response.json()["error"]["code"] == code
    assert handler.received == []


async def test_a_body_at_the_limit_is_accepted() -> None:
    header = _wav(0.0)
    content = header + b"\x00" * (MAX_AUDIO_BYTES - len(header))

    response = await _post(RecordingHandler(), content)

    assert response.status_code == 200


async def test_an_oversized_body_without_content_length_is_cut_off() -> None:
    chunks_read = 0

    async def chunks() -> AsyncIterator[bytes]:
        nonlocal chunks_read
        for _ in range(MAX_AUDIO_BYTES // 65_536 + 50):
            chunks_read += 1
            yield b"\x00" * 65_536

    response = await _post(RecordingHandler(), chunks())

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "audio_too_large"
    assert chunks_read < MAX_AUDIO_BYTES // 65_536 + 50


async def test_handler_exception_becomes_a_transport_error() -> None:
    def failing_handler(audio: ReceivedAudio) -> Any:
        raise RuntimeError("transcription API details must not escape")

    response = await _post(failing_handler, _wav())

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "handler_failure",
        "detail": "the interpretation handler failed",
    }


async def test_non_serializable_handler_result_is_rejected() -> None:
    response = await _post(lambda audio: {"value": object()}, _wav())

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "serialization_failure"


async def test_endpoint_is_absent_without_an_audio_handler() -> None:
    response = await _post(None, _wav())

    assert response.status_code == 404
