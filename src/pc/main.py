"""PC entry point that wires InterpretationService into the HTTP server.

This is the only module that knows both layers: the communication server stays
unaware of interpretation, and the service stays unaware of HTTP.

Audio requests go to ``describe_received_audio`` until transcription through
an API exists. The real audio handler is passed to ``create_pc_app`` here; it
is expected to transcribe ``audio.wav`` and return the ``ServiceResult`` of
``InterpretationService.interpret`` for that text.
"""

import uvicorn
from fastapi import FastAPI

from pc.communication import AudioHandler, ReceivedAudio, ServerSettings, create_app
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
) -> FastAPI:
    """Build the HTTP app: text goes to InterpretationService.interpret."""
    service = InterpretationService(registry, provider_name)
    return create_app(service.interpret, audio_handler=audio_handler)


def main() -> None:
    """Run the PC server with the provider selected in the environment."""
    server_settings = ServerSettings.from_environment()
    interpretation_settings = InterpretationSettings.from_environment()
    uvicorn.run(
        create_pc_app(default_registry(), interpretation_settings.provider),
        host=server_settings.host,
        port=server_settings.port,
    )


if __name__ == "__main__":
    main()
