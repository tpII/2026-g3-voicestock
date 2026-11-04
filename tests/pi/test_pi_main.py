"""Tests for the voicestock-pi-client command, with text and with audio."""

import json
import socket
from pathlib import Path

import pytest

from pi.main import main


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


def test_audio_option_sends_the_wav_file(
    pc_server_url: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_URL", pc_server_url)
    wav = Path(__file__).parents[1] / "fixtures/speech_to_text/wav/basico"
    wav = wav / "solo_restar.wav"

    exit_code = main(["--audio", str(wav)])

    assert exit_code == 0
    received = json.loads(capsys.readouterr().out)["payload"]["payload"]
    assert received["received_audio"]["size_bytes"] == wav.stat().st_size


def test_missing_audio_file_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["--audio", str(tmp_path / "missing.wav")])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["error"]["code"] == (
        "audio_read_failure"
    )


@pytest.mark.parametrize("args", [["--audio"], ["--audio", "a.wav", "b.wav"]])
def test_audio_option_needs_exactly_one_path(
    args: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(args) == 2
    assert "--audio" in capsys.readouterr().err
