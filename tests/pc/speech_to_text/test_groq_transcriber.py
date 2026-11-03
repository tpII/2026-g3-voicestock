"""Groq Whisper adapter tests. No live API call is made."""

import httpx
import pytest

from pc.speech_to_text import (
    GroqWhisperTranscriber,
    TranscriptionError,
    TranscriptionFailure,
)

SECRET = "super-secret-groq-key"


def _client(handler: httpx.MockTransport) -> httpx.Client:
    return httpx.Client(transport=handler)


def test_transcription_returns_spanish_text() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/audio/transcriptions")
        assert request.headers["authorization"] == f"Bearer {SECRET}"
        body = request.content.decode("latin1")
        assert 'name="language"' in body
        assert "es" in body
        assert "audio.wav" in body
        return httpx.Response(200, json={"text": "  agregá dos paquetes  "})

    transcriber = GroqWhisperTranscriber(
        api_key=SECRET, client=_client(httpx.MockTransport(handler))
    )
    assert transcriber.transcribe(b"RIFFwav") == "agregá dos paquetes"


def test_blank_transcription_is_empty() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"text": "  "})
    )
    transcriber = GroqWhisperTranscriber(api_key=SECRET, client=_client(transport))
    with pytest.raises(TranscriptionError) as caught:
        transcriber.transcribe(b"RIFFwav")
    assert caught.value.kind is TranscriptionFailure.EMPTY


def test_timeout_does_not_include_the_api_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException(SECRET)

    transcriber = GroqWhisperTranscriber(
        api_key=SECRET, client=_client(httpx.MockTransport(handler))
    )
    with pytest.raises(TranscriptionError) as caught:
        transcriber.transcribe(b"RIFFwav")
    assert caught.value.kind is TranscriptionFailure.TIMEOUT
    assert SECRET not in str(caught.value)


def test_http_failure_hides_the_response_body(caplog: pytest.LogCaptureFixture) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text=f"boom {SECRET} RIFF-audio-body")

    transcriber = GroqWhisperTranscriber(
        api_key=SECRET, client=_client(httpx.MockTransport(handler))
    )
    with caplog.at_level("INFO"), pytest.raises(TranscriptionError) as caught:
        transcriber.transcribe(b"RIFFwav")
    assert caught.value.kind is TranscriptionFailure.FAILED
    assert "HTTP 503" in str(caught.value)
    assert SECRET not in str(caught.value)
    assert SECRET not in caplog.text
    assert "RIFF-audio-body" not in caplog.text
