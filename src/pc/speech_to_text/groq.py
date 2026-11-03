"""Groq Whisper adapter.

The benchmark runner is not used here. This module sends one WAV and returns
its text, or a ``TranscriptionError``. It does not interpret commands.
"""

import logging

import httpx

from pc.speech_to_text.errors import TranscriptionError, TranscriptionFailure

logger = logging.getLogger(__name__)

GROQ_TRANSCRIPTIONS_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
DEFAULT_STT_MODEL = "whisper-large-v3-turbo"


class GroqWhisperTranscriber:
    """Transcribe WAV bytes with Groq's OpenAI-compatible audio endpoint."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_STT_MODEL,
        timeout_seconds: float = 20.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Groq API key must not be blank")
        if not model.strip():
            raise ValueError("STT model must not be blank")
        if timeout_seconds <= 0:
            raise ValueError("STT timeout must be positive")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._client = client if client is not None else httpx.Client()
        self._owns_client = client is None

    def transcribe(self, wav: bytes) -> str:
        """Send ``wav`` and return non-blank Spanish text."""
        if not wav:
            raise TranscriptionError(TranscriptionFailure.FAILED, "audio body is empty")
        try:
            response = self._client.post(
                GROQ_TRANSCRIPTIONS_URL,
                data={
                    "model": self._model,
                    "language": "es",
                    "temperature": "0",
                    "response_format": "json",
                },
                files={"file": ("audio.wav", wav, "audio/wav")},
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException:
            logger.info("speech-to-text request timed out")
            raise TranscriptionError(
                TranscriptionFailure.TIMEOUT,
                "speech-to-text request timed out",
            ) from None
        except httpx.HTTPError as error:
            logger.info("speech-to-text request failed")
            raise TranscriptionError(
                TranscriptionFailure.FAILED,
                _http_detail(error),
            ) from None

        text = _read_text(response)
        if not text.strip():
            raise TranscriptionError(
                TranscriptionFailure.EMPTY, "transcription is blank"
            )
        return text.strip()

    def close(self) -> None:
        """Close the client this adapter created."""
        if self._owns_client:
            self._client.close()


def _read_text(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        raise TranscriptionError(
            TranscriptionFailure.FAILED,
            "speech-to-text response is not JSON",
        ) from None
    if not isinstance(body, dict):
        raise TranscriptionError(
            TranscriptionFailure.FAILED,
            "speech-to-text response is not an object",
        )
    text = body.get("text")
    if not isinstance(text, str):
        raise TranscriptionError(
            TranscriptionFailure.FAILED,
            "speech-to-text response has no text",
        )
    return text


def _http_detail(error: httpx.HTTPError) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        return f"speech-to-text request failed with HTTP {error.response.status_code}"
    return "speech-to-text request failed"
