"""Tests for the Raspberry Pi client against a mocked HTTP transport."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from pi.communication import (
    ClientErrorCode,
    ClientSettings,
    HttpInterpretationClient,
    InterpretationClient,
)
from shared.communication import TransportEnvelope

Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> HttpInterpretationClient:
    return HttpInterpretationClient(
        ClientSettings(base_url="http://pc.test:8000", timeout_seconds=1.5),
        transport=httpx.MockTransport(handler),
    )


def _envelope(payload: Any) -> dict[str, Any]:
    return {"status": "success", "payload": payload, "error": None}


def test_happy_path_returns_the_success_envelope() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_envelope({"recognized_text": "arroz"}))

    with _client(handler) as client:
        envelope = client.interpret("arroz")

    assert envelope == TransportEnvelope.success({"recognized_text": "arroz"})
    assert [(r.method, str(r.url)) for r in requests] == [
        ("POST", "http://pc.test:8000/api/v1/interpret")
    ]


def test_spanish_text_is_sent_as_utf8_json() -> None:
    text = "agregá dos paquetes de ñoquis"
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json=_envelope(None))

    with _client(handler) as client:
        client.interpret(text)

    request = sent[0]
    assert request.headers["content-type"] == "application/json; charset=utf-8"
    assert request.content == '{"text": "agregá dos paquetes de ñoquis"}'.encode()
    assert json.loads(request.content.decode("utf-8")) == {"text": text}


def test_payload_is_returned_intact_even_if_its_domain_content_is_odd() -> None:
    payload = {"status": "error", "whatever": [1, "dos", None], "nested": {}}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_envelope(payload))

    with _client(handler) as client:
        envelope = client.interpret("arroz")

    assert envelope.status == "success"
    assert envelope.payload == payload


@pytest.mark.parametrize("text", ["", "   ", "x" * 10_000])
def test_any_string_is_sent_without_client_side_validation(text: str) -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json=_envelope(None))

    with _client(handler) as client:
        client.interpret(text)

    assert json.loads(sent[0].content) == {"text": text}


def test_server_error_envelope_is_passed_through() -> None:
    server_envelope = {
        "status": "error",
        "payload": None,
        "error": {"code": "invalid_request", "detail": "request body is not valid"},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json=server_envelope)

    with _client(handler) as client:
        envelope = client.interpret(" ")

    assert envelope == TransportEnvelope.model_validate(server_envelope)


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectTimeout("connect timed out"),
        httpx.ReadTimeout("read timed out"),
        httpx.WriteTimeout("write timed out"),
        httpx.PoolTimeout("pool timed out"),
    ],
)
def test_timeouts_are_reported_as_timeout(error: httpx.TimeoutException) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    with _client(handler) as client:
        envelope = client.interpret("arroz")

    assert envelope.status == "error"
    assert envelope.error is not None
    assert envelope.error.code == ClientErrorCode.TIMEOUT
    assert envelope.error.detail == "no response within 1.5 seconds"


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("connection refused"),
        httpx.ReadError("connection reset"),
        httpx.RemoteProtocolError("server disconnected"),
    ],
)
def test_connection_problems_are_reported_as_connection_failed(
    error: httpx.TransportError,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    with _client(handler) as client:
        envelope = client.interpret("arroz")

    assert envelope.error is not None
    assert envelope.error.code == ClientErrorCode.CONNECTION_FAILED


@pytest.mark.parametrize(
    ("response", "expected_code"),
    [
        (httpx.Response(200, content=b"\xff\xfe"), "invalid_response_encoding"),
        (httpx.Response(200, content=b"not json"), "invalid_response_encoding"),
        (httpx.Response(200, json={"text": "arroz"}), "invalid_envelope"),
        (
            httpx.Response(200, json={"status": "error", "payload": 1, "error": None}),
            "invalid_envelope",
        ),
        (httpx.Response(404, text="<h1>Not Found</h1>"), "unexpected_status"),
        (httpx.Response(502, json={"detail": "bad gateway"}), "unexpected_status"),
        (
            httpx.Response(
                200,
                json={"status": "error", "payload": None, "error": {"code": "x"}},
            ),
            "unexpected_status",
        ),
        (httpx.Response(500, json=_envelope(None)), "unexpected_status"),
    ],
)
def test_malformed_responses_are_distinguishable(
    response: httpx.Response, expected_code: str
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    with _client(handler) as client:
        envelope = client.interpret("arroz")

    assert envelope.status == "error"
    assert envelope.payload is None
    assert envelope.error is not None
    assert envelope.error.code == expected_code


def test_text_that_cannot_be_utf8_is_rejected_before_sending() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("nothing must be sent")

    with _client(handler) as client:
        envelope = client.interpret("arroz \ud800")

    assert envelope.error is not None
    assert envelope.error.code == ClientErrorCode.REQUEST_ENCODING_FAILURE


def test_failures_are_not_retried() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("connection refused")

    with _client(handler) as client:
        client.interpret("arroz")

    assert calls == 1


def test_client_error_codes_do_not_collide_with_server_codes() -> None:
    server_codes = {
        "invalid_json",
        "unsupported_media_type",
        "invalid_request",
        "handler_failure",
        "serialization_failure",
    }

    assert server_codes.isdisjoint(set(ClientErrorCode))


def test_http_client_satisfies_the_protocol() -> None:
    client: InterpretationClient = _client(lambda request: httpx.Response(200))

    assert callable(client.interpret)
