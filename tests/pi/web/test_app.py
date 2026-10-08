"""The Pi web app answers health checks and serves the operator page."""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from pi.web.app import create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client


def test_create_app_returns_a_fastapi_app() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.state.query_port is None
    assert app.state.resolution_port is None


def test_create_app_keeps_ports_for_a_later_api() -> None:
    query_port = object()
    resolution_port = object()

    app = create_app(query_port=query_port, resolution_port=resolution_port)

    assert app.state.query_port is query_port
    assert app.state.resolution_port is resolution_port


async def test_health_reports_the_http_server_is_up(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_root_serves_the_operator_page(client: httpx.AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "<header" in body
    assert 'id="connection-label"' in body
    assert "Listo para escuchar" in body
    assert 'id="confirm-button"' in body
    assert 'id="cancel-button"' in body
    assert "Operación pendiente" in body
    assert "Texto reconocido" in body
    assert 'href="/static/styles.css"' in body
    assert 'src="/static/app.js"' in body
    assert "VoiceStock Web está funcionando." not in body
    assert "https://" not in body
    assert "Coca-Cola" not in body


async def test_static_assets_are_served_from_the_application(
    client: httpx.AsyncClient,
) -> None:
    styles = await client.get("/static/styles.css")
    script = await client.get("/static/app.js")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".operation-card" in styles.text
    assert "https://" not in styles.text
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    page_script = script.text
    assert "/api/v1/pending-operation" in page_script
    assert "textContent" in page_script
    assert "setTimeout" in page_script
    assert "setInterval" not in page_script
    assert "innerHTML" not in page_script
    assert "https://" not in page_script
