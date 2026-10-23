"""Tests for sending WAV audio from the Raspberry Pi client, with a mocked PC."""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from pi.communication import (
    AudioInterpretationClient,
    ClientErrorCode,
    ClientSettings,
    HttpInterpretationClient,
)
from shared.communication import TransportEnvelope

Handler = Callable[[httpx.Request], httpx.Response]

WAV_BYTES = b"RIFF\x24\x00\x00\x00WAVEfmt any bytes the server will judge"


def _client(handler: Handler) -> HttpInterpretationClient:
    return HttpInterpretationClient(
        ClientSettings(base_url="http://pc.test:8000", timeout_seconds=1.5),
        transport=httpx.MockTransport(handler),
    )


@pytest.fixture
def wav_path(tmp_path: Path) -> Path:
    path = tmp_path / "recording.wav"
    path.write_bytes(WAV_BYTES)
    return path


def test_the_file_is_sent_unchanged_as_a_wav_body(wav_path: Path) -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(
            200, json={"status": "success", "payload": {"ok": 1}, "error": None}
        )

    with _client(handler) as client:
        envelope = client.interpret_audio(wav_path)

    assert envelope == TransportEnvelope.success({"ok": 1})
    [request] = sent
    assert (request.method, str(request.url)) == (
        "POST",
        "http://pc.test:8000/api/v1/interpret-audio",
    )
    assert request.headers["content-type"] == "audio/wav"
    assert request.content == WAV_BYTES


def test_server_error_envelope_is_passed_through(wav_path: Path) -> None:
    server_envelope = {
        "status": "error",
        "payload": None,
        "error": {"code": "invalid_audio", "detail": "not a WAV"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json=server_envelope)

    with _client(handler) as client:
        envelope = client.interpret_audio(wav_path)

    assert envelope == TransportEnvelope.model_validate(server_envelope)


@pytest.mark.parametrize("name", ["missing.wav", "."], ids=["missing", "directory"])
def test_unreadable_file_is_a_local_error_and_nothing_is_sent(
    tmp_path: Path, name: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("nothing must be sent")

    with _client(handler) as client:
        envelope = client.interpret_audio(tmp_path / name)

    assert envelope.status == "error"
    assert envelope.error is not None
    assert envelope.error.code == ClientErrorCode.AUDIO_READ_FAILURE


@pytest.mark.parametrize(
    ("error", "expected_code"),
    [
        (httpx.WriteTimeout("upload timed out"), ClientErrorCode.TIMEOUT),
        (httpx.ReadTimeout("no answer"), ClientErrorCode.TIMEOUT),
        (httpx.ConnectError("refused"), ClientErrorCode.CONNECTION_FAILED),
        (httpx.WriteError("broken pipe"), ClientErrorCode.CONNECTION_FAILED),
    ],
)
def test_transport_failures_use_the_text_client_codes(
    wav_path: Path, error: httpx.TransportError, expected_code: ClientErrorCode
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise error

    with _client(handler) as client:
        envelope = client.interpret_audio(wav_path)

    assert envelope.error is not None
    assert envelope.error.code == expected_code
    assert calls == 1


@pytest.mark.parametrize(
    ("response", "expected_code"),
    [
        (httpx.Response(200, content=b"not json"), "invalid_response_encoding"),
        (httpx.Response(200, json={"seconds": 2}), "invalid_envelope"),
        (httpx.Response(404, text="Not Found"), "unexpected_status"),
    ],
)
def test_malformed_responses_are_distinguishable(
    wav_path: Path, response: httpx.Response, expected_code: str
) -> None:
    with _client(lambda request: response) as client:
        envelope = client.interpret_audio(wav_path)

    assert envelope.error is not None
    assert envelope.error.code == expected_code


def test_audio_read_failure_does_not_collide_with_server_codes() -> None:
    server_codes = {
        "unsupported_media_type",
        "audio_too_large",
        "empty_audio",
        "invalid_audio",
        "handler_failure",
        "serialization_failure",
    }

    assert server_codes.isdisjoint(set(ClientErrorCode))


def test_http_client_satisfies_the_audio_protocol() -> None:
    client: AudioInterpretationClient = _client(lambda request: httpx.Response(200))

    assert callable(client.interpret_audio)
