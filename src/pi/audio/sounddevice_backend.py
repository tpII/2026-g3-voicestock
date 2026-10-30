"""PortAudio input through sounddevice.

This is the only audio module that imports sounddevice. The import happens
when a device is listed or a stream is opened, not when this module loads.

``SoundDeviceBackend`` opens ``sounddevice.RawInputStream`` with a callback.
The callback copies each PCM block into a bounded queue. ``read`` waits on
that queue. ``stop`` closes the queue before it aborts the stream, so a
blocked ``read`` returns even when ``abort`` does not unblock a PortAudio
read. WAV writing stays on the capture worker, not in the callback.

The queue holds ``PCM_QUEUE_CAPACITY`` blocks and one extra slot. The extra
slot is only for the shutdown sentinel, so ``stop`` can wake ``read`` when
every data slot is full. A block that arrives while every data slot is already
full fails the capture. It is not discarded in order to keep going.
"""

import queue
import threading
from dataclasses import dataclass
from typing import Any

from pi.audio.config import (
    CHANNELS,
    FRAMES_PER_READ,
    PCM_DTYPE,
    PCM_QUEUE_CAPACITY,
    SAMPLE_RATE_HZ,
)
from pi.audio.errors import (
    AudioCaptureError,
    AudioDeviceAmbiguousError,
    AudioDeviceNotFoundError,
    AudioDeviceUnsupportedError,
    AudioStreamError,
)

_SENTINEL = object()


@dataclass(frozen=True)
class InputDeviceInfo:
    """One input currently visible to PortAudio.

    ``name`` and ``host_api`` are the values a later settings screen can store.
    The PortAudio index is omitted because it changes across boots and machines.
    """

    name: str
    host_api: str
    max_input_channels: int
    default_samplerate: float


