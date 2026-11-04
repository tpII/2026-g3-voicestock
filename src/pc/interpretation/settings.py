"""Configuration that selects the active interpretation provider."""

import os
from dataclasses import dataclass

DEFAULT_PROVIDER = "stub"


@dataclass(frozen=True, slots=True)
class InterpretationSettings:
    """Name of the provider the service should resolve, if any."""

    provider: str | None = DEFAULT_PROVIDER

    @classmethod
    def from_environment(cls) -> "InterpretationSettings":
        """Read VOICESTOCK_INTERPRETATION_PROVIDER; blank means not configured."""
        raw = os.getenv("VOICESTOCK_INTERPRETATION_PROVIDER", DEFAULT_PROVIDER)
        return cls(provider=raw.strip().lower() or None)
