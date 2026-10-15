"""Engine-independent boundary for already captured audio."""

from pathlib import Path
from typing import Protocol


class TranscriptionError(Exception):
    """Invalid audio, unavailable engine or failed transcription."""


class SpeechToText(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        """Transcribe WAV PCM16 mono 16 kHz without capturing audio."""
        ...
