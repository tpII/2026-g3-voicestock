"""Offline speech-to-text adapters consuming already captured audio."""

from pi.speech_to_text.contracts import SpeechToText, TranscriptionError
from pi.speech_to_text.whisper_adapter import WhisperAdapter

__all__ = ["SpeechToText", "TranscriptionError", "WhisperAdapter"]
