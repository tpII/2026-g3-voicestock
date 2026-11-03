"""Failures of a speech-to-text adapter.

These errors stay inside the adapter boundary. The audio pipeline maps them
to service results and does not let the original exception reach HTTP.
"""

from enum import StrEnum


class TranscriptionFailure(StrEnum):
    """Why a transcription request did not produce usable text."""

    EMPTY = "empty"
    TIMEOUT = "timeout"
    FAILED = "failed"
    NOT_CONFIGURED = "not_configured"


class TranscriptionError(Exception):
    """Expected transcription failure with a stable kind and a safe detail."""

    def __init__(self, kind: TranscriptionFailure, detail: str) -> None:
        self.kind = kind
        super().__init__(detail)
