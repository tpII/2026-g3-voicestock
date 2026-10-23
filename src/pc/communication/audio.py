"""Audio received by the PC server and the handler that consumes it."""

import io
import wave
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class InvalidAudioError(ValueError):
    """The request body is not a WAV file the server can read."""


@dataclass(frozen=True, slots=True)
class ReceivedAudio:
    """One WAV file received from the Raspberry Pi, with its header data.

    ``wav`` is the complete file exactly as it arrived, ready to be sent to a
    transcription API. The other fields come from the WAV header; the server
    reads them but does not require a particular format.
    """

    wav: bytes
    duration_seconds: float
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int


AudioHandler = Callable[[ReceivedAudio], Any]


def read_wav(content: bytes) -> ReceivedAudio:
    """Read the WAV header of ``content`` or raise ``InvalidAudioError``."""
    try:
        with wave.open(io.BytesIO(content), "rb") as wav:
            frames = wav.getnframes()
            sample_rate_hz = wav.getframerate()
            channels = wav.getnchannels()
            sample_width_bytes = wav.getsampwidth()
    except (wave.Error, EOFError) as error:
        raise InvalidAudioError("body is not a readable WAV file") from error
    if sample_rate_hz <= 0:
        raise InvalidAudioError("WAV header has no sample rate")

    return ReceivedAudio(
        wav=content,
        duration_seconds=frames / sample_rate_hz,
        sample_rate_hz=sample_rate_hz,
        channels=channels,
        sample_width_bytes=sample_width_bytes,
    )
