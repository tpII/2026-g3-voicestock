"""Capture settings that deployment chooses, and the fixed PCM contract."""

from dataclasses import dataclass
from pathlib import Path

# VoiceStock output contract. These are not end-user options.
SAMPLE_RATE_HZ = 16_000
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2
PCM_DTYPE = "int16"
FRAMES_PER_READ = 1024


@dataclass(frozen=True)
class AudioCaptureConfig:
    """Where to read audio from and where to publish the finished WAV.

    ``input_device`` is a descriptive device query, not a PortAudio index.
    ``output_directory`` is where ``.recording`` and ``.wav`` files are written.
    """

    input_device: str
    output_directory: Path

    def __post_init__(self) -> None:
        output_directory = Path(self.output_directory)
        object.__setattr__(self, "output_directory", output_directory)
