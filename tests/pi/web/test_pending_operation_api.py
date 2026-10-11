"""HTTP mapping for the pending-operation API. Ports are fakes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
import pytest

from pi.pending_operation import (
    PendingOperationView,
    ResolutionResult,
    ResolutionStatus,
    ResolvedAction,
)
from pi.web.app import create_app

pytestmark = pytest.mark.anyio


class FakeQueryPort:
    """Returns one scripted snapshot and records that it was read."""

    def __init__(self, current: PendingOperationView | None) -> None:
        self.current = current
        self.calls = 0

    def get_current(self) -> PendingOperationView | None:
        self.calls += 1
        return self.current


class FakeResolutionPort:
    """Returns one scripted result and records the id it received."""

    def __init__(
        self,
        result: ResolutionResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result
        self.error = error
        self.confirmed: list[str] = []
        self.cancelled: list[str] = []

    def confirm(self, operation_id: str) -> ResolutionResult:
        self.confirmed.append(operation_id)
        return self._finish()

    def cancel(self, operation_id: str) -> ResolutionResult:
        self.cancelled.append(operation_id)
        return self._finish()

    def _finish(self) -> ResolutionResult:
        if self.error is not None:
            raise self.error
        if self.result is None:
            raise AssertionError("fake resolution has no result")
        return self.result


VIEW_FIELDS = {
    "operation_id",
    "recognized_text",
    "product",
    "operation",
    "quantity",
    "unit",
    "confirmation_message",
}


def _result(
    status: ResolutionStatus,
    action: ResolvedAction | None = None,
) -> ResolutionResult:
    if status is ResolutionStatus.NO_PENDING:
        return ResolutionResult(status=status)
    return ResolutionResult(
        status=status,
        operation_id="op-aaa",
        resolved_action=action,
    )


@asynccontextmanager
async def client_for(
    query_port: object | None = None,
    resolution_port: object | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(query_port=query_port, resolution_port=resolution_port)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_get_returns_only_the_public_view_fields() -> None:
    @dataclass(frozen=True)
    class LeakyView(PendingOperationView):
        secret: str = "inventory-row"

    leaked = LeakyView(
        operation_id="op-aaa",
        recognized_text="agregar diez unidades de coca cola",
        product="Coca-Cola",
        operation="agregar",
        quantity=10,
        unit="unidad",
        confirmation_message="Agregar 10 unidades de Coca-Cola",
    )
    async with client_for(query_port=FakeQueryPort(leaked)) as client:
        response = await client.get("/api/v1/pending-operation")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert set(body) == VIEW_FIELDS
    assert body["quantity"] == 10
    assert isinstance(body["quantity"], int)
    assert body["confirmation_message"] == "Agregar 10 unidades de Coca-Cola"
    assert "secret" not in body


async def test_get_returns_no_content_when_nothing_is_pending() -> None:
    query = FakeQueryPort(None)
    async with client_for(query_port=query) as client:
        response = await client.get("/api/v1/pending-operation")

    assert response.status_code == 204
    assert response.content == b""
    assert response.headers["cache-control"] == "no-store"
    assert query.calls == 1


async def test_get_reports_application_not_ready_without_a_query_port() -> None:
    async with client_for() as client:
        response = await client.get("/api/v1/pending-operation")

    assert response.status_code == 503
    assert response.json() == {
        "code": "application_not_ready",
        "detail": "pending-operation application ports are not configured",
    }


@pytest.mark.parametrize(
    ("status", "action", "http_status"),
    [
        (ResolutionStatus.SUCCESS, ResolvedAction.CONFIRM, 200),
        (ResolutionStatus.ALREADY_RESOLVED, ResolvedAction.CONFIRM, 200),
        (ResolutionStatus.NO_PENDING, None, 404),
        (ResolutionStatus.STALE_OPERATION, None, 409),
        (ResolutionStatus.CONFLICT, ResolvedAction.CANCEL, 409),
        (ResolutionStatus.EXECUTION_FAILED, None, 503),
    ],
)
async def test_confirm_maps_application_results(
    status: ResolutionStatus,
    action: ResolvedAction | None,
    http_status: int,
) -> None:
    port = FakeResolutionPort(_result(status, action))
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/op-aaa/confirm")

    assert response.status_code == http_status
    assert port.confirmed == ["op-aaa"]
    assert port.cancelled == []
    assert response.json() == {
        "status": status.value,
        "operation_id": None if status is ResolutionStatus.NO_PENDING else "op-aaa",
        "resolved_action": None if action is None else action.value,
    }


@pytest.mark.parametrize(
    ("status", "action", "http_status"),
    [
        (ResolutionStatus.SUCCESS, ResolvedAction.CANCEL, 200),
        (ResolutionStatus.ALREADY_RESOLVED, ResolvedAction.CANCEL, 200),
        (ResolutionStatus.NO_PENDING, None, 404),
        (ResolutionStatus.STALE_OPERATION, None, 409),
        (ResolutionStatus.CONFLICT, ResolvedAction.CONFIRM, 409),
    ],
)
async def test_cancel_maps_application_results(
    status: ResolutionStatus,
    action: ResolvedAction | None,
    http_status: int,
) -> None:
    port = FakeResolutionPort(_result(status, action))
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/op-aaa/cancel")

    assert response.status_code == http_status
    assert port.cancelled == ["op-aaa"]
    assert port.confirmed == []
    expected_action = None if action is None else action.value
    assert response.json()["status"] == status.value
    assert response.json()["resolved_action"] == expected_action


async def test_cancel_uses_the_shared_map_if_execution_failed_is_returned() -> None:
    port = FakeResolutionPort(_result(ResolutionStatus.EXECUTION_FAILED))
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/op-aaa/cancel")

    assert response.status_code == 503
    assert response.json() == {
        "status": "execution_failed",
        "operation_id": "op-aaa",
        "resolved_action": None,
    }


async def test_conflict_keeps_the_winning_action() -> None:
    port = FakeResolutionPort(
        ResolutionResult(
            status=ResolutionStatus.CONFLICT,
            operation_id="op-aaa",
            resolved_action=ResolvedAction.CONFIRM,
        )
    )
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/op-aaa/cancel")

    assert response.status_code == 409
    assert response.json() == {
        "status": "conflict",
        "operation_id": "op-aaa",
        "resolved_action": "confirm",
    }


async def test_stale_operation_does_not_add_the_current_id() -> None:
    port = FakeResolutionPort(
        ResolutionResult(
            status=ResolutionStatus.STALE_OPERATION,
            operation_id="op-aaa",
        )
    )
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/op-aaa/confirm")

    assert response.status_code == 409
    assert response.json() == {
        "status": "stale_operation",
        "operation_id": "op-aaa",
        "resolved_action": None,
    }
    assert "op-bbb" not in response.text


async def test_confirm_and_cancel_report_not_ready_without_a_resolution_port() -> None:
    async with client_for(query_port=FakeQueryPort(None)) as client:
        confirm = await client.post("/api/v1/pending-operation/op-aaa/confirm")
        cancel = await client.post("/api/v1/pending-operation/op-aaa/cancel")

    assert confirm.status_code == 503
    assert cancel.status_code == 503
    assert confirm.json()["code"] == "application_not_ready"
    assert cancel.json()["code"] == "application_not_ready"


async def test_blank_operation_id_is_422_and_does_not_call_the_port() -> None:
    port = FakeResolutionPort(_result(ResolutionStatus.SUCCESS, ResolvedAction.CONFIRM))
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/%20%20/confirm")

    assert response.status_code == 422
    assert response.json() == {
        "code": "invalid_operation_id",
        "detail": "operation_id must be a non-blank string",
    }
    assert port.confirmed == []


async def test_application_blank_id_error_is_422() -> None:
    port = FakeResolutionPort(
        error=ValueError("operation_id must be a non-blank string")
    )
    async with client_for(resolution_port=port) as client:
        response = await client.post("/api/v1/pending-operation/op-aaa/cancel")

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_operation_id"
    assert port.cancelled == ["op-aaa"]


async def test_unexpected_value_error_is_not_rewritten() -> None:
    port = FakeResolutionPort(error=ValueError("inventory exploded"))
    async with client_for(resolution_port=port) as client:
        with pytest.raises(ValueError, match="inventory exploded"):
            await client.post("/api/v1/pending-operation/op-aaa/confirm")


async def test_openapi_lists_the_pending_operation_routes() -> None:
    async with client_for() as client:
        response = await client.get("/openapi.json")

    paths = response.json()["paths"]
    assert "/api/v1/pending-operation" in paths
    assert "/api/v1/pending-operation/{operation_id}/confirm" in paths
    assert "/api/v1/pending-operation/{operation_id}/cancel" in paths


async def test_health_and_operator_page_still_work_without_ports() -> None:
    async with client_for() as client:
        health = await client.get("/health")
        page = await client.get("/")
        styles = await client.get("/static/styles.css")

    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert page.status_code == 200
    assert "Listo para escuchar" in page.text
    assert "VoiceStock Web está funcionando." not in page.text
    assert styles.status_code == 200
