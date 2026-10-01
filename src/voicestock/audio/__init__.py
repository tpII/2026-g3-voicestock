"""USB microphone capture for VoiceStock.

Importing this package does not open a device. The sounddevice backend is a
separate module and is loaded only when that backend is used.
"""

from voicestock.audio.artifact import AudioArtifact
from voicestock.audio.capture import AudioCapture
from voicestock.audio.config import AudioCaptureConfig
from voicestock.audio.errors import (
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
