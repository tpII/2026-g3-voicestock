"""Configuration for the PC communication server."""

import os
from dataclasses import dataclass

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


@dataclass(frozen=True, slots=True)
class ServerSettings:
    """Network binding used by the PC communication server."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("server host must not be blank")
        if not 1 <= self.port <= 65535:
            raise ValueError("server port must be between 1 and 65535")

    @classmethod
    def from_environment(cls) -> "ServerSettings":
        """Read server settings from environment variables."""
        raw_port = os.getenv("VOICESTOCK_PC_PORT", str(DEFAULT_PORT))
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("VOICESTOCK_PC_PORT must be an integer") from error

        return cls(
            host=os.getenv("VOICESTOCK_PC_HOST", DEFAULT_HOST),
            port=port,
        )
