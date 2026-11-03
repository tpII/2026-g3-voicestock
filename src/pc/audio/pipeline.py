"""Compose transcription, interpretation and the version-1 contract.

The HTTP route stays in the communication server. This pipeline is one
audio handler: it returns a ``ServiceResult`` and does not raise provider
exceptions to FastAPI.
"""

import logging
from collections.abc import Callable

from pc.audio.catalog import (
    CatalogEntry,
    ProductMatch,
    match_description,
)
from pc.communication.audio import ReceivedAudio
from pc.interpretation.providers import InterpretationProvider, ProviderRegistry
from pc.interpretation.results import ServiceErrorCode, ServiceResult
from pc.interpretation.service import InterpretationService
from pc.operation_contract import DraftMappingError, map_draft
from pc.speech_to_text.errors import TranscriptionError, TranscriptionFailure

logger = logging.getLogger(__name__)

_TRANSCRIPTION_CODES = {
    TranscriptionFailure.EMPTY: ServiceErrorCode.EMPTY_TRANSCRIPTION,
    TranscriptionFailure.TIMEOUT: ServiceErrorCode.TRANSCRIPTION_TIMEOUT,
    TranscriptionFailure.FAILED: ServiceErrorCode.TRANSCRIPTION_FAILURE,
    TranscriptionFailure.NOT_CONFIGURED: ServiceErrorCode.TRANSCRIPTION_FAILURE,
}
_MATCH_CODES = {
    ProductMatch.AMBIGUOUS: ServiceErrorCode.AMBIGUOUS_PRODUCT,
    ProductMatch.UNKNOWN: ServiceErrorCode.UNKNOWN_PRODUCT,
    ProductMatch.INSUFFICIENT: ServiceErrorCode.INSUFFICIENT_PRODUCT,
}
_MATCH_DETAILS = {
    ProductMatch.AMBIGUOUS: "several catalog products match the description",
    ProductMatch.UNKNOWN: "no catalog product matches the description",
    ProductMatch.INSUFFICIENT: "the product description has no usable name",
}


class AudioInterpretationPipeline:
    """WAV to a contract payload, or a typed service error."""

    def __init__(
        self,
        transcriber: Callable[[bytes], str],
        service: InterpretationService,
        catalog: tuple[CatalogEntry, ...],
    ) -> None:
        if not catalog:
            raise ValueError("audio pipeline catalog must not be empty")
        self._transcriber = transcriber
        self._service = service
        self._catalog = catalog

    def handle(self, audio: ReceivedAudio) -> ServiceResult:
        """Transcribe ``audio`` and return a contract or a typed failure."""
        try:
            recognized_text = self._transcriber(audio.wav)
        except TranscriptionError as error:
            logger.info("audio transcription was not accepted")
            code = _TRANSCRIPTION_CODES[error.kind]
            return ServiceResult.failure(code, str(error) or None)
        except Exception:
            logger.info("audio transcription failed unexpectedly")
            return ServiceResult.failure(
                ServiceErrorCode.TRANSCRIPTION_FAILURE,
                "speech-to-text failed unexpectedly",
            )

        interpreted = self._service.interpret(recognized_text)
        if interpreted.status != "success":
            return interpreted

        draft = interpreted.payload
        count = _operation_count(draft)
        if count != 1:
            return ServiceResult.failure(
                ServiceErrorCode.UNSUPPORTED_COMMAND,
                f"expected exactly one operation, got {count}",
            )
        try:
            contract = map_draft(draft)
        except DraftMappingError as error:
            return ServiceResult.failure(
                ServiceErrorCode.CONTRACT_MAPPING_FAILURE, str(error)
            )

        match = match_description(contract.operations[0].product, self._catalog)
        if match is not ProductMatch.IDENTIFIED:
            return ServiceResult.failure(_MATCH_CODES[match], _MATCH_DETAILS[match])

        payload = contract.model_dump(mode="json")
        payload["recognized_text"] = recognized_text
        return ServiceResult.success(payload)


def build_pipeline(
    transcriber: Callable[[bytes], str],
    provider: InterpretationProvider,
    catalog: tuple[CatalogEntry, ...],
) -> AudioInterpretationPipeline:
    """Wire one provider instance behind InterpretationService."""
    registry = ProviderRegistry()
    registry.register("groq", lambda: provider)
    service = InterpretationService(registry, "groq")
    return AudioInterpretationPipeline(transcriber, service, catalog)


def _operation_count(draft: object) -> int | None:
    if not isinstance(draft, dict):
        return None
    operations = draft.get("operaciones")
    if not isinstance(operations, list):
        return None
    return len(operations)
