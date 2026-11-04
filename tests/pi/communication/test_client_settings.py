"""Tests for Raspberry Pi client environment configuration."""

import pytest

from pi.communication.settings import ClientSettings


def test_client_settings_default_to_the_local_development_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VOICESTOCK_PC_URL", raising=False)
    monkeypatch.delenv("VOICESTOCK_PC_TIMEOUT", raising=False)

    settings = ClientSettings.from_environment()

    assert settings == ClientSettings(
        base_url="http://127.0.0.1:8000", timeout_seconds=10.0
    )


def test_client_settings_load_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_URL", "http://10.42.0.2:8123")
    monkeypatch.setenv("VOICESTOCK_PC_TIMEOUT", "2.5")

    settings = ClientSettings.from_environment()

    assert settings == ClientSettings(
        base_url="http://10.42.0.2:8123", timeout_seconds=2.5
    )


@pytest.mark.parametrize("url", ["", "10.42.0.2:8000", "ftp://pc:8000", "http://"])
def test_client_settings_reject_invalid_url(
    monkeypatch: pytest.MonkeyPatch,
    url: str,
) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_URL", url)

    with pytest.raises(ValueError):
        ClientSettings.from_environment()


@pytest.mark.parametrize("timeout", ["0", "-1", "nan", "inf", "soon"])
def test_client_settings_reject_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch,
    timeout: str,
) -> None:
    monkeypatch.setenv("VOICESTOCK_PC_TIMEOUT", timeout)

    with pytest.raises(ValueError):
        ClientSettings.from_environment()
