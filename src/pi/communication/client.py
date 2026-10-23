"""Raspberry Pi client that sends recognized text or recorded audio to the PC.

Callers depend on InterpretationClient or AudioInterpretationClient, not on
HTTP: every outcome is a TransportEnvelope. Failures detected locally (no
reachable server, timeout, unreadable response or audio file) use
ClientErrorCode; failures reported by the server keep the server's own error
codes. The payload is returned untouched.
"""

import json
from enum import StrEnum
from pathlib import Path
from types import TracebackType
from typing import Protocol, Self

import httpx

from pi.communication.settings import ClientSettings
from shared.communication.contracts import WAV_MEDIA_TYPE, TransportEnvelope

INTERPRET_PATH = "/api/v1/interpret"
INTERPRET_AUDIO_PATH = "/api/v1/interpret-audio"


class ClientErrorCode(StrEnum):
    """Transport failures detected by the client, distinct from server codes."""

    REQUEST_ENCODING_FAILURE = "request_encoding_failure"
    AUDIO_READ_FAILURE = "audio_read_failure"
    TIMEOUT = "timeout"
    CONNECTION_FAILED = "connection_failed"
    UNEXPECTED_STATUS = "unexpected_status"
    INVALID_RESPONSE_ENCODING = "invalid_response_encoding"
    INVALID_ENVELOPE = "invalid_envelope"


class InterpretationClient(Protocol):
    """Stable client contract: send text, get a transported result or error."""

    def interpret(self, text: str) -> TransportEnvelope: ...


class AudioInterpretationClient(Protocol):
    """Stable client contract: send a WAV file, get a transported result or error."""

    def interpret_audio(self, wav_path: Path) -> TransportEnvelope: ...


class HttpInterpretationClient:
    """Both client contracts over HTTP: text as JSON, audio as a WAV body.

    It never retries and never raises for communication failures: each call
    makes at most one request, bounded by the configured timeout.
    """

    def __init__(
        self,
        settings: ClientSettings,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout_seconds = settings.timeout_seconds
        self._http = httpx.Client(
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            transport=transport,
        )

    def interpret(self, text: str) -> TransportEnvelope:
        """Send recognized text to the PC and return the transport envelope."""
        try:
            body = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError):
            return TransportEnvelope.failure(
                ClientErrorCode.REQUEST_ENCODING_FAILURE,
                "text cannot be encoded as UTF-8 JSON",
            )

        return self._post(INTERPRET_PATH, body, "application/json; charset=utf-8")

    def interpret_audio(self, wav_path: Path) -> TransportEnvelope:
        """Send a recorded WAV file to the PC and return the transport envelope.

        The file is sent as it is: the server decides whether it is acceptable.
        """
        try:
            body = Path(wav_path).read_bytes()
        except OSError:
            return TransportEnvelope.failure(
                ClientErrorCode.AUDIO_READ_FAILURE,
                "audio file cannot be read",
            )

        return self._post(INTERPRET_AUDIO_PATH, body, WAV_MEDIA_TYPE)

    def _post(self, path: str, body: bytes, content_type: str) -> TransportEnvelope:
        try:
            response = self._http.post(
                path,
                content=body,
                headers={"Content-Type": content_type},
            )
        except httpx.TimeoutException:
            return TransportEnvelope.failure(
                ClientErrorCode.TIMEOUT,
                f"no response within {self._timeout_seconds} seconds",
            )
        except httpx.TransportError:
            return TransportEnvelope.failure(
                ClientErrorCode.CONNECTION_FAILED,
                "could not communicate with the PC server",
            )

        return _read_envelope(response)

    def close(self) -> None:
        """Release the underlying connections."""
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


def _read_envelope(response: httpx.Response) -> TransportEnvelope:
    try:
        body = json.loads(response.content.decode("utf-8"))
    except ValueError:
        return _failure_for(
            response,
            ClientErrorCode.INVALID_RESPONSE_ENCODING,
            "response body is not UTF-8 JSON",
        )

    try:
        envelope = TransportEnvelope.model_validate(body)
    except ValueError:
        return _failure_for(
            response,
            ClientErrorCode.INVALID_ENVELOPE,
            "response body is not a transport envelope",
        )

    if (envelope.status == "success") != (response.status_code == 200):
        return _unexpected_status(response)
    return envelope


def _failure_for(
    response: httpx.Response, code: ClientErrorCode, detail: str
) -> TransportEnvelope:
    # A non-200 response without a server envelope (e.g. a 404 page from a wrong
    # URL) is reported as a status problem, not as a body problem.
    if response.status_code != 200:
        return _unexpected_status(response)
    return TransportEnvelope.failure(code, detail)


def _unexpected_status(response: httpx.Response) -> TransportEnvelope:
    return TransportEnvelope.failure(
        ClientErrorCode.UNEXPECTED_STATUS,
        f"unexpected HTTP status {response.status_code}",
    )
