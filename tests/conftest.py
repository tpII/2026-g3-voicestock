"""Shared fixtures for tests that need a real PC server on localhost."""

import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn

from pc.interpretation import default_registry
from pc.main import create_pc_app


@pytest.fixture
def pc_server_url() -> Iterator[str]:
    config = uvicorn.Config(
        create_pc_app(default_registry(), "stub"),
        host="127.0.0.1",
        port=0,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("PC server did not start")
        time.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
