"""Push-to-talk orchestration without GPIO or a microphone."""

import threading
import wave
from pathlib import Path

import pytest

from pi.audio.artifact import AudioArtifact
from pi.audio.errors import AudioDeviceNotFoundError, AudioStreamError
from pi.push_to_talk import (
    DEFAULT_MAX_DURATION_SECONDS,
    PushToTalkController,
    PushToTalkState,
    TerminationReason,
)
from pi.push_to_talk.controller import RecordingTimer
from pi.push_to_talk.result import AudioCaptureResult


class ManualTimer:
    """Records the armed delay and fires only when the test says so."""

    def __init__(self) -> None:
        self.delay: float | None = None
        self.active = False
        self._on_fire = None

    def start(self, delay_seconds: float, callback) -> None:
        self.delay = delay_seconds
        self._on_fire = callback
        self.active = True

    def cancel(self) -> None:
        self._on_fire = None
        self.active = False

    def fire(self) -> None:
        callback = self._on_fire
        self._on_fire = None
        self.active = False
        if callback is not None:
            callback()


class FakeCapture:
    def __init__(
        self,
        artifact: AudioArtifact,
        *,
        start_error: Exception | None = None,
        stop_error: Exception | None = None,
    ) -> None:
        self.artifact = artifact
        self.start_error = start_error
        self.stop_error = stop_error
        self.start_count = 0
        self.stop_count = 0
        self.block_stop = False
        self.in_stop = threading.Event()
        self.allow_stop = threading.Event()

    def start(self) -> None:
        self.start_count += 1
        if self.start_error is not None:
            raise self.start_error

    def stop(self) -> AudioArtifact:
        if self.block_stop:
            self.in_stop.set()
            assert self.allow_stop.wait(2)
        self.stop_count += 1
        if self.stop_error is not None:
            raise self.stop_error
        return self.artifact


def _write_wav(path: Path, frames: int) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * frames)


def _workers() -> list[threading.Thread]:
    return [
        thread
        for thread in threading.enumerate()
        if thread.name == "voicestock-push-to-talk" and thread.is_alive()
    ]


@pytest.fixture
def artifact(tmp_path: Path) -> AudioArtifact:
    path = tmp_path / "take.wav"
    _write_wav(path, frames=3200)
    return AudioArtifact("take-id", path)


@pytest.fixture
def timer() -> ManualTimer:
    return ManualTimer()


def _controller(
    capture: FakeCapture,
    timer: RecordingTimer,
    results: list[AudioCaptureResult],
    errors: list[Exception],
    *,
    max_duration: float = DEFAULT_MAX_DURATION_SECONDS,
    on_completed=None,
):
    def completed(result: AudioCaptureResult) -> None:
        results.append(result)
        if on_completed is not None:
            on_completed(result)

    controller = PushToTalkController(
        capture,  # type: ignore[arg-type]
        on_capture_completed=completed,
        on_capture_error=errors.append,
        max_duration=max_duration,
        timer=timer,
    )
    controller.start()
    return controller


