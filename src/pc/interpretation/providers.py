"""Provider port, provider registry and the offline stub provider."""

from collections.abc import Callable
from typing import Any, Protocol


class InterpretationProvider(Protocol):
    """Port implemented by every interpretation backend.

    A local model and an external API both fit this port: the provider owns
    its own network access, timeouts and configuration. Expected failures are
    reported by raising ``ProviderError``.
    """

    def interpret(self, text: str) -> Any:
        """Interpret recognized text and return a JSON-serializable payload."""
        ...


ProviderFactory = Callable[[], InterpretationProvider]


class ProviderError(Exception):
    """Expected provider failure reported to callers as ``provider_failure``."""


class ProviderRegistry:
    """Named provider factories from which the active provider is resolved."""

    def __init__(self) -> None:
        self._factories: dict[str, ProviderFactory] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        """Make a provider selectable under ``name``."""
        if name in self._factories:
            raise ValueError(f"provider {name!r} is already registered")
        self._factories[name] = factory

    def create(self, name: str) -> InterpretationProvider | None:
        """Instantiate the named provider, or return None if it is unknown."""
        factory = self._factories.get(name)
        return factory() if factory is not None else None

    @property
    def names(self) -> list[str]:
        """Registered provider names in alphabetical order."""
        return sorted(self._factories)


class StubProvider:
    """Deterministic offline provider used until a real model is integrated."""

    def interpret(self, text: str) -> dict[str, str]:
        return {"recognized_text": text}


def default_registry() -> ProviderRegistry:
    """Registry with every provider shipped by VoiceStock."""
    registry = ProviderRegistry()
    registry.register("stub", StubProvider)
    return registry
