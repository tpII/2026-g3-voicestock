"""HTTP view of the public operation cycle."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

from pi.pending_operation import (
    OperationCycleStatus,
    OperationPhase,
    PendingOperationView,
)
from pi.web.app import create_app

pytestmark = pytest.mark.anyio


class FakeStatusPort:
    def __init__(self, status: OperationCycleStatus) -> None:
        self.status = status
        self.calls = 0

    def get_status(self) -> OperationCycleStatus:
        self.calls += 1
        return self.status


@asynccontextmanager
async def client_for(
    status_port: object | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(status_port=status_port)  # type: ignore[arg-type]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_system_status_is_not_ready_without_a_port() -> None:
    async with client_for() as client:
        response = await client.get("/api/v1/system-status")

    assert response.status_code == 503
    assert response.json() == {
        "code": "application_not_ready",
        "detail": "pending-operation application ports are not configured",
    }


async def test_system_status_returns_the_public_phase() -> None:
    view = PendingOperationView(
        operation_id="op-aaa",
        recognized_text="sumá dos",
        product="Coca Cola Zero 2L",
        operation="agregar",
        quantity=2,
        unit="unidad",
        confirmation_message="Agregar 2 unidades de Coca Cola Zero 2L",
    )
    port = FakeStatusPort(
        OperationCycleStatus(
            phase=OperationPhase.WAIT_CONFIRMATION,
            headline="Operación pendiente de confirmación",
            detail="",
            operator_message=None,
            pending_operation=view,
        )
    )
    async with client_for(status_port=port) as client:
        response = await client.get("/api/v1/system-status")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "phase": "wait_confirmation",
        "headline": "Operación pendiente de confirmación",
        "detail": "",
        "operator_message": None,
        "pending_operation": {
            "operation_id": "op-aaa",
            "recognized_text": "sumá dos",
            "product": "Coca Cola Zero 2L",
            "operation": "agregar",
            "quantity": 2,
            "unit": "unidad",
            "confirmation_message": "Agregar 2 unidades de Coca Cola Zero 2L",
        },
    }
    assert port.calls == 1
