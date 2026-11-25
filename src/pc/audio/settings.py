"""Settings that select the diagnostic stub or the Groq audio pipeline."""

import math
import os
from dataclasses import dataclass
from urllib.parse import urlsplit

STUB_MODE = "stub"
GROQ_MODE = "groq"
_MODES = {STUB_MODE, GROQ_MODE}
DEFAULT_PI_URL = "http://192.168.50.1:8000"


@dataclass(frozen=True, slots=True)
class AudioPipelineSettings:
    """Environment selection for ``POST /api/v1/interpret-audio``."""

    mode: str = STUB_MODE
    pi_base_url: str = DEFAULT_PI_URL
    catalog_timeout_seconds: float = 5.0
    stt_model: str = "whisper-large-v3-turbo"
    llm_model: str = "openai/gpt-oss-20b"
    stt_timeout_seconds: float = 20.0
    llm_timeout_seconds: float = 20.0
    api_key: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in _MODES:
            raise ValueError("VOICESTOCK_AUDIO_PIPELINE must be stub or groq")
        if self.stt_timeout_seconds <= 0 or self.llm_timeout_seconds <= 0:
            raise ValueError("audio pipeline timeouts must be positive")
        if not self.stt_model.strip() or not self.llm_model.strip():
            raise ValueError("audio pipeline model names must not be blank")
        if self.catalog_timeout_seconds <= 0 or not math.isfinite(
            self.catalog_timeout_seconds
        ):
            raise ValueError("VOICESTOCK_CATALOG_TIMEOUT_SECONDS must be positive")
        if self.mode == GROQ_MODE:
            _require_pi_url(self.pi_base_url)

    @classmethod
    def from_environment(cls) -> "AudioPipelineSettings":
        """Read pipeline settings. The API key is not logged."""
        api_key = (
            os.getenv("VOICESTOCK_GROQ_API_KEY", "").strip()
            or os.getenv("GROQ_API_KEY", "").strip()
        )
        pi_url = os.getenv("VOICESTOCK_PI_URL", DEFAULT_PI_URL).strip()
        return cls(
            mode=os.getenv("VOICESTOCK_AUDIO_PIPELINE", STUB_MODE).strip().lower(),
            pi_base_url=pi_url or DEFAULT_PI_URL,
            catalog_timeout_seconds=_positive_float(
                "VOICESTOCK_CATALOG_TIMEOUT_SECONDS", "5"
            ),
            stt_model=os.getenv(
                "VOICESTOCK_STT_MODEL", "whisper-large-v3-turbo"
            ).strip(),
            llm_model=os.getenv("VOICESTOCK_LLM_MODEL", "openai/gpt-oss-20b").strip(),
            stt_timeout_seconds=_positive_float("VOICESTOCK_STT_TIMEOUT_SECONDS", "20"),
            llm_timeout_seconds=_positive_float("VOICESTOCK_LLM_TIMEOUT_SECONDS", "20"),
            api_key=api_key or None,
        )


def _require_pi_url(value: str) -> None:
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("VOICESTOCK_PI_URL must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise ValueError("VOICESTOCK_PI_URL must not include credentials")


def _positive_float(name: str, default: str) -> float:
    raw = os.getenv(name, default).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error
    if value <= 0 or not math.isfinite(value):
        raise ValueError(f"{name} must be positive")
    return value
