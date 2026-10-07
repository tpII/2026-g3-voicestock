"""Provider-independent interpretation of recognized text."""

from pc.interpretation.providers import (
    InterpretationProvider,
    ProviderError,
    ProviderRegistry,
    StubProvider,
    default_registry,
)
from pc.interpretation.results import (
    ServiceError,
    ServiceErrorCode,
    ServiceResult,
)
from pc.interpretation.service import InterpretationService
from pc.interpretation.settings import InterpretationSettings

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
