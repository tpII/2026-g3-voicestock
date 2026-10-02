"""Device resolution for the sounddevice backend, without opening hardware."""

from typing import Any

import pytest

from pi.audio.errors import (
    AudioDeviceAmbiguousError,
    AudioDeviceNotFoundError,
    AudioDeviceUnsupportedError,
    AudioStreamError,
)
from pi.audio.sounddevice_backend import (
    SoundDeviceBackend,
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
    assert library.streams[0].started is True
    chunk = backend.read()
    assert chunk == b"\x00\x00" * library.opened_kwargs["blocksize"]
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
