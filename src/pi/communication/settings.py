"""Configuration for the Raspberry Pi communication client."""

import math
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

DEFAULT_PC_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class ClientSettings:
    """Destination and timeout used by the Raspberry Pi client to reach the PC.

    The destination is only consumed here: the PC address is assigned by the
    local network (LocalNetworkInfra), not configured by this client.
    """

    base_url: str = DEFAULT_PC_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        parts = urlsplit(self.base_url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise ValueError("PC URL must be an http(s) URL with a host")
        if not (math.isfinite(self.timeout_seconds) and self.timeout_seconds > 0):
            raise ValueError(
                "client timeout must be a finite, positive number of seconds"
            )

    @classmethod
    def from_environment(cls) -> "ClientSettings":
        """Read client settings from environment variables."""
        raw_timeout = os.getenv("VOICESTOCK_PC_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))
        try:
            timeout_seconds = float(raw_timeout)
        except ValueError as error:
            raise ValueError("VOICESTOCK_PC_TIMEOUT must be a number") from error

        return cls(
            base_url=os.getenv("VOICESTOCK_PC_URL", DEFAULT_PC_URL),
            timeout_seconds=timeout_seconds,
        )
