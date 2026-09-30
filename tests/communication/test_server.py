"""Component tests for the PC communication HTTP server."""

from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest

from voicestock.communication.server import create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def handler() -> Callable[[str], Any]:
    return lambda text: {"echo": text, "provider": "stub"}


@pytest.fixture
async def client(handler: Callable[[str], Any]) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app(handler), raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client


async def test_interpret_returns_opaque_handler_payload(
    client: httpx.AsyncClient,
    handler: Callable[[str], Any],
) -> None:
    del handler

    response = await client.post(
        "/api/v1/interpret",
        json={"text": "quitá una botella de aceite"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "payload": {
            "echo": "quitá una botella de aceite",
            "provider": "stub",
        },
        "error": None,
    }


@pytest.mark.parametrize(
    ("body", "expected_code"),
    [
        ({}, "invalid_request"),
        ({"text": 42}, "invalid_request"),
        ({"text": "   "}, "invalid_request"),
        ({"text": "válido", "extra": True}, "invalid_request"),
    ],
)
async def test_interpret_rejects_invalid_request_shape(
    client: httpx.AsyncClient,
    body: dict[str, Any],
    expected_code: str,
) -> None:
    response = await client.post("/api/v1/interpret", json=body)

    assert response.status_code == 422
    assert response.json()["status"] == "error"
    assert response.json()["error"]["code"] == expected_code


async def test_interpret_rejects_malformed_json(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/interpret",
        content=b'{"text":',
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_json"


async def test_interpret_rejects_unsupported_media_type(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/interpret",
        content="agregá arroz",
        headers={"content-type": "text/plain; charset=utf-8"},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


async def test_interpret_converts_handler_exception_to_transport_error() -> None:
    def failing_handler(text: str) -> Any:
        del text
        raise RuntimeError("provider details must not escape")

    transport = httpx.ASGITransport(
        app=create_app(failing_handler),
        raise_app_exceptions=False,
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/interpret",
            json={"text": "agregá arroz"},
        )

    assert response.status_code == 500
    assert response.json()["error"] == {
        "code": "handler_failure",
        "detail": "the interpretation handler failed",
    }


async def test_interpret_rejects_non_serializable_handler_result() -> None:
    transport = httpx.ASGITransport(
        app=create_app(lambda text: {"text": text, "value": object()}),
        raise_app_exceptions=False,
    )
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/api/v1/interpret",
            json={"text": "agregá arroz"},
        )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "serialization_failure"
