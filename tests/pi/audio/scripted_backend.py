"""PCM source used by capture tests. It does not touch audio hardware."""

import threading

from pi.audio.errors import AudioCaptureError


class ScriptedPcmBackend:
    """Yield scripted PCM chunks, then block until ``stop``."""

    def __init__(
        self,
        chunks: list[bytes] | None = None,
        *,
        start_error: AudioCaptureError | None = None,
        read_error: AudioCaptureError | None = None,
    ) -> None:
        self._pending = list(chunks or [])
        self._start_error = start_error
        self._read_error = read_error
        self._stop = threading.Event()
        self.drained = threading.Event()
        self.started = threading.Event()
        self.closed = threading.Event()

    def add_chunks(self, chunks: list[bytes]) -> None:
        self._pending.extend(chunks)
        self.drained.clear()

    def start(self) -> None:
        if self._start_error is not None:
            error = self._start_error
            self._start_error = None
            raise error
        self._stop.clear()
        self.closed.clear()
        self.started.set()

    def read(self) -> bytes:
        if self._read_error is not None:
            raise self._read_error
        if self._pending:
            return self._pending.pop(0)
        self.drained.set()
        self._stop.wait()
        return b""

    def stop(self) -> None:
        self._stop.set()

    def close(self) -> None:
        self._stop.set()
        self.closed.set()
