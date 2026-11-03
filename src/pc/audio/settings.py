"""Settings that select the diagnostic stub or the Groq audio pipeline."""

import os
from dataclasses import dataclass
from pathlib import Path

STUB_MODE = "stub"
GROQ_MODE = "groq"
_MODES = {STUB_MODE, GROQ_MODE}


@dataclass(frozen=True, slots=True)
class AudioPipelineSettings:
    """Environment selection for ``POST /api/v1/interpret-audio``."""

    mode: str = STUB_MODE
    catalog_path: Path | None = None
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

    @classmethod
    def from_environment(cls) -> "AudioPipelineSettings":
        """Read pipeline settings. The API key is not logged."""
        raw_catalog = os.getenv("VOICESTOCK_CATALOG_PATH", "").strip()
        api_key = (
            os.getenv("VOICESTOCK_GROQ_API_KEY", "").strip()
            or os.getenv("GROQ_API_KEY", "").strip()
        )
        return cls(
            mode=os.getenv("VOICESTOCK_AUDIO_PIPELINE", STUB_MODE).strip().lower(),
            catalog_path=Path(raw_catalog) if raw_catalog else None,
            stt_model=os.getenv(
                "VOICESTOCK_STT_MODEL", "whisper-large-v3-turbo"
            ).strip(),
            llm_model=os.getenv("VOICESTOCK_LLM_MODEL", "openai/gpt-oss-20b").strip(),
            stt_timeout_seconds=_positive_float("VOICESTOCK_STT_TIMEOUT_SECONDS", "20"),
            llm_timeout_seconds=_positive_float("VOICESTOCK_LLM_TIMEOUT_SECONDS", "20"),
            api_key=api_key or None,
        )


def _positive_float(name: str, default: str) -> float:
    raw = os.getenv(name, default).strip()
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error
