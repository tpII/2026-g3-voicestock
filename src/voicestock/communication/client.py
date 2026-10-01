"""Raspberry Pi client that sends recognized text to the PC server.

Callers depend on InterpretationClient, not on HTTP: every outcome is a
TransportEnvelope. Failures detected locally (no reachable server, timeout,
unreadable response) use ClientErrorCode; failures reported by the server keep
the server's own error codes. The payload is returned untouched.
"""

import json
from enum import StrEnum
from types import TracebackType
from typing import Protocol, Self

import httpx

from voicestock.communication.contracts import TransportEnvelope
from voicestock.communication.settings import ClientSettings

INTERPRET_PATH = "/api/v1/interpret"


class ClientErrorCode(StrEnum):
    """Transport failures detected by the client, distinct from server codes."""

    REQUEST_ENCODING_FAILURE = "request_encoding_failure"
    TIMEOUT = "timeout"
    CONNECTION_FAILED = "connection_failed"
    UNEXPECTED_STATUS = "unexpected_status"
    INVALID_RESPONSE_ENCODING = "invalid_response_encoding"
    INVALID_ENVELOPE = "invalid_envelope"


class InterpretationClient(Protocol):
    """Stable client contract: send text, get a transported result or error."""

    def interpret(self, text: str) -> TransportEnvelope: ...


class HttpInterpretationClient:
    """InterpretationClient that talks to the PC server over HTTP + JSON.

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

        try:
            response = self._http.post(
                INTERPRET_PATH,
                content=body,
                headers={"Content-Type": "application/json; charset=utf-8"},
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
