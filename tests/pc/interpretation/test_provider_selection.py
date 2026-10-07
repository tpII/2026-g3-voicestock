"""Tests for reading the active provider name from the environment."""

import pytest

from pc.interpretation.settings import InterpretationSettings


def test_default_provider_is_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VOICESTOCK_INTERPRETATION_PROVIDER", raising=False)

    assert InterpretationSettings.from_environment().provider == "stub"


def test_provider_name_is_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICESTOCK_INTERPRETATION_PROVIDER", "  Stub ")

    assert InterpretationSettings.from_environment().provider == "stub"


def test_blank_provider_means_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICESTOCK_INTERPRETATION_PROVIDER", "  ")

    assert InterpretationSettings.from_environment().provider is None
