"""Tests for InterpretationService using in-memory providers only."""

from typing import Any

import pytest

from pc.interpretation.providers import (
    ProviderError,
    ProviderRegistry,
    StubProvider,
    default_registry,
)
from pc.interpretation.results import ServiceErrorCode
from pc.interpretation.service import InterpretationService


class RaisingProvider:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def interpret(self, text: str) -> Any:
        raise self._error


class FixedProvider:
    def __init__(self, payload: Any) -> None:
        self._payload = payload
        self.received: list[str] = []

    def interpret(self, text: str) -> Any:
        self.received.append(text)
        return self._payload


def _service_with(provider: Any) -> InterpretationService:
    registry = ProviderRegistry()
    registry.register("test", lambda: provider)
    return InterpretationService(registry, "test")


def test_stub_provider_returns_success_with_recognized_text() -> None:
    service = InterpretationService(default_registry(), "stub")

    result = service.interpret("agregá dos paquetes de arroz")

    assert result.status == "success"
    assert result.payload == {"recognized_text": "agregá dos paquetes de arroz"}


def test_service_passes_text_unchanged_to_provider() -> None:
    provider = FixedProvider({"operation": "add"})

    result = _service_with(provider).interpret("sacá un litro de leche")

    assert provider.received == ["sacá un litro de leche"]
    assert result.payload == {"operation": "add"}


def test_substituting_the_active_provider_keeps_the_interface() -> None:
    registry = ProviderRegistry()
    registry.register("stub", StubProvider)
    registry.register("other", lambda: FixedProvider({"source": "other"}))

    stub_result = InterpretationService(registry, "stub").interpret("arroz")
    other_result = InterpretationService(registry, "other").interpret("arroz")

    assert stub_result.payload == {"recognized_text": "arroz"}
    assert other_result.payload == {"source": "other"}


@pytest.mark.parametrize("text", ["", "   ", "\n\t", None, 42])
def test_invalid_input_is_rejected_before_the_provider(text: Any) -> None:
    provider = FixedProvider({"operation": "add"})

    result = _service_with(provider).interpret(text)

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == ServiceErrorCode.INVALID_INPUT
    assert provider.received == []


@pytest.mark.parametrize("provider_name", [None, "", "gpt"])
def test_missing_or_unknown_provider_is_not_configured(
    provider_name: str | None,
) -> None:
    service = InterpretationService(default_registry(), provider_name)

    result = service.interpret("arroz")

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == ServiceErrorCode.PROVIDER_NOT_CONFIGURED


def test_provider_error_becomes_provider_failure() -> None:
    result = _service_with(RaisingProvider(ProviderError("model timed out"))).interpret(
        "arroz"
    )

    assert result.status == "error"
    assert result.error is not None
    assert result.error.code == ServiceErrorCode.PROVIDER_FAILURE
    assert result.error.detail == "model timed out"


def test_unexpected_provider_exception_hides_internal_detail() -> None:
    provider = RaisingProvider(RuntimeError("secret internal state"))

    result = _service_with(provider).interpret("arroz")

    assert result.error is not None
    assert result.error.code == ServiceErrorCode.PROVIDER_FAILURE
    assert "secret" not in (result.error.detail or "")


def test_registry_rejects_duplicate_names() -> None:
    registry = default_registry()

    with pytest.raises(ValueError):
        registry.register("stub", StubProvider)

    assert registry.names == ["stub"]
