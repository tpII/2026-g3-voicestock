"""Audio capture lifecycle without a microphone."""

import threading
import wave
from pathlib import Path

import pytest
from scripted_backend import ScriptedPcmBackend

from pi.audio import (
    AudioArtifact,
    AudioCapture,
    AudioCaptureConfig,
    AudioCaptureStateError,
    AudioDeviceNotFoundError,
    AudioStreamError,
)

_PCM_A = b"\x01\x00\x02\x00\xff\x7f\x00\x80"
_PCM_B = b"\x10\x00\x20\x00"


def _capture(tmp_path: Path, backend: ScriptedPcmBackend) -> AudioCapture:
    config = AudioCaptureConfig(
        input_device="USB Microphone",
        output_directory=tmp_path,
    )
    return AudioCapture(config, backend)


def _capture_threads() -> list[threading.Thread]:
    return [
        thread
        for thread in threading.enumerate()
        if thread.name == "voicestock-audio-capture" and thread.is_alive()
    ]


def _wav_frames(path: Path) -> tuple[int, int, int, bytes]:
    with wave.open(str(path), "rb") as wav:
        return (
            wav.getnchannels(),
            wav.getsampwidth(),
            wav.getframerate(),
            wav.readframes(wav.getnframes()),
        )


def test_start_then_stop_publishes_contract_wav(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend([_PCM_A, _PCM_B])
    capture = _capture(tmp_path, backend)

    capture.start()
    assert backend.drained.wait(2)
    recording = list(tmp_path.glob("*.recording"))
    assert len(recording) == 1
    assert list(tmp_path.glob("*.wav")) == []
    assert _capture_threads()

    artifact = capture.stop()

    assert _capture_threads() == []
    assert backend.closed.is_set()
    assert list(tmp_path.glob("*.recording")) == []
    assert artifact.path == tmp_path / f"{artifact.id}.wav"
    assert artifact.path.is_file()
    channels, width, rate, frames = _wav_frames(artifact.path)
    assert (channels, width, rate, frames) == (1, 2, 16000, _PCM_A + _PCM_B)


def test_stop_while_idle_fails(tmp_path: Path) -> None:
    capture = _capture(tmp_path, ScriptedPcmBackend())

    with pytest.raises(AudioCaptureStateError):
        capture.stop()


def test_second_start_while_recording_fails(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend()
    capture = _capture(tmp_path, backend)
    capture.start()
    assert backend.drained.wait(2)

    with pytest.raises(AudioCaptureStateError):
        capture.start()

    capture.stop()
    assert _capture_threads() == []


def test_consecutive_cycles_publish_distinct_recordings(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend([_PCM_A])
    capture = _capture(tmp_path, backend)

    capture.start()
    assert backend.drained.wait(2)
    first = capture.stop()

    backend.add_chunks([_PCM_B])
    capture.start()
    assert backend.drained.wait(2)
    second = capture.stop()

    assert first.id != second.id
    assert first.path != second.path
    assert first.path.is_file()
    assert second.path.is_file()
    assert _wav_frames(first.path)[-1] == _PCM_A
    assert _wav_frames(second.path)[-1] == _PCM_B
    assert _capture_threads() == []


def test_successful_stop_leaves_wav_until_artifact_cleanup(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend([_PCM_A])
    capture = _capture(tmp_path, backend)
    capture.start()
    assert backend.drained.wait(2)
    artifact = capture.stop()

    assert artifact.path.is_file()

    artifact.cleanup()
    assert not artifact.path.exists()
    artifact.cleanup()


def test_read_failure_publishes_nothing(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend(read_error=AudioStreamError("read failed"))
    capture = _capture(tmp_path, backend)
    capture.start()

    with pytest.raises(AudioStreamError, match="read failed"):
        capture.stop()

    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []
    with pytest.raises(AudioCaptureStateError):
        capture.stop()


def test_start_failure_leaves_no_files_and_allows_retry(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend(
        [_PCM_A],
        start_error=AudioDeviceNotFoundError("No input device matches 'missing'"),
    )
    capture = _capture(tmp_path, backend)

    with pytest.raises(AudioDeviceNotFoundError):
        capture.start()

    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []

    capture.start()
    assert backend.drained.wait(2)
    artifact = capture.stop()
    assert isinstance(artifact, AudioArtifact)
    assert artifact.path.is_file()


def test_misaligned_pcm_publishes_nothing(tmp_path: Path) -> None:
    backend = ScriptedPcmBackend([b"\x01"])
    capture = _capture(tmp_path, backend)
    capture.start()

    with pytest.raises(AudioStreamError, match="not aligned"):
        capture.stop()

    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []


def test_timed_out_worker_cannot_write_a_closed_recording(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class StuckBackend:
        def __init__(self) -> None:
            self.entered = threading.Event()
            self.release = threading.Event()
            self._session = 0
            self._passed_stuck = False
            self._gave_pcm = False
            self._stop = threading.Event()
            self.drained = threading.Event()

        def start(self) -> None:
            self._session += 1
            self._stop.clear()

        def read(self) -> bytes:
            if self._session == 1:
                if not self._passed_stuck:
                    self.entered.set()
                    self.release.wait()
                    self._passed_stuck = True
                    return b"\x01\x00"
                return b""
            if not self._gave_pcm:
                self._gave_pcm = True
                return _PCM_A
            self.drained.set()
            self._stop.wait()
            return b""

        def stop(self) -> None:
            if self._session == 1 and not self._passed_stuck:
                return
            self._stop.set()

        def close(self) -> None:
            self.close_calls += 1
            self._stop.set()

    backend = StuckBackend()
    backend.close_calls = 0
    capture = _capture(tmp_path, backend)
    capture.start()
    assert backend.entered.wait(2)
    stuck = _capture_threads()
    assert len(stuck) == 1
    monkeypatch.setattr("pi.audio.capture._WORKER_JOIN_TIMEOUT_SECONDS", 0.0)

    with pytest.raises(AudioStreamError, match="did not stop"):
        capture.stop()

    assert backend.close_calls == 1
    assert list(tmp_path.iterdir()) == []
    with pytest.raises(AudioStreamError, match="did not stop"):
        capture.start()
    assert backend.close_calls == 1
    assert list(tmp_path.iterdir()) == []
    backend.release.set()
    stuck[0].join(2)
    assert not stuck[0].is_alive()
    assert list(tmp_path.iterdir()) == []
    monkeypatch.setattr("pi.audio.capture._WORKER_JOIN_TIMEOUT_SECONDS", 5.0)

    capture.start()
    assert backend.drained.wait(2)
    artifact = capture.stop()
    assert _wav_frames(artifact.path)[-1] == _PCM_A
    assert _capture_threads() == []


def test_stop_closes_after_the_worker_exits_and_before_publish(
    tmp_path: Path,
) -> None:
    class OrderedBackend:
        def __init__(self) -> None:
            self._chunks = [_PCM_A]
            self._stop = threading.Event()
            self.events: list[str] = []
            self.read_thread: int | None = None
            self.close_thread: int | None = None
            self.worker_alive_at_close = True
            self.recording_present_at_close = False
            self.wav_present_at_close = False

        def start(self) -> None:
            self.events.append("start")
            self._stop.clear()

        def read(self) -> bytes:
            self.read_thread = threading.get_ident()
            if self._chunks:
                return self._chunks.pop(0)
            self._stop.wait()
            self.events.append("read-empty")
            return b""

        def stop(self) -> None:
            self.events.append("stop")
            self._stop.set()

        def close(self) -> None:
            self.events.append("close")
            self.close_thread = threading.get_ident()
            self.worker_alive_at_close = any(
                thread.name == "voicestock-audio-capture" and thread.is_alive()
                for thread in threading.enumerate()
            )
            self.recording_present_at_close = any(tmp_path.glob("*.recording"))
            self.wav_present_at_close = any(tmp_path.glob("*.wav"))
            self._stop.set()

    backend = OrderedBackend()
    capture = _capture(tmp_path, backend)
    capture.start()
    assert backend.events == ["close", "start"]
    artifact = capture.stop()

    assert backend.events == ["close", "start", "stop", "read-empty", "close"]
    assert backend.read_thread is not None
    assert backend.close_thread == threading.get_ident()
    assert backend.read_thread != backend.close_thread
    assert backend.worker_alive_at_close is False
    assert backend.recording_present_at_close is True
    assert backend.wav_present_at_close is False
    assert artifact.path.is_file()
    assert _wav_frames(artifact.path)[-1] == _PCM_A
    assert _capture_threads() == []


def test_startup_failure_closes_on_the_caller_and_can_retry(tmp_path: Path) -> None:
    class PartialBackend:
        def __init__(self) -> None:
            self.opened = False
            self.close_threads: list[int] = []
            self._stop = threading.Event()
            self._failed = False
            self.drained = threading.Event()

        def start(self) -> None:
            self._stop.clear()
            if not self._failed:
                self.opened = True
                self._failed = True
                raise AudioStreamError("stream start failed")

        def read(self) -> bytes:
            self.drained.set()
            self._stop.wait()
            return b""

        def stop(self) -> None:
            self._stop.set()

        def close(self) -> None:
            self.close_threads.append(threading.get_ident())
            self._stop.set()

    backend = PartialBackend()
    capture = _capture(tmp_path, backend)

    with pytest.raises(AudioStreamError, match="stream start failed"):
        capture.start()

    assert backend.opened is True
    assert backend.close_threads
    assert backend.close_threads[-1] == threading.get_ident()
    assert _capture_threads() == []
    assert list(tmp_path.iterdir()) == []

    capture.start()
    assert backend.drained.wait(2)
    artifact = capture.stop()
    assert artifact.path.is_file()
    assert _capture_threads() == []


def test_startup_timeout_does_not_close_a_live_worker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    class BlockingStart:
        def __init__(self) -> None:
            self.entered = threading.Event()
            self.release = threading.Event()
            self.stop_calls = 0
            self.close_calls = 0
            self._attempts = 0
            self._stop = threading.Event()
            self.drained = threading.Event()

        def start(self) -> None:
            self._attempts += 1
            self._stop.clear()
            if self._attempts == 1:
                self.entered.set()
                self.release.wait()
                raise AudioStreamError("start hung")
            return

        def read(self) -> bytes:
            self.drained.set()
            self._stop.wait()
            return b""

        def stop(self) -> None:
            self.stop_calls += 1
            self._stop.set()

        def close(self) -> None:
            self.close_calls += 1
            self._stop.set()

    backend = BlockingStart()
    capture = _capture(tmp_path, backend)
    real_wait = threading.Event.wait

    def wait(self: threading.Event, timeout: float | None = None) -> bool:
        if self is capture._started_event:
            assert real_wait(backend.entered, 2)
            return False
        return real_wait(self, timeout)

    monkeypatch.setattr(threading.Event, "wait", wait)
    monkeypatch.setattr("pi.audio.capture._WORKER_JOIN_TIMEOUT_SECONDS", 0.0)

    try:
        with pytest.raises(AudioStreamError, match="did not start"):
            capture.start()

        assert backend.entered.is_set()
        assert backend.stop_calls == 0
        assert backend.close_calls == 1
        assert list(tmp_path.iterdir()) == []
        with pytest.raises(AudioStreamError, match="did not stop"):
            capture.start()
        assert backend.close_calls == 1
        assert list(tmp_path.iterdir()) == []
    finally:
        monkeypatch.undo()
        backend.release.set()
        for thread in _capture_threads():
            thread.join(2)

    assert _capture_threads() == []
    capture.start()
    assert backend.drained.wait(2)
    artifact = capture.stop()
    assert artifact.path.is_file()
    assert _capture_threads() == []


def test_wav_write_failure_publishes_nothing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_write(self: AudioCapture, chunk: bytes, session: int) -> None:
        del self, chunk, session
        raise AudioStreamError("disk full")

    monkeypatch.setattr(AudioCapture, "_write_chunk", fail_write)
    backend = ScriptedPcmBackend([_PCM_A])
    capture = _capture(tmp_path, backend)
    capture.start()

    with pytest.raises(AudioStreamError, match="disk full"):
        capture.stop()

    assert backend.closed.is_set()
    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []
    with pytest.raises(AudioCaptureStateError):
        capture.stop()


def test_backend_close_failure_is_not_published(tmp_path: Path) -> None:
    class CloseFails:
        def __init__(self) -> None:
            self._chunks = [_PCM_A]
            self._stop = threading.Event()
            self.drained = threading.Event()
            self.close_calls = 0

        def start(self) -> None:
            self._stop.clear()

        def read(self) -> bytes:
            if self._chunks:
                return self._chunks.pop(0)
            self.drained.set()
            self._stop.wait()
            return b""

        def stop(self) -> None:
            self._stop.set()

        def close(self) -> None:
            self.close_calls += 1
            if self.close_calls > 1:
                raise AudioStreamError("close failed")

    backend = CloseFails()
    capture = _capture(tmp_path, backend)
    capture.start()
    assert backend.drained.wait(2)

    with pytest.raises(AudioStreamError, match="close failed"):
        capture.stop()

    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []
    with pytest.raises(AudioCaptureStateError):
        capture.stop()
    with pytest.raises(AudioStreamError, match="close failed"):
        capture.start()
    assert list(tmp_path.iterdir()) == []


def test_unexpected_read_error_publishes_nothing(tmp_path: Path) -> None:
    class BrokenRead:
        def __init__(self) -> None:
            self._stop = threading.Event()
            self.closed = threading.Event()

        def start(self) -> None:
            self._stop.clear()
            self.closed.clear()

        def read(self) -> bytes:
            raise RuntimeError("backend exploded")

        def stop(self) -> None:
            self._stop.set()

        def close(self) -> None:
            self.closed.set()

    backend = BrokenRead()
    capture = _capture(tmp_path, backend)
    capture.start()

    with pytest.raises(AudioStreamError, match="audio capture failed"):
        capture.stop()

    assert backend.closed.is_set()
    assert list(tmp_path.iterdir()) == []
    assert _capture_threads() == []


def test_importing_audio_package_does_not_load_sounddevice() -> None:
    import sys

    import pi.audio

    assert pi.audio.__name__ == "pi.audio"
    assert "sounddevice" not in sys.modules
