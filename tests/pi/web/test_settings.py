"""Tests for the Pi web server environment configuration."""

import pytest

from pi.web.settings import DEFAULT_HOST, DEFAULT_PORT, WebServerSettings


def test_web_settings_use_the_ethernet_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VOICESTOCK_WEB_HOST", raising=False)
    monkeypatch.delenv("VOICESTOCK_WEB_PORT", raising=False)

    settings = WebServerSettings.from_environment()

    assert settings == WebServerSettings(host=DEFAULT_HOST, port=DEFAULT_PORT)
    assert settings.host == "192.168.50.1"
    assert settings.port == 8000


def test_web_settings_override_host_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICESTOCK_WEB_HOST", "127.0.0.1")
    monkeypatch.setenv("VOICESTOCK_WEB_PORT", "8123")

    settings = WebServerSettings.from_environment()

    assert settings == WebServerSettings(host="127.0.0.1", port=8123)


@pytest.mark.parametrize("port", ["0", "65536", "-1", "not-a-number", ""])
def test_web_settings_reject_invalid_port(
    monkeypatch: pytest.MonkeyPatch,
    port: str,
) -> None:
    monkeypatch.setenv("VOICESTOCK_WEB_PORT", port)

    with pytest.raises(ValueError):
        WebServerSettings.from_environment()


def test_web_settings_reject_a_blank_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICESTOCK_WEB_HOST", "   ")

    with pytest.raises(ValueError, match="host"):
        WebServerSettings.from_environment()
