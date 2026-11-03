"""PC entry point that wires InterpretationService into the HTTP server.

This is the only module that knows both layers: the communication server stays
unaware of interpretation, and the service stays unaware of HTTP.

``VOICESTOCK_AUDIO_PIPELINE=stub`` keeps ``describe_received_audio``.
``groq`` transcribes the WAV, interprets the text and returns a version-1
contract plus ``recognized_text``. The text route is unchanged.
"""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager

import uvicorn
from fastapi import FastAPI

from pc.audio.factory import audio_session_for
from pc.audio.settings import AudioPipelineSettings
from pc.communication import (
    AudioHandler,
    ReceivedAudio,
    ServerSettings,
    create_app,
)
from pc.interpretation import (
    InterpretationService,
    InterpretationSettings,
    ProviderRegistry,
    ServiceResult,
    default_registry,
)


def describe_received_audio(audio: ReceivedAudio) -> ServiceResult:
    """Stub audio handler: report what arrived instead of transcribing it.

    It answers with a ``ServiceResult`` so the Raspberry Pi reads the same
    layers it will read once the real handler is connected.
    """
    return ServiceResult.success(
        {
            "received_audio": {
                "size_bytes": len(audio.wav),
                "duration_seconds": audio.duration_seconds,
                "sample_rate_hz": audio.sample_rate_hz,
                "channels": audio.channels,
                "sample_width_bytes": audio.sample_width_bytes,
            }
        }
    )


def create_pc_app(
    registry: ProviderRegistry,
    provider_name: str | None,
    audio_handler: AudioHandler = describe_received_audio,
    lifespan: Callable[[FastAPI], AbstractAsyncContextManager[None]] | None = None,
) -> FastAPI:
    """Build the HTTP app: text goes to InterpretationService.interpret."""
    service = InterpretationService(registry, provider_name)
    return create_app(
        service.interpret,
        audio_handler=audio_handler,
        lifespan=lifespan,
    )


def main() -> None:
    """Run the PC server with the provider selected in the environment."""
    server_settings = ServerSettings.from_environment()
    interpretation_settings = InterpretationSettings.from_environment()
    session = audio_session_for(
        AudioPipelineSettings.from_environment(),
        describe_received_audio,
    )
    uvicorn.run(
        create_pc_app(
            default_registry(),
            interpretation_settings.provider,
            session.handle,
            session.lifespan,
        ),
        host=server_settings.host,
        port=server_settings.port,
    )


if __name__ == "__main__":
    main()