def test_press_then_release_delivers_one_result(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert capture.start_count == 1
    assert controller.state is PushToTalkState.RECORDING
    assert timer.delay == DEFAULT_MAX_DURATION_SECONDS
    assert timer.active is True

    controller.notify_released()
    controller.wait_until_caught_up()

    assert capture.stop_count == 1
    assert len(results) == 1
    assert results[0].artifact is artifact
    assert results[0].termination_reason is TerminationReason.RELEASED
    assert results[0].duration == 3200 / 16000
    assert results[0].format.container == "WAV"
    assert results[0].format.sample_rate_hz == 16000
    assert results[0].format.channels == 1
    assert results[0].format.sample_width_bytes == 2
    assert controller.state is PushToTalkState.IDLE
    assert timer.active is False
    assert errors == []
    assert artifact.path.is_file()
    controller.close()


def test_max_duration_keeps_partial_result_until_release(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors, max_duration=15.0)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert timer.delay == 15.0
    timer.fire()
    controller.wait_until_caught_up()

    assert capture.stop_count == 1
    assert len(results) == 1
    assert results[0].artifact is artifact
    assert results[0].termination_reason is TerminationReason.MAX_DURATION
    assert results[0].duration == 0.2
    assert controller.state is PushToTalkState.WAITING_FOR_RELEASE
    assert artifact.path.is_file()

    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert capture.start_count == 1
    assert controller.state is PushToTalkState.WAITING_FOR_RELEASE

    controller.notify_released()
    controller.wait_until_caught_up()
    assert capture.stop_count == 1
    assert len(results) == 1
    assert controller.state is PushToTalkState.IDLE
    controller.close()


def test_redundant_events_do_not_start_another_capture(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_released()
    controller.wait_until_caught_up()
    assert capture.start_count == 0
    assert controller.state is PushToTalkState.IDLE

    controller.notify_pressed()
    controller.wait_until_caught_up()
    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert capture.start_count == 1
    assert controller.state is PushToTalkState.RECORDING

    timer.fire()
    controller.wait_until_caught_up()
    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert capture.start_count == 1
    assert len(results) == 1
    assert controller.state is PushToTalkState.WAITING_FOR_RELEASE
    controller.close()


def test_start_failure_reports_error_and_stays_idle(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    failure = AudioDeviceNotFoundError("No input device matches 'missing'")
    capture = FakeCapture(artifact, start_error=failure)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()

    assert errors == [failure]
    assert results == []
    assert capture.stop_count == 0
    assert controller.state is PushToTalkState.IDLE
    assert timer.active is False
    controller.close()


def test_stop_failure_after_release_returns_to_idle(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    failure = AudioStreamError("stop failed")
    capture = FakeCapture(artifact, stop_error=failure)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    controller.notify_released()
    controller.wait_until_caught_up()

    assert errors == [failure]
    assert results == []
    assert capture.stop_count == 1
    assert controller.state is PushToTalkState.IDLE
    controller.close()


def test_stop_failure_after_max_duration_waits_for_release(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    failure = AudioStreamError("stop failed")
    capture = FakeCapture(artifact, stop_error=failure)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    timer.fire()
    controller.wait_until_caught_up()

    assert errors == [failure]
    assert results == []
    assert controller.state is PushToTalkState.WAITING_FOR_RELEASE

    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert capture.start_count == 1

    controller.notify_released()
    controller.wait_until_caught_up()
    assert controller.state is PushToTalkState.IDLE
    assert capture.stop_count == 1
    controller.close()


def test_released_before_timeout_ignores_the_later_timeout(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    late_timeout = timer._on_fire
    controller.notify_released()
    assert late_timeout is not None
    late_timeout()
    controller.wait_until_caught_up()

    assert capture.stop_count == 1
    assert len(results) == 1
    assert results[0].termination_reason is TerminationReason.RELEASED
    assert controller.state is PushToTalkState.IDLE
    controller.close()


def test_timeout_before_release_does_not_stop_twice(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    timer.fire()
    controller.notify_released()
    controller.wait_until_caught_up()

    assert capture.stop_count == 1
    assert len(results) == 1
    assert results[0].termination_reason is TerminationReason.MAX_DURATION
    assert controller.state is PushToTalkState.IDLE
    controller.close()


def test_stale_timeout_does_not_stop_the_next_recording(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    capture.block_stop = True
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    stale_timeout = timer._on_fire
    assert stale_timeout is not None

    controller.notify_released()
    assert capture.in_stop.wait(2)
    controller.notify_pressed()
    stale_timeout()
    capture.allow_stop.set()
    controller.wait_until_caught_up()

    assert capture.stop_count == 1
    assert capture.start_count == 2
    assert len(results) == 1
    assert results[0].termination_reason is TerminationReason.RELEASED
    assert controller.state is PushToTalkState.RECORDING

    capture.block_stop = False
    controller.notify_released()
    controller.wait_until_caught_up()
    assert capture.stop_count == 2
    assert len(results) == 2
    controller.close()


def test_consumer_exception_does_not_drop_the_artifact_or_the_worker(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []

    def fail(result: AudioCaptureResult) -> None:
        raise RuntimeError(f"consumer rejected {result.artifact.id}")

    controller = _controller(
        capture,
        timer,
        results,
        errors,
        on_completed=fail,
    )
    controller.notify_pressed()
    controller.wait_until_caught_up()
    controller.notify_released()
    controller.wait_until_caught_up()

    assert len(results) == 1
    assert artifact.path.is_file()
    assert controller.state is PushToTalkState.IDLE
    assert _workers()

    controller.notify_pressed()
    controller.wait_until_caught_up()
    assert capture.start_count == 2
    controller.close()
    assert _workers() == []
    assert timer.active is False


def test_close_stops_an_active_recording_and_joins_the_worker(
    artifact: AudioArtifact,
    timer: ManualTimer,
) -> None:
    capture = FakeCapture(artifact)
    results: list[AudioCaptureResult] = []
    errors: list[Exception] = []
    controller = _controller(capture, timer, results, errors)

    controller.notify_pressed()
    controller.wait_until_caught_up()
    controller.close()

    assert capture.stop_count == 1
    assert len(results) == 1
    assert results[0].termination_reason is TerminationReason.RELEASED
    assert timer.active is False
    assert _workers() == []
    assert artifact.path.is_file()

    controller.notify_pressed()
    assert capture.start_count == 1
    controller.close()
