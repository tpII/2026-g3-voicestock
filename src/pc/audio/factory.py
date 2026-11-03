"""Build the audio handler selected by the environment.

The Groq HTTP client is created when the ASGI lifespan starts and closed
when it ends. Stub mode never opens that client. Speech-to-text and the
draft provider share the one client the session owns.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx

from pc.audio.catalog import CatalogEntry, load_catalog_entries, prompt_rows
from pc.audio.groq_chat import GroqChatPoster
from pc.audio.pipeline import AudioInterpretationPipeline, build_pipeline
from pc.audio.settings import GROQ_MODE, STUB_MODE, AudioPipelineSettings
from pc.communication.audio import AudioHandler, ReceivedAudio
from pc.interpretation.groq import GroqDraftProvider
from pc.interpretation.results import ServiceResult
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
    """One shared Groq client for transcription and interpretation."""

    def __init__(
        self,
        settings: AudioPipelineSettings,
        catalog: tuple[CatalogEntry, ...],
    ) -> None:
        self._settings = settings
        self._catalog = catalog
        self._client: httpx.Client | None = None
        self._pipeline: AudioInterpretationPipeline | None = None
        self._transcriber: GroqWhisperTranscriber | None = None
        self._poster: GroqChatPoster | None = None
        self._closed = False

    def handle(self, audio: ReceivedAudio) -> ServiceResult:
        """Transcribe and interpret one WAV. The session must be started."""
        if self._pipeline is None:
            raise RuntimeError("audio pipeline is not started")
        return self._pipeline.handle(audio)

    def start(self) -> None:
        """Open the shared client once. A closed session stays closed."""
        if self._closed or self._pipeline is not None:
            return
        if not self._settings.api_key:
            raise ValueError("Set VOICESTOCK_GROQ_API_KEY or GROQ_API_KEY")
        client = httpx.Client()
        try:
            transcriber = GroqWhisperTranscriber(
                api_key=self._settings.api_key,
                model=self._settings.stt_model,
                timeout_seconds=self._settings.stt_timeout_seconds,
                client=client,
            )
            poster = GroqChatPoster(
                api_key=self._settings.api_key,
                timeout_seconds=self._settings.llm_timeout_seconds,
                client=client,
            )
            provider = GroqDraftProvider(
                poster=poster,
                catalog=prompt_rows(self._catalog),
                model=self._settings.llm_model,
            )
            pipeline = build_pipeline(transcriber.transcribe, provider, self._catalog)
        except Exception:
            client.close()
            raise
        self._client = client
        self._transcriber = transcriber
        self._poster = poster
        self._pipeline = pipeline
        logger.info(
            "audio pipeline groq stt_model=%s llm_model=%s",
            self._settings.stt_model,
            self._settings.llm_model,
        )

    def close(self) -> None:
        """Close the shared client once."""
        if self._closed:
            return
        self._closed = True
        client = self._client
        self._client = None
        if client is not None:
            client.close()

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
    """Select the stub or load the catalog. The HTTP client waits for startup."""
    if settings.mode == STUB_MODE:
        return StubAudioSession(stub)
    if settings.mode != GROQ_MODE:
        raise ValueError("VOICESTOCK_AUDIO_PIPELINE must be stub or groq")
    if settings.catalog_path is None:
        raise ValueError("VOICESTOCK_CATALOG_PATH is required for the groq pipeline")
    if not settings.api_key:
        raise ValueError("Set VOICESTOCK_GROQ_API_KEY or GROQ_API_KEY")
    return GroqAudioSession(settings, load_catalog_entries(settings.catalog_path))
