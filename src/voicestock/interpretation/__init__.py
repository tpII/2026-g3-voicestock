"""Provider-independent interpretation of recognized text."""

from voicestock.interpretation.providers import (
    InterpretationProvider,
    ProviderError,
    ProviderRegistry,
    StubProvider,
    default_registry,
)
from voicestock.interpretation.results import (
    ServiceError,
    ServiceErrorCode,
    ServiceResult,
)
from voicestock.interpretation.service import InterpretationService
from voicestock.interpretation.settings import InterpretationSettings

__all__ = [
    "InterpretationProvider",
    "InterpretationService",
    "InterpretationSettings",
    "ProviderError",
    "ProviderRegistry",
    "ServiceError",
    "ServiceErrorCode",
    "ServiceResult",
    "StubProvider",
    "default_registry",
]
