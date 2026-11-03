"""Device resolution for the sounddevice backend, without opening hardware."""

import threading
import wave
from pathlib import Path
from typing import Any

import pytest

from pi.audio.capture import AudioCapture
from pi.audio.config import AudioCaptureConfig
from pi.audio.errors import (
    AudioDeviceAmbiguousError,
    AudioDeviceNotFoundError,
    AudioDeviceUnsupportedError,
    AudioStreamError,
)
from pi.audio.sounddevice_backend import (
    SoundDeviceBackend,
    _PcmBuffer,
    list_input_devices,
)


class PortAudioFailure(Exception):
    """Stand-in for sounddevice.PortAudioError."""


class FakeStream:
    def __init__(self, *, fail_start: bool = False) -> None:
        self.fail_start = fail_start
        self.started = False
        self.aborted = False
        self.closed = False
        self.read_sizes: list[int] = []

    def start(self) -> None:
        if self.fail_start:
            raise PortAudioFailure("device unavailable")
        self.started = True

    def read(self, frames: int) -> tuple[bytes, bool]:
        self.read_sizes.append(frames)
        return b"\x00\x00" * frames, False

    def abort(self) -> None:
        self.aborted = True

    def close(self) -> None:
        self.closed = True


class FakeSoundDevice:
    def __init__(
        self,
        devices: list[dict[str, Any]],
        *,
        unsupported: bool = False,
        fail_open: bool = False,
        fail_start: bool = False,
    ) -> None:
        self._devices = devices
        self.unsupported = unsupported
        self.fail_open = fail_open
        self.fail_start = fail_start
        self.PortAudioError = PortAudioFailure
        self.streams: list[FakeStream] = []
        self.checked: list[dict[str, Any]] = []

    def query_devices(self) -> list[dict[str, Any]]:
        return self._devices

    def query_hostapis(self) -> list[dict[str, Any]]:
        return [{"name": "ALSA"}]

    def check_input_settings(self, **kwargs: Any) -> None:
        self.checked.append(kwargs)
        if self.unsupported:
            raise PortAudioFailure("Invalid sample rate")

    def RawInputStream(self, **kwargs: Any) -> FakeStream:
        if self.fail_open:
            raise PortAudioFailure("cannot open")
        stream = FakeStream(fail_start=self.fail_start)
        self.streams.append(stream)
        self.opened_kwargs = kwargs
        return stream


def _device(
    index: int,
    name: str,
    *,
    inputs: int = 1,
    rate: float = 48000.0,
) -> dict[str, Any]:
    return {
        "name": name,
        "index": index,
        "hostapi": 0,
        "max_input_channels": inputs,
        "default_samplerate": rate,
    }


def _patch(monkeypatch: pytest.MonkeyPatch, library: FakeSoundDevice) -> None:
    monkeypatch.setattr(
        "pi.audio.sounddevice_backend._load_sounddevice",
        lambda: library,
    )


def test_module_import_does_not_load_sounddevice() -> None:
    import sys

    assert "sounddevice" not in sys.modules


def test_resolves_a_single_name_match(monkeypatch: pytest.MonkeyPatch) -> None:
    library = FakeSoundDevice(
        [
            _device(0, "Built-in Output", inputs=0),
            _device(3, "USB Audio Device", rate=44100.0),
        ]
    )
    _patch(monkeypatch, library)
    backend = SoundDeviceBackend("usb audio")

    backend.start()

    assert library.checked[0]["device"] == 3
    assert library.checked[0]["channels"] == 1
    assert library.checked[0]["dtype"] == "int16"
    assert library.checked[0]["samplerate"] == 16000
    assert library.opened_kwargs["device"] == 3
    assert library.opened_kwargs["samplerate"] == 16000
    assert library.opened_kwargs["channels"] == 1
    assert library.opened_kwargs["dtype"] == "int16"
    assert library.opened_kwargs["blocksize"] == 1024
    assert callable(library.opened_kwargs["callback"])
    assert library.streams[0].started is True
    block = b"\x00\x00" * library.opened_kwargs["blocksize"]
    library.opened_kwargs["callback"](block, 1024, None, None)
    chunk = backend.read()
    assert chunk == block
    backend.stop()
    backend.close()
    assert library.streams[0].aborted is True
    assert library.streams[0].closed is True


