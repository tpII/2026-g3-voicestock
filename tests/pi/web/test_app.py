"""The Pi web app answers health checks and serves the local placeholder."""

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


async def test_root_serves_the_placeholder_page(client: httpx.AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    body = response.text
    assert "VoiceStock Web está funcionando." in body
    assert 'href="/static/styles.css"' in body
    assert 'src="/static/app.js"' in body
    assert "Coca-Cola" not in body


async def test_static_assets_are_served_from_the_application(
    client: httpx.AsyncClient,
) -> None:
    styles = await client.get("/static/styles.css")
    script = await client.get("/static/app.js")

    assert styles.status_code == 200
    assert "text/css" in styles.headers["content-type"]
    assert ".status-panel" in styles.text
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]
    assert "serverStatus" in script.text
