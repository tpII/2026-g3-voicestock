"""PortAudio input through sounddevice.

This is the only audio module that imports sounddevice. The import happens
when a device is listed or a stream is opened, not when this module loads.
"""

import threading
from dataclasses import dataclass
from typing import Any

from pi.audio.config import (
    CHANNELS,
    FRAMES_PER_READ,
    PCM_DTYPE,
    SAMPLE_RATE_HZ,
)
from pi.audio.errors import (
    AudioCaptureError,
    AudioDeviceAmbiguousError,
    AudioDeviceNotFoundError,
    AudioDeviceUnsupportedError,
    AudioStreamError,
)


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


class SoundDeviceBackend:
    """Read signed 16-bit mono PCM from a configured input device.

    The device must already accept 16 kHz, one channel, and ``int16``. This
    backend does not resample or downmix. A device that cannot be opened at
    that contract raises ``AudioDeviceUnsupportedError``.
    """

    def __init__(self, input_device: str) -> None:
        self._input_device = input_device
        self._lock = threading.Lock()
        self._stop_requested = threading.Event()
        self._stream: Any | None = None

    def start(self) -> None:
        """Resolve the configured device and open a blocking input stream."""
        library = _load_sounddevice()
        self._stop_requested.clear()
        try:
            device_index = _resolve_input_device(library, self._input_device)
            _require_contract_format(library, device_index, self._input_device)
        except AudioCaptureError:
            raise
        except library.PortAudioError as exc:
            raise AudioStreamError("could not open the input stream") from exc

        try:
            stream = library.RawInputStream(
                samplerate=SAMPLE_RATE_HZ,
                channels=CHANNELS,
                dtype=PCM_DTYPE,
                device=device_index,
                blocksize=FRAMES_PER_READ,
            )
        except library.PortAudioError as exc:
            raise AudioStreamError("could not open the input stream") from exc
        try:
            stream.start()
        except library.PortAudioError as exc:
            stream.close()
            raise AudioStreamError("could not open the input stream") from exc
        with self._lock:
            self._stream = stream

    def read(self) -> bytes:
        """Block until the next PCM block is available, or until ``stop``."""
        stream = self._stream
        if stream is None:
            raise AudioStreamError("input stream is not open")
        library = _load_sounddevice()
        try:
            data, _overflowed = stream.read(FRAMES_PER_READ)
        except library.PortAudioError as exc:
            if self._stop_requested.is_set():
                return b""
            raise AudioStreamError("reading from the input stream failed") from exc
        return bytes(data)

    def stop(self) -> None:
        """Abort the stream so a blocked ``read`` returns."""
        self._stop_requested.set()
        with self._lock:
            stream = self._stream
        if stream is None:
            return
        abort = getattr(stream, "abort", None)
        if abort is None:
            return
        try:
            abort()
        except Exception as exc:
            library = _load_sounddevice()
            if not isinstance(exc, library.PortAudioError):
                raise
            if not self._stop_requested.is_set():
                raise AudioStreamError("stopping the input stream failed") from exc

    def close(self) -> None:
        """Close the stream if it is still open."""
        with self._lock:
            stream = self._stream
            self._stream = None
        if stream is None:
            return
        close = getattr(stream, "close", None)
        if close is not None:
            close()


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
