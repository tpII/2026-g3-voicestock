"""PC entry point that wires InterpretationService into the HTTP server.

This is the only module that knows both layers: the communication server stays
unaware of interpretation, and the service stays unaware of HTTP.
"""

import uvicorn
from fastapi import FastAPI

from pc.communication.server import create_app
from pc.communication.settings import ServerSettings
from pc.interpretation import (
    InterpretationService,
    InterpretationSettings,
    ProviderRegistry,
    default_registry,
)


def create_pc_app(registry: ProviderRegistry, provider_name: str | None) -> FastAPI:
    """Build the HTTP app whose handler is InterpretationService.interpret."""
    service = InterpretationService(registry, provider_name)
    return create_app(service.interpret)


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
