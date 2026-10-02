"""Errors raised by audio capture.

Callers see these types. PortAudio and sounddevice exceptions stay inside
the sounddevice backend.
"""


class AudioCaptureError(Exception):
    """Base error for audio capture."""


class AudioCaptureStateError(AudioCaptureError):
    """The capture lifecycle does not allow this operation."""


class AudioDeviceNotFoundError(AudioCaptureError):
    """No input device matches the configured selector."""


class AudioDeviceAmbiguousError(AudioCaptureError):
    """More than one input device matches the configured selector."""

    def __init__(self, query: str, matches: list[str]) -> None:
        self.query = query
        self.matches = tuple(matches)
        listed = ", ".join(matches)
        super().__init__(f"Multiple input devices match {query!r}: {listed}")


class AudioDeviceUnsupportedError(AudioCaptureError):
    """The device cannot be opened at the VoiceStock capture contract."""


class AudioStreamError(AudioCaptureError):
    """Opening, reading, or stopping the input stream failed."""