def test_missing_device_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    library = FakeSoundDevice([_device(1, "USB Audio Device")])
    _patch(monkeypatch, library)

    with pytest.raises(AudioDeviceNotFoundError):
        SoundDeviceBackend("headset").start()

    assert library.streams == []


def test_ambiguous_selector_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    library = FakeSoundDevice(
        [
            _device(1, "USB Audio Device"),
            _device(2, "USB Audio Device Pro"),
        ]
    )
    _patch(monkeypatch, library)

    with pytest.raises(AudioDeviceAmbiguousError) as raised:
        SoundDeviceBackend("usb audio").start()

    assert raised.value.matches == ("USB Audio Device", "USB Audio Device Pro")
    assert library.streams == []


def test_exact_name_breaks_an_ambiguous_substring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = FakeSoundDevice(
        [
            _device(1, "USB Audio Device"),
            _device(2, "USB Audio Device Pro"),
        ]
    )
    _patch(monkeypatch, library)

    backend = SoundDeviceBackend("USB Audio Device")
    backend.start()
    backend.stop()
    backend.close()

    assert library.opened_kwargs["device"] == 1


def test_unsupported_contract_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    library = FakeSoundDevice(
        [_device(4, "USB Audio Device")],
        unsupported=True,
    )
    _patch(monkeypatch, library)

    with pytest.raises(AudioDeviceUnsupportedError):
        SoundDeviceBackend("USB Audio Device").start()

    assert library.streams == []


def test_stream_open_failure_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    library = FakeSoundDevice(
        [_device(4, "USB Audio Device")],
        fail_open=True,
    )
    _patch(monkeypatch, library)

    with pytest.raises(AudioStreamError):
        SoundDeviceBackend("USB Audio Device").start()


def test_list_input_devices_hides_outputs_and_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = FakeSoundDevice(
        [
            _device(0, "Speakers", inputs=0),
            _device(2, "USB Audio Device", rate=48000.0),
        ]
    )
    _patch(monkeypatch, library)

    devices = list_input_devices()

    assert len(devices) == 1
    assert devices[0].name == "USB Audio Device"
    assert devices[0].host_api == "ALSA"
    assert devices[0].max_input_channels == 1
    assert devices[0].default_samplerate == 48000.0
    assert not hasattr(devices[0], "index")


def _backend(
    monkeypatch: pytest.MonkeyPatch,
    name: str = "Desk Mic",
    *,
    queue_capacity: int = 4,
    **library_kwargs: Any,
) -> tuple[SoundDeviceBackend, FakeSoundDevice]:
    library = FakeSoundDevice([_device(7, name)], **library_kwargs)
    _patch(monkeypatch, library)
    return SoundDeviceBackend(name, queue_capacity=queue_capacity), library


def _callback(library: FakeSoundDevice) -> Any:
    return library.opened_kwargs["callback"]


def test_selector_is_independent_of_the_g435_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch, "Conference Mic")

    backend.start()

    assert library.opened_kwargs["device"] == 7
    assert library.opened_kwargs["samplerate"] == 16000
    assert library.opened_kwargs["channels"] == 1
    assert library.opened_kwargs["dtype"] == "int16"
    assert library.checked[0]["samplerate"] == 16000
    assert library.opened_kwargs["device"] != "voicestock_mic"
    backend.close()


def test_empty_selector_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    library = FakeSoundDevice([_device(1, "Desk Mic")])
    _patch(monkeypatch, library)

    with pytest.raises(AudioDeviceNotFoundError):
        SoundDeviceBackend("   ").start()

    assert library.streams == []


def test_query_failure_raises_stream_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenDevices(FakeSoundDevice):
        def query_devices(self) -> list[dict[str, Any]]:
            raise self.PortAudioError("alsa unavailable")

    library = BrokenDevices([_device(1, "Desk Mic")])
    _patch(monkeypatch, library)

    with pytest.raises(AudioStreamError, match="could not query input devices"):
        list_input_devices()
    with pytest.raises(AudioStreamError, match="could not query input devices"):
        SoundDeviceBackend("Desk Mic").start()


