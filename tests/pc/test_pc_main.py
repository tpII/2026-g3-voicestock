"""Component tests for the PC server -> InterpretationService -> provider path."""

from typing import Any

import httpx
import pytest

from pc.interpretation import (
    ProviderError,
    ProviderRegistry,
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
