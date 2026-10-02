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


def test_importing_audio_package_does_not_load_sounddevice() -> None:
    import sys

    import pi.audio

    assert pi.audio.__name__ == "pi.audio"
    assert "sounddevice" not in sys.modules
