"""Configuration for the Raspberry Pi web server."""

import os
from dataclasses import dataclass

DEFAULT_HOST = "192.168.50.1"
DEFAULT_PORT = 8000


@dataclass(frozen=True, slots=True)
class WebServerSettings:
    """Address where the Pi web server accepts browser connections.

    The default host is the Raspberry Pi address on the VoiceStock Ethernet
    segment. Override it for local development. The PC interpretation server
    uses port 8000 on the PC, which is a different machine.
    """

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("web server host must not be blank")
        if not 1 <= self.port <= 65535:
            raise ValueError("web server port must be between 1 and 65535")

    @classmethod
    def from_environment(cls) -> "WebServerSettings":
        """Read web server settings from environment variables."""
        raw_port = os.getenv("VOICESTOCK_WEB_PORT", str(DEFAULT_PORT))
        try:
            port = int(raw_port)
        except ValueError as error:
            raise ValueError("VOICESTOCK_WEB_PORT must be an integer") from error

        return cls(
            host=os.getenv("VOICESTOCK_WEB_HOST", DEFAULT_HOST),
            port=port,
        )
