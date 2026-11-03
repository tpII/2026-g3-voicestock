"""Speech-to-text adapters used by the PC."""

from pc.speech_to_text.errors import TranscriptionError, TranscriptionFailure
from pc.speech_to_text.groq import DEFAULT_STT_MODEL, GroqWhisperTranscriber

__all__ = [
    "DEFAULT_STT_MODEL",
    "GroqWhisperTranscriber",
    "TranscriptionError",
    "TranscriptionFailure",
]
