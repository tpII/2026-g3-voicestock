"""Build the audio handler selected by the environment.

The Groq HTTP client is created when the ASGI lifespan starts and closed
when it ends. Stub mode never opens that client and never asks the Pi for
a catalog. The Groq session synchronizes the catalog before each WAV is
transcribed.
"""

import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from pc.audio.catalog import InstalledCatalog, prompt_rows
from pc.audio.groq_chat import GroqChatPoster
from pc.audio.pi_catalog import CatalogSyncError, PiCatalogSession
from pc.audio.pipeline import AudioInterpretationPipeline, build_pipeline
from pc.audio.settings import GROQ_MODE, STUB_MODE, AudioPipelineSettings
from pc.communication.audio import AudioHandler, ReceivedAudio
from pc.interpretation.groq import GroqDraftProvider
from pc.interpretation.results import ServiceErrorCode, ServiceResult
from pc.speech_to_text import GroqWhisperTranscriber

logger = logging.getLogger(__name__)


class StubAudioSession:
    """Diagnostic handler with nothing to open or close."""

    def __init__(self, handler: AudioHandler) -> None:
        self._handler = handler
        self._closed = False

    def handle(self, audio: ReceivedAudio) -> ServiceResult:
        """Forward to the diagnostic stub."""
        return self._handler(audio)

    def start(self) -> None:
        """Stub mode has no external resources."""

    def close(self) -> None:
        """Mark the session closed. A second call does nothing."""
        self._closed = True

    @asynccontextmanager
    async def lifespan(self, app: object) -> AsyncIterator[None]:
        """Run the app without creating a Groq client."""
        del app
        self.start()
        try:
            yield
        finally:
            self.close()


class GroqAudioSession:
    """One Groq client and one Pi catalog client for this process."""

    def __init__(self, settings: AudioPipelineSettings) -> None:
        self._settings = settings
        self._groq: httpx.Client | None = None
        self._catalog: PiCatalogSession | None = None
        self._pipeline: AudioInterpretationPipeline | None = None
        self._installed: InstalledCatalog | None = None
        self._transcriber: GroqWhisperTranscriber | None = None
        self._poster: GroqChatPoster | None = None
        self._lock = threading.Lock()
        self._closed = False

    def handle(self, audio: ReceivedAudio) -> ServiceResult:
        """Synchronize the catalog, then transcribe and interpret one WAV."""
        if self._transcriber is None or self._poster is None or self._catalog is None:
            raise RuntimeError("audio pipeline is not started")
        with self._lock:
            try:
                catalog = self._catalog.pull()
            except CatalogSyncError as error:
                logger.info("catalog synchronization failed")
                return ServiceResult.failure(
                    ServiceErrorCode.CATALOG_UNAVAILABLE, str(error)
                )
            if catalog is not self._installed:
                provider = GroqDraftProvider(
                    poster=self._poster,
                    catalog=prompt_rows(catalog.entries),
                    model=self._settings.llm_model,
                )
                pipeline = build_pipeline(
                    self._transcriber.transcribe, provider, catalog.entries
                )
                self._catalog.accept(catalog)
                self._installed = catalog
                self._pipeline = pipeline
            pipeline = self._pipeline
        if pipeline is None:
            raise RuntimeError("audio pipeline is not started")
        return pipeline.handle(audio)

    def start(self) -> None:
        """Open the shared clients once. A closed session stays closed."""
        if self._closed or self._transcriber is not None:
            return
        if not self._settings.api_key:
            raise ValueError("Set VOICESTOCK_GROQ_API_KEY or GROQ_API_KEY")
        groq = httpx.Client()
        catalog_client = httpx.Client(timeout=self._settings.catalog_timeout_seconds)
        try:
            catalog = PiCatalogSession(self._settings.pi_base_url, catalog_client)
            transcriber = GroqWhisperTranscriber(
                api_key=self._settings.api_key,
                model=self._settings.stt_model,
                timeout_seconds=self._settings.stt_timeout_seconds,
                client=groq,
            )
            poster = GroqChatPoster(
                api_key=self._settings.api_key,
                timeout_seconds=self._settings.llm_timeout_seconds,
                client=groq,
            )
        except Exception:
            groq.close()
            catalog_client.close()
            raise
        self._groq = groq
        self._catalog = catalog
        self._transcriber = transcriber
        self._poster = poster
        logger.info(
            "audio pipeline groq stt_model=%s llm_model=%s",
            self._settings.stt_model,
            self._settings.llm_model,
        )

    def close(self) -> None:
        """Close the Groq client and the catalog client once."""
        if self._closed:
            return
        self._closed = True
        groq = self._groq
        catalog = self._catalog
        self._groq = None
        self._catalog = None
        if catalog is not None:
            catalog.close()
        if groq is not None:
            groq.close()

    @asynccontextmanager
    async def lifespan(self, app: object) -> AsyncIterator[None]:
        """Open the Groq client for the app and close it on the way out."""
        del app
        self.start()
        try:
            yield
        finally:
            self.close()


def audio_session_for(
    settings: AudioPipelineSettings, stub: AudioHandler
) -> StubAudioSession | GroqAudioSession:
    """Select the stub or the Groq session. HTTP clients wait for startup."""
    if settings.mode == STUB_MODE:
        return StubAudioSession(stub)
    if settings.mode != GROQ_MODE:
        raise ValueError("VOICESTOCK_AUDIO_PIPELINE must be stub or groq")
    if not settings.api_key:
        raise ValueError("Set VOICESTOCK_GROQ_API_KEY or GROQ_API_KEY")
    return GroqAudioSession(settings)
