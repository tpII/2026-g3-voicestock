"""USB microphone capture for VoiceStock.

Importing this package does not open a device. The sounddevice backend is a
separate module and is loaded only when that backend is used.
"""

from pi.audio.artifact import AudioArtifact
from pi.audio.capture import AudioCapture
from pi.audio.config import AudioCaptureConfig
from pi.audio.errors import (
    AudioCaptureError,
    AudioCaptureStateError,
    AudioDeviceAmbiguousError,
    AudioDeviceNotFoundError,
    AudioDeviceUnsupportedError,
    AudioStreamError,
)

__all__ = [
    "AudioArtifact",
    "AudioCapture",
    "AudioCaptureConfig",
    "AudioCaptureError",
    "AudioCaptureStateError",
    "AudioDeviceAmbiguousError",
    "AudioDeviceNotFoundError",
    "AudioDeviceUnsupportedError",
    "AudioStreamError",
]
