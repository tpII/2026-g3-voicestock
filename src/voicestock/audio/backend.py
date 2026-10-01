"""Boundary between capture lifecycle and a PCM source."""

from typing import Protocol


class AudioInputBackend(Protocol):
    """PCM source used by ``AudioCapture``.

    ``start`` opens the source. ``read`` blocks until the next chunk or until
    ``stop`` unblocks it. ``close`` releases the source. ``stop`` and ``close``
    are safe to call more than once.
    """

    def start(self) -> None:
        """Open the source and begin producing PCM."""

    def read(self) -> bytes:
        """Return the next interleaved PCM chunk, or empty bytes when stopped."""

    def stop(self) -> None:
        """Unblock ``read`` and stop producing PCM."""

    def close(self) -> None:
        """Release the source."""