def test_close_before_start_leaves_read_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, _library = _backend(monkeypatch)
    backend.close()
    backend.close()

    with pytest.raises(AudioStreamError, match="not open"):
        backend.read()


def test_read_blocks_until_the_callback_delivers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entered = threading.Event()
    original = _PcmBuffer.get

    def wrapped(self: _PcmBuffer) -> bytes:
        entered.set()
        return original(self)

    monkeypatch.setattr(_PcmBuffer, "get", wrapped)
    backend, library = _backend(monkeypatch)
    backend.start()
    found: dict[str, bytes] = {}

    def reader() -> None:
        found["chunk"] = backend.read()

    thread = threading.Thread(target=reader)
    thread.start()
    assert entered.wait(2)
    assert thread.is_alive()
    _callback(library)(b"\x01\x02", 1, None, None)
    thread.join(2)

    assert not thread.is_alive()
    assert found["chunk"] == b"\x01\x02"
    assert library.streams[0].read_sizes == []
    backend.close()


def test_stop_unblocks_a_waiting_read(monkeypatch: pytest.MonkeyPatch) -> None:
    entered = threading.Event()
    original = _PcmBuffer.get

    def wrapped(self: _PcmBuffer) -> bytes:
        entered.set()
        return original(self)

    monkeypatch.setattr(_PcmBuffer, "get", wrapped)
    backend, library = _backend(monkeypatch)
    backend.start()
    found: dict[str, bytes] = {}

    def reader() -> None:
        found["chunk"] = backend.read()

    thread = threading.Thread(target=reader)
    thread.start()
    assert entered.wait(2)
    backend.stop()
    thread.join(2)

    assert not thread.is_alive()
    assert found["chunk"] == b""
    assert library.streams[0].aborted is True
    backend.stop()
    backend.close()
    backend.close()
    assert library.streams[0].closed is True


def test_stop_returns_queued_blocks_before_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    callback = _callback(library)
    callback(b"\x01\x00", 1, None, None)
    callback(b"\x02\x00", 1, None, None)
    backend.stop()

    assert backend.read() == b"\x01\x00"
    assert backend.read() == b"\x02\x00"
    assert backend.read() == b""
    backend.close()


def test_stop_when_the_queue_is_full(monkeypatch: pytest.MonkeyPatch) -> None:
    backend, library = _backend(monkeypatch, queue_capacity=2)
    backend.start()
    callback = _callback(library)
    callback(b"\x01\x00", 1, None, None)
    callback(b"\x02\x00", 1, None, None)
    backend.stop()
    callback(b"\x03\x00", 1, None, "input overflow")

    assert backend.read() == b"\x01\x00"
    assert backend.read() == b"\x02\x00"
    assert backend.read() == b""
    backend.close()


def test_stop_immediately_after_start_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    backend.stop()

    assert backend.read() == b""
    assert library.streams[0].aborted is True
    backend.close()


def test_sequential_sessions_use_a_new_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    _callback(library)(b"\x01\x00", 1, None, None)
    assert backend.read() == b"\x01\x00"
    backend.stop()
    backend.close()

    backend.start()
    _callback(library)(b"\x02\x00", 1, None, None)
    assert backend.read() == b"\x02\x00"
    backend.stop()
    backend.close()

    assert len(library.streams) == 2
    assert all(stream.closed for stream in library.streams)
    assert library.streams[0].read_sizes == []
    assert library.streams[1].read_sizes == []


def test_stream_start_failure_closes_and_can_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch, fail_start=True)

    with pytest.raises(AudioStreamError, match="could not open"):
        backend.start()

    assert library.streams[0].closed is True
    library.fail_start = False
    backend.start()
    _callback(library)(b"\x04\x00", 1, None, None)
    assert backend.read() == b"\x04\x00"
    backend.close()


