"""Roundtrip tests for the Raspberry Pi client over real localhost sockets."""

import socket
import threading
import time
from collections.abc import Iterator

import pytest
import uvicorn

from voicestock.communication import (
    ClientErrorCode,
    ClientSettings,
    HttpInterpretationClient,
)
from voicestock.interpretation import default_registry
from voicestock.pc_server import create_pc_app


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


def _client(url: str, timeout_seconds: float = 2.0) -> HttpInterpretationClient:
    return HttpInterpretationClient(
        ClientSettings(base_url=url, timeout_seconds=timeout_seconds)
    )


def test_roundtrip_through_the_real_pc_server(pc_server_url: str) -> None:
    with _client(pc_server_url) as client:
        envelope = client.interpret("agregá dos paquetes de arroz")

    assert envelope.status == "success"
    assert envelope.payload == {
        "status": "success",
        "payload": {"recognized_text": "agregá dos paquetes de arroz"},
        "error": None,
    }


def test_server_transport_error_reaches_the_caller(pc_server_url: str) -> None:
    with _client(pc_server_url) as client:
        envelope = client.interpret("   ")

    assert envelope.error is not None
    assert envelope.error.code == "invalid_request"


def test_refused_connection_is_reported() -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    # The port is now closed: nothing is listening there.

    with _client(f"http://127.0.0.1:{port}") as client:
        envelope = client.interpret("arroz")

    assert envelope.error is not None
    assert envelope.error.code == ClientErrorCode.CONNECTION_FAILED


def test_silent_server_does_not_block_forever() -> None:
    # The kernel accepts the TCP connection, but nobody ever answers.
    with socket.socket() as silent:
        silent.bind(("127.0.0.1", 0))
        silent.listen()
        port = silent.getsockname()[1]

        started = time.monotonic()
        with _client(f"http://127.0.0.1:{port}", timeout_seconds=0.3) as client:
            envelope = client.interpret("arroz")
        elapsed = time.monotonic() - started

    assert envelope.error is not None
    assert envelope.error.code == ClientErrorCode.TIMEOUT
    assert elapsed < 2
