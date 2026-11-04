"""The web API reads and resolves the live operation cycle."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from fakes import ScriptedExecutor
from test_flow import EnvelopeClient, _finish, _flow, _success, _wav

from pi.pending_operation import ExecutionResult, ExecutionStatus
from pi.web.app import create_app

pytestmark = pytest.mark.anyio


@asynccontextmanager
async def client_for(flow: object) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(
        query_port=flow.query_port,  # type: ignore[attr-defined]
        resolution_port=flow.resolution_port,  # type: ignore[attr-defined]
        status_port=flow,  # type: ignore[arg-type]
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_the_live_cycle_is_visible_and_confirm_returns_to_idle(
    tmp_path: Path,
) -> None:
    flow = _flow(EnvelopeClient(_success()))
    try:
        async with client_for(flow) as client:
            idle = await client.get("/api/v1/system-status")
            assert idle.status_code == 200
            assert idle.json()["phase"] == "idle"
            assert idle.json()["headline"] == "Listo para escuchar"
            assert idle.json()["detail"] == "Presioná el botón para hablar"
            assert idle.json()["pending_operation"] is None

            assert flow.try_begin_recording() is True
            recording = await client.get("/api/v1/system-status")
            assert recording.json()["phase"] == "recording"
            assert recording.json()["headline"] == "Escuchando..."
            assert recording.json()["detail"] == "Soltá el botón para terminar"

            flow.on_capture_completed(_wav(tmp_path / "take.wav"))
            flow.wait_until_settled()
            waiting = await client.get("/api/v1/system-status")
            body = waiting.json()
            assert body["phase"] == "wait_confirmation"
            assert body["headline"] == "Operación pendiente de confirmación"
            pending = body["pending_operation"]
            assert pending["product"] == "Coca Cola Zero 2L"
            operation_id = pending["operation_id"]

            current = await client.get("/api/v1/pending-operation")
            assert current.status_code == 200
            assert current.json()["operation_id"] == operation_id

            confirmed = await client.post(
                f"/api/v1/pending-operation/{operation_id}/confirm"
            )
            assert confirmed.status_code == 200
            assert confirmed.json()["status"] == "success"

            after = await client.get("/api/v1/system-status")
            assert after.json()["phase"] == "idle"
            assert after.json()["pending_operation"] is None
            empty = await client.get("/api/v1/pending-operation")
            assert empty.status_code == 204
    finally:
        flow.close()


async def test_cancel_from_the_web_returns_the_cycle_to_idle(tmp_path: Path) -> None:
    flow = _flow(EnvelopeClient(_success()))
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        pending = flow.get_status().pending_operation
        assert pending is not None
        async with client_for(flow) as client:
            cancelled = await client.post(
                f"/api/v1/pending-operation/{pending.operation_id}/cancel"
            )
            assert cancelled.status_code == 200
            assert cancelled.json()["status"] == "success"
            status = await client.get("/api/v1/system-status")
            assert status.json()["phase"] == "idle"
    finally:
        flow.close()


async def test_a_failed_confirm_keeps_the_operation_on_the_status(
    tmp_path: Path,
) -> None:
    flow = _flow(
        EnvelopeClient(_success()),
        executor=ScriptedExecutor(ExecutionResult(status=ExecutionStatus.FAILED)),
    )
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        pending = flow.get_status().pending_operation
        assert pending is not None
        async with client_for(flow) as client:
            failed = await client.post(
                f"/api/v1/pending-operation/{pending.operation_id}/confirm"
            )
            assert failed.status_code == 503
            assert failed.json()["status"] == "execution_failed"
            status = await client.get("/api/v1/system-status")
            body = status.json()
            assert body["phase"] == "wait_confirmation"
            assert body["pending_operation"]["operation_id"] == pending.operation_id
    finally:
        flow.close()
