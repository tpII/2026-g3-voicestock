"""Tests for the voicestock-pi-client command."""

import json
import socket

import pytest

from voicestock.pi_client import main


def test_success_prints_the_envelope_and_exits_zero(
    pc_server_url: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_URL", pc_server_url)

    exit_code = main(["agregá", "dos", "paquetes", "de", "arroz"])

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "status": "success",
        "payload": {
            "status": "success",
            "payload": {"recognized_text": "agregá dos paquetes de arroz"},
            "error": None,
        },
        "error": None,
    }


def test_communication_error_prints_the_envelope_and_exits_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    monkeypatch.setenv("VOICESTOCK_PC_URL", f"http://127.0.0.1:{port}")

    exit_code = main(["arroz"])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == ("connection_failed")


def test_missing_text_prints_usage_and_exits_two(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err