def test_callback_failure_reaches_read(monkeypatch: pytest.MonkeyPatch) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    _callback(library)(None, 0, None, None)

    with pytest.raises(AudioStreamError, match="audio callback failed"):
        backend.read()
    backend.close()


def test_empty_callback_block_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    callback = _callback(library)
    callback(b"", 0, None, None)
    callback(b"\x01\x00", 1, None, None)

    assert backend.read() == b"\x01\x00"
    backend.close()


def test_queue_overflow_keeps_earlier_audio_then_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch, queue_capacity=1)
    backend.start()
    callback = _callback(library)
    callback(b"\x01\x00", 1, None, None)
    callback(b"\x02\x00", 1, None, None)

    assert backend.read() == b"\x01\x00"
    with pytest.raises(AudioStreamError, match="PCM input queue overflowed"):
        backend.read()
    backend.close()


def test_portaudio_status_fails_the_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    _callback(library)(b"\x01\x00", 1, None, "input overflow")

    with pytest.raises(AudioStreamError, match="input overflow"):
        backend.read()
    backend.close()


def test_status_after_stop_does_not_fail_queued_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    callback = _callback(library)
    callback(b"\x01\x00", 1, None, None)
    backend.stop()
    callback(b"\x02\x00", 1, None, "input overflow")

    assert backend.read() == b"\x01\x00"
    assert backend.read() == b""
    backend.close()


def test_unexpected_stream_stop_fails_read(monkeypatch: pytest.MonkeyPatch) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    library.opened_kwargs["finished_callback"]()

    with pytest.raises(AudioStreamError, match="stopped unexpectedly"):
        backend.read()
    backend.close()


def test_finished_callback_after_stop_is_a_normal_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, library = _backend(monkeypatch)
    backend.start()
    _callback(library)(b"\x01\x00", 1, None, None)
    backend.stop()
    library.opened_kwargs["finished_callback"]()

    assert backend.read() == b"\x01\x00"
    assert backend.read() == b""
    backend.close()


def _emit_on_start(
    library: FakeSoundDevice,
    blocks: list[bytes],
    *,
    status: Any = None,
) -> None:
    raw_input_stream = library.RawInputStream

    def raw_input_stream_with_blocks(**kwargs: Any) -> FakeStream:
        stream = raw_input_stream(**kwargs)
        start_stream = stream.start

        def start() -> None:
            start_stream()
            for block in blocks:
                kwargs["callback"](block, 1, None, status)

        stream.start = start  # type: ignore[method-assign]
        return stream

    library.RawInputStream = raw_input_stream_with_blocks  # type: ignore[method-assign]


def _wav_bytes(path: Path) -> bytes:
    with wave.open(str(path), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        return wav.readframes(wav.getnframes())


def _capture_threads() -> list[threading.Thread]:
    return [
        thread
        for thread in threading.enumerate()
        if thread.name == "voicestock-audio-capture" and thread.is_alive()
    ]


def test_audio_capture_publishes_callback_pcm(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    backend, library = _backend(monkeypatch)
    _emit_on_start(library, [b"\x01\x00\x02\x00", b"\x03\x00"])
    capture = AudioCapture(
        AudioCaptureConfig(input_device="Desk Mic", output_directory=tmp_path),
        backend,
    )
    capture.start()
    artifact = capture.stop()

    assert _capture_threads() == []
    assert library.streams[0].closed is True
    assert library.streams[0].read_sizes == []
    assert list(tmp_path.glob("*.recording")) == []
    assert _wav_bytes(artifact.path) == b"\x01\x00\x02\x00\x03\x00"


def test_audio_capture_overflow_publishes_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    backend, library = _backend(monkeypatch, queue_capacity=1)
    _emit_on_start(library, [b"\x01\x00", b"\x02\x00"])
    capture = AudioCapture(
        AudioCaptureConfig(input_device="Desk Mic", output_directory=tmp_path),
        backend,
    )
    capture.start()

    with pytest.raises(AudioStreamError, match="PCM input queue overflowed"):
        capture.stop()

    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []
    assert library.streams[0].closed is True