class _PcmBuffer:
    """Bounded queue of PCM blocks with a reserved slot for shutdown.

    Data producers never occupy the last slot. ``close`` and ``fail`` put one
    sentinel there, including when every data slot is full. ``get`` returns
    queued blocks first. It then raises the stored failure, or returns empty
    bytes when the close was a normal stop.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("PCM queue capacity must be at least 1")
        self._capacity = capacity
        self._queue: queue.Queue[bytes | object] = queue.Queue(maxsize=capacity + 1)
        self._depth = 0
        self._closed = False
        self._failure: BaseException | None = None
        self._sentinel_queued = False
        self._lock = threading.Lock()

    def put(self, block: bytes) -> None:
        with self._lock:
            if self._closed or self._failure is not None:
                return
            if self._depth >= self._capacity:
                self._failure = AudioStreamError("PCM input queue overflowed")
                self._wake_locked()
                return
            try:
                self._queue.put_nowait(block)
            except queue.Full:
                self._failure = AudioStreamError("PCM input queue overflowed")
                self._wake_locked()
                return
            self._depth += 1

    def fail(self, error: BaseException) -> None:
        with self._lock:
            if self._closed and self._failure is None:
                return
            if self._failure is None:
                self._failure = error
            self._wake_locked()

    def close(self) -> None:
        with self._lock:
            if self._sentinel_queued:
                self._closed = True
                return
            self._closed = True
            self._wake_locked()

    def get(self) -> bytes:
        item = self._queue.get()
        if item is not _SENTINEL:
            with self._lock:
                self._depth -= 1
            if not isinstance(item, bytes):
                raise AudioStreamError("PCM queue returned a non-audio block")
            return item
        with self._lock:
            failure = self._failure
            self._requeue_sentinel_locked()
        if failure is not None:
            raise failure
        return b""

    def _wake_locked(self) -> None:
        self._closed = True
        if self._sentinel_queued:
            return
        self._queue.put_nowait(_SENTINEL)
        self._sentinel_queued = True

    def _requeue_sentinel_locked(self) -> None:
        if self._sentinel_queued and self._queue.empty():
            self._queue.put_nowait(_SENTINEL)


class SoundDeviceBackend:
    """Read signed 16-bit mono PCM from a configured input device.

    The device must already accept 16 kHz, one channel, and ``int16``. This
    backend does not resample or downmix. A device that cannot be opened at
    that contract raises ``AudioDeviceUnsupportedError``. The device name is
    whatever ``input_device`` matches. No microphone is hard-coded.
    """

    def __init__(
        self,
        input_device: str,
        *,
        queue_capacity: int = PCM_QUEUE_CAPACITY,
    ) -> None:
        self._input_device = input_device
        self._queue_capacity = queue_capacity
        self._lifecycle = threading.Lock()
        self._stop_requested = threading.Event()
        self._generation = 0
        self._aborted = False
        self._stream: Any | None = None
        self._pcm: _PcmBuffer | None = None

    def start(self) -> None:
        """Resolve the configured device and open a callback input stream."""
        self.close()
        self._aborted = False
        self._stop_requested.clear()
        generation = self._generation
        library = _load_sounddevice()
        try:
            device_index = _resolve_input_device(library, self._input_device)
            _require_contract_format(library, device_index, self._input_device)
        except AudioCaptureError:
            raise
        except library.PortAudioError as exc:
            raise AudioStreamError("could not open the input stream") from exc

        pcm = _PcmBuffer(self._queue_capacity)
        self._pcm = pcm

        def callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            self._on_pcm(generation, indata, frames, time_info, status)

        def finished() -> None:
            self._on_finished(generation)

        try:
            stream = library.RawInputStream(
                samplerate=SAMPLE_RATE_HZ,
                channels=CHANNELS,
                dtype=PCM_DTYPE,
                device=device_index,
                blocksize=FRAMES_PER_READ,
                callback=callback,
                finished_callback=finished,
            )
        except library.PortAudioError as exc:
            self._pcm = None
            raise AudioStreamError("could not open the input stream") from exc
        with self._lifecycle:
            self._stream = stream
        try:
            stream.start()
        except library.PortAudioError as exc:
            self._abandon(stream)
            raise AudioStreamError("could not open the input stream") from exc

    def read(self) -> bytes:
        """Block until the next PCM block is available, or until ``stop``."""
        pcm = self._pcm
        if pcm is None:
            raise AudioStreamError("input stream is not open")
        return pcm.get()

    def stop(self) -> None:
        """Release a blocked ``read`` and stop the callback stream.

        The queue is closed first. ``abort`` does not have to unblock a
        PortAudio read, because this backend does not call ``stream.read``.
        Repeated calls are safe. A normal stop is not a capture error.
        """
        self._stop_requested.set()
        pcm = self._pcm
        if pcm is not None:
            pcm.close()
        with self._lifecycle:
            stream = self._stream
            if stream is None or self._aborted:
                return
            self._aborted = True
        abort = getattr(stream, "abort", None)
        if abort is None:
            return
        try:
            abort()
        except Exception as exc:
            library = _load_sounddevice()
            if isinstance(exc, library.PortAudioError):
                return
            raise

    def close(self) -> None:
        """Stop the stream, if needed, and release it. Safe to call again."""
        self._generation += 1
        self.stop()
        with self._lifecycle:
            stream = self._stream
            self._stream = None
        if stream is None:
            return
        closer = getattr(stream, "close", None)
        if closer is not None:
            closer()

    def _on_pcm(
        self,
        generation: int,
        indata: Any,
        frames: int,
        time_info: Any,
        status: Any,
    ) -> None:
        del frames, time_info
        if generation != self._generation or self._stop_requested.is_set():
            return
        pcm = self._pcm
        if pcm is None:
            return
        if status:
            pcm.fail(AudioStreamError(f"PortAudio reported an input status: {status}"))
            return
        try:
            block = _owned_pcm(indata)
        except Exception as exc:
            error = AudioStreamError("audio callback failed")
            error.__cause__ = exc
            pcm.fail(error)
            return
        if not block:
            return
        pcm.put(block)

    def _on_finished(self, generation: int) -> None:
        if generation != self._generation:
            return
        pcm = self._pcm
        if pcm is None:
            return
        if self._stop_requested.is_set():
            pcm.close()
            return
        pcm.fail(AudioStreamError("input stream stopped unexpectedly"))

    def _abandon(self, stream: Any) -> None:
        pcm = self._pcm
        self._pcm = None
        with self._lifecycle:
            self._stream = None
        if pcm is not None:
            pcm.close()
        closer = getattr(stream, "close", None)
        if closer is not None:
            closer()


def list_input_devices() -> list[InputDeviceInfo]:
    """Return the input devices PortAudio can see right now."""
    library = _load_sounddevice()
    try:
        devices = _input_devices(library)
    except library.PortAudioError as exc:
        raise AudioStreamError("could not query input devices") from exc
    return [
        InputDeviceInfo(
            name=device["name"],
            host_api=host_api,
            max_input_channels=device["max_input_channels"],
            default_samplerate=device["default_samplerate"],
        )
        for device, host_api in devices
    ]


def _owned_pcm(indata: Any) -> bytes:
    if isinstance(indata, bytes):
        return indata
    return bytes(indata)


def _load_sounddevice() -> Any:
    import sounddevice

    return sounddevice


def _require_contract_format(library: Any, device_index: int, query: str) -> None:
    try:
        library.check_input_settings(
            device=device_index,
            channels=CHANNELS,
            dtype=PCM_DTYPE,
            samplerate=SAMPLE_RATE_HZ,
        )
    except library.PortAudioError as exc:
        raise AudioDeviceUnsupportedError(
            f"Input device {query!r} cannot capture 16 kHz mono signed 16-bit PCM"
        ) from exc


def _resolve_input_device(library: Any, query: str) -> int:
    if not query.strip():
        raise AudioDeviceNotFoundError("Input device selector is empty")
    try:
        devices = _input_devices(library)
    except library.PortAudioError as exc:
        raise AudioStreamError("could not query input devices") from exc

    matches = [
        (device, host_api)
        for device, host_api in devices
        if _query_matches(query, device["name"], host_api)
    ]
    if not matches:
        raise AudioDeviceNotFoundError(f"No input device matches {query!r}")
    if len(matches) == 1:
        return int(matches[0][0]["index"])

    exact = [
        device
        for device, host_api in matches
        if _is_exact_name(query, device["name"], host_api)
    ]
    if len(exact) == 1:
        return int(exact[0]["index"])
    names = [device["name"] for device, _host_api in matches]
    raise AudioDeviceAmbiguousError(query, names)


def _input_devices(library: Any) -> list[tuple[dict[str, Any], str]]:
    host_apis = library.query_hostapis()
    found: list[tuple[dict[str, Any], str]] = []
    for device in library.query_devices():
        if int(device["max_input_channels"]) < 1:
            continue
        host_api = host_apis[device["hostapi"]]["name"]
        found.append((device, host_api))
    return found


def _query_matches(query: str, device_name: str, host_api: str) -> bool:
    haystack = f"{device_name}, {host_api}".lower()
    position = 0
    for part in query.lower().split():
        position = haystack.find(part, position)
        if position < 0:
            return False
        position += len(part)
    return True


def _is_exact_name(query: str, device_name: str, host_api: str) -> bool:
    normalized = query.lower()
    full_name = f"{device_name}, {host_api}".lower()
    return normalized in {device_name.lower(), full_name}
