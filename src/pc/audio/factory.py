"""Build the audio handler selected by the environment."""

import logging

import httpx

from pc.audio.catalog import load_catalog_entries, prompt_rows
from pc.audio.groq_chat import GroqChatPoster
from pc.audio.pipeline import build_pipeline
from pc.audio.settings import GROQ_MODE, STUB_MODE, AudioPipelineSettings
from pc.communication.audio import AudioHandler
from pc.interpretation.groq import GroqDraftProvider
from pc.speech_to_text import GroqWhisperTranscriber

logger = logging.getLogger(__name__)


def audio_handler_for(
    settings: AudioPipelineSettings, stub: AudioHandler
) -> AudioHandler:
    """Return ``stub`` or the Groq pipeline. The stub needs no credentials."""
    if settings.mode == STUB_MODE:
        return stub
    if settings.mode != GROQ_MODE:
        raise ValueError("VOICESTOCK_AUDIO_PIPELINE must be stub or groq")
    if settings.catalog_path is None:
        raise ValueError("VOICESTOCK_CATALOG_PATH is required for the groq pipeline")
    if not settings.api_key:
        raise ValueError("Set VOICESTOCK_GROQ_API_KEY or GROQ_API_KEY")

    catalog = load_catalog_entries(settings.catalog_path)
    client = httpx.Client()
    transcriber = GroqWhisperTranscriber(
        api_key=settings.api_key,
        model=settings.stt_model,
        timeout_seconds=settings.stt_timeout_seconds,
        client=client,
    )
    provider = GroqDraftProvider(
        poster=GroqChatPoster(
            api_key=settings.api_key,
            timeout_seconds=settings.llm_timeout_seconds,
            client=client,
        ),
        catalog=prompt_rows(catalog),
        model=settings.llm_model,
    )
    pipeline = build_pipeline(transcriber.transcribe, provider, catalog)
    logger.info(
        "audio pipeline groq stt_model=%s llm_model=%s",
        settings.stt_model,
        settings.llm_model,
    )
    return pipeline.handle
