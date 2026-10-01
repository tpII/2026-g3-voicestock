"""Provider-independent entry point for interpreting recognized text."""

from voicestock.interpretation.providers import ProviderError, ProviderRegistry
from voicestock.interpretation.results import ServiceErrorCode, ServiceResult


class InterpretationService:
    """Resolve the active provider and type every interpretation outcome."""

    def __init__(self, registry: ProviderRegistry, provider_name: str | None) -> None:
        self._provider_name = provider_name
        self._provider = registry.create(provider_name) if provider_name else None

    def interpret(self, text: str) -> ServiceResult:
        """Return a ServiceResult; failures never escape as exceptions."""
        if not isinstance(text, str) or not text.strip():
            return ServiceResult.failure(
                ServiceErrorCode.INVALID_INPUT, "text must be a non-blank string"
            )

        if self._provider is None:
            return ServiceResult.failure(
                ServiceErrorCode.PROVIDER_NOT_CONFIGURED,
                f"no provider available for {self._provider_name!r}",
            )

        try:
            payload = self._provider.interpret(text)
        except ProviderError as error:
            return ServiceResult.failure(
                ServiceErrorCode.PROVIDER_FAILURE, str(error) or None
            )
        except Exception:
            # Unknown provider bugs must still reach the caller as a typed
            # result, without leaking internal error messages.
            return ServiceResult.failure(
                ServiceErrorCode.PROVIDER_FAILURE, "the provider failed unexpectedly"
            )

        return ServiceResult.success(payload)
