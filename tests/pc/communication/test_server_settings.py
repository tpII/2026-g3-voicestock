"""Tests for PC server environment configuration."""

import pytest

from pc.communication.settings import ServerSettings


def test_server_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_HOST", "0.0.0.0")
    monkeypatch.setenv("VOICESTOCK_PC_PORT", "8123")

    settings = ServerSettings.from_environment()

    assert settings == ServerSettings(host="0.0.0.0", port=8123)


@pytest.mark.parametrize("port", ["0", "65536", "not-a-number"])
def test_server_settings_reject_invalid_port(
    monkeypatch: pytest.MonkeyPatch,
    port: str,
) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_PORT", port)

    with pytest.raises(ValueError):
        ServerSettings.from_environment()
