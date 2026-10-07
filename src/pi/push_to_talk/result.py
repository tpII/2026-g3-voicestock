"""One finished push-to-talk cycle, independent of GPIO and speech-to-text."""

import wave
from dataclasses import dataclass
from enum import Enum

from pi.audio.artifact import AudioArtifact
from pi.audio.config import CHANNELS, SAMPLE_RATE_HZ, SAMPLE_WIDTH_BYTES
from pi.audio.errors import AudioStreamError


class TerminationReason(Enum):
    """Why a successful capture stopped.

    Capture failures are not termination reasons. They produce no result.
    """

    RELEASED = "released"
    MAX_DURATION = "max_duration"


@dataclass(frozen=True)
class AudioFormat:
    """PCM contract of a push-to-talk artifact."""

    container: str
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int


CAPTURED_AUDIO_FORMAT = AudioFormat(
    container="WAV",
    sample_rate_hz=SAMPLE_RATE_HZ,
    channels=CHANNELS,
    sample_width_bytes=SAMPLE_WIDTH_BYTES,
)


@dataclass(frozen=True)
class AudioCaptureResult:
    """Semantic result of one push-to-talk cycle.

    ``artifact`` is the file the caller now owns. ``duration`` is the length
    of that file in seconds. ``termination_reason`` says whether the button
    was released or the maximum recording time was reached.
    """

    artifact: AudioArtifact
    duration: float
    format: AudioFormat
    termination_reason: TerminationReason


def duration_of(artifact: AudioArtifact) -> float:
    """Return the duration of a published WAV, in seconds."""
    try:
        with wave.open(str(artifact.path), "rb") as wav:
            frames = wav.getnframes()
            sample_rate = wav.getframerate()
    except wave.Error as exc:
        raise AudioStreamError("captured audio is not a valid WAV file") from exc
    if sample_rate <= 0:
        raise AudioStreamError("captured audio has no sample rate")
    return frames / sample_rate
