"""The web server runner accepts a host without opening a socket."""

import pytest
from fastapi import FastAPI

from pi.web.app import create_app
from pi.web.server import main, run_server
from pi.web.settings import WebServerSettings


def test_run_server_passes_the_app_and_bind_address_to_the_runner() -> None:
    app = create_app()
    seen: dict[str, object] = {}

    def runner(application: FastAPI, host: str, port: int) -> None:
        seen["app"] = application
        seen["host"] = host
        seen["port"] = port

    run_server(
        WebServerSettings(host="127.0.0.1", port=8123),
        app=app,
        runner=runner,
    )

    assert seen == {"app": app, "host": "127.0.0.1", "port": 8123}


def test_run_server_reads_bind_settings_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VOICESTOCK_WEB_HOST", "127.0.0.1")
    monkeypatch.setenv("VOICESTOCK_WEB_PORT", "9000")
    seen: dict[str, object] = {}

    def runner(application: FastAPI, host: str, port: int) -> None:
        del application
        seen["host"] = host
        seen["port"] = port

    run_server(runner=runner)

    assert seen == {"host": "127.0.0.1", "port": 9000}


def test_run_server_uses_uvicorn_when_no_runner_is_injected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_run(application: FastAPI, host: str, port: int) -> None:
        seen["title"] = application.title
        seen["host"] = host
        seen["port"] = port

    monkeypatch.setattr("pi.web.server.uvicorn.run", fake_run)

    run_server(WebServerSettings(host="127.0.0.1", port=8000))

    assert seen == {
        "title": "VoiceStock Web",
        "host": "127.0.0.1",
        "port": 8000,
    }


def test_main_starts_the_development_server(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[bool] = []
    monkeypatch.setattr("pi.web.server.run_server", lambda: called.append(True))

    main()

    assert called == [True]
