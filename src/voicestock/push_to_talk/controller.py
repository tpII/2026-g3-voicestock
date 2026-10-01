"""Serialize button events and drive one audio capture at a time."""

import logging
import queue
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from voicestock.audio.capture import AudioCapture
from voicestock.audio.errors import AudioCaptureError
from voicestock.push_to_talk.result import (
    CAPTURED_AUDIO_FORMAT,
    AudioCaptureResult,
    TerminationReason,
    duration_of,
)

logger = logging.getLogger(__name__)

_JOIN_TIMEOUT_SECONDS = 5.0
DEFAULT_MAX_DURATION_SECONDS = 60.0


class PushToTalkState(Enum):
    """Controller state. This is not the state inside ``AudioCapture``."""

    IDLE = "idle"
    RECORDING = "recording"
    WAITING_FOR_RELEASE = "waiting_for_release"


class _Kind(Enum):
    PRESSED = "pressed"
    RELEASED = "released"
    MAX_DURATION = "max_duration"
    SHUTDOWN = "shutdown"


@dataclass(frozen=True)
class _Event:
    kind: _Kind
    generation: int


class RecordingTimer(Protocol):
    """Arms and cancels the maximum recording duration."""

    def start(self, delay_seconds: float, callback: Callable[[], None]) -> None:
        """Invoke ``callback`` once after ``delay_seconds``, unless cancelled."""

    def cancel(self) -> None:
        """Prevent a pending callback. Extra calls do nothing."""


class ThreadingRecordingTimer:
    """``RecordingTimer`` backed by ``threading.Timer``."""

    def __init__(self) -> None:
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def start(self, delay_seconds: float, callback: Callable[[], None]) -> None:
        with self._lock:
            self._cancel_unlocked()
            timer = threading.Timer(delay_seconds, callback)
            self._timer = timer
            timer.start()

    def cancel(self) -> None:
        with self._lock:
            self._cancel_unlocked()

    def _cancel_unlocked(self) -> None:
        timer = self._timer
        self._timer = None
        if timer is not None:
            timer.cancel()


class PushToTalkController:
    """Connect press and release notifications to ``AudioCapture``.

    Button callbacks must only call ``notify_pressed`` and ``notify_released``.
    Those methods enqueue an event. A single worker starts and stops capture,
    so the button callback never blocks on audio I/O.

    ``max_duration`` limits one hold. Reaching it stops the capture, delivers
    the partial recording, and waits for release before another cycle can start.
    """

    def __init__(
        self,
        capture: AudioCapture,
        on_capture_completed: Callable[[AudioCaptureResult], None],
        on_capture_error: Callable[[AudioCaptureError], None],
        max_duration: float = DEFAULT_MAX_DURATION_SECONDS,
        timer: RecordingTimer | None = None,
    ) -> None:
        if max_duration <= 0:
            raise ValueError("max_duration must be positive")
        self._capture = capture
        self._on_capture_completed = on_capture_completed
        self._on_capture_error = on_capture_error
        self._max_duration = max_duration
        self._timer = timer if timer is not None else ThreadingRecordingTimer()
        self._state = PushToTalkState.IDLE
        self._generation = 0
        self._closed = False
        self._queue: queue.Queue[_Event] = queue.Queue()
        self._worker: threading.Thread | None = None

    @property
    def state(self) -> PushToTalkState:
        return self._state

    def start(self) -> None:
        """Start the worker that processes button and timeout events."""
        if self._closed:
            raise RuntimeError("push-to-talk controller is closed")
        if self._worker is not None:
            return
        worker = threading.Thread(
            target=self._run,
            name="voicestock-push-to-talk",
        )
        self._worker = worker
        worker.start()

    def close(self) -> None:
        """Stop the worker and cancel the recording timer.

        An in-progress recording is stopped and delivered. Artifacts already
        given to the consumer are left untouched.
        """
        if self._closed:
            return
        self._closed = True
        self._timer.cancel()
        worker = self._worker
        if worker is None:
            return
        self._queue.put(_Event(_Kind.SHUTDOWN, self._generation))
        worker.join(_JOIN_TIMEOUT_SECONDS)
        if worker.is_alive():
            raise RuntimeError("push-to-talk worker did not stop")
        self._worker = None

    def notify_pressed(self) -> None:
        """Record that the button was pressed. Safe to call from a GPIO callback."""
        self._enqueue(_Kind.PRESSED)

    def notify_released(self) -> None:
        """Record that the button was released. Safe to call from a GPIO callback."""
        self._enqueue(_Kind.RELEASED)

    def wait_until_caught_up(self, timeout: float = 2.0) -> None:
        """Block until events queued so far have been handled."""
        finished = threading.Event()

        def _join() -> None:
            self._queue.join()
            finished.set()

        threading.Thread(target=_join, daemon=True).start()
        if not finished.wait(timeout):
            raise TimeoutError("push-to-talk worker did not catch up")

    def _enqueue(self, kind: _Kind) -> None:
        if self._closed:
            return
        self._queue.put(_Event(kind, self._generation))

    def _on_timeout(self, generation: int) -> None:
        # The generation is the recording that armed this timer. A late firing
        # must not stop a later recording.
        if self._closed:
            return
        self._queue.put(_Event(_Kind.MAX_DURATION, generation))

    def _run(self) -> None:
        while True:
            event = self._queue.get()
            try:
                if event.kind is _Kind.SHUTDOWN:
                    self._shutdown_capture()
                    return
                self._dispatch(event)
            finally:
                self._queue.task_done()

    def _dispatch(self, event: _Event) -> None:
        if event.kind is _Kind.PRESSED:
            self._handle_pressed()
        elif event.kind is _Kind.RELEASED:
            self._handle_released()
        elif event.kind is _Kind.MAX_DURATION:
            self._handle_max_duration(event.generation)

    def _handle_pressed(self) -> None:
        if self._state is not PushToTalkState.IDLE:
            return
        try:
            self._capture.start()
        except AudioCaptureError as exc:
            self._state = PushToTalkState.IDLE
            self._emit_error(exc)
            return
        self._generation += 1
        self._state = PushToTalkState.RECORDING
        self._timer.start(
            self._max_duration,
            lambda generation=self._generation: self._on_timeout(generation),
        )

    def _handle_released(self) -> None:
        if self._state is PushToTalkState.WAITING_FOR_RELEASE:
            self._state = PushToTalkState.IDLE
            return
        if self._state is not PushToTalkState.RECORDING:
            return
        self._timer.cancel()
        self._finish(TerminationReason.RELEASED)

    def _handle_max_duration(self, generation: int) -> None:
        if self._state is not PushToTalkState.RECORDING:
            return
        if generation != self._generation:
            return
        self._timer.cancel()
        self._finish(TerminationReason.MAX_DURATION)

    def _shutdown_capture(self) -> None:
        self._timer.cancel()
        if self._state is PushToTalkState.RECORDING:
            self._finish(TerminationReason.RELEASED)

    def _finish(self, reason: TerminationReason) -> None:
        try:
            artifact = self._capture.stop()
            result = AudioCaptureResult(
                artifact=artifact,
                duration=duration_of(artifact),
                format=CAPTURED_AUDIO_FORMAT,
                termination_reason=reason,
            )
        except AudioCaptureError as exc:
            self._state = _state_after_failed_stop(reason)
            self._emit_error(exc)
            return
        self._state = _state_after_successful_stop(reason)
        self._emit_completed(result)

    def _emit_completed(self, result: AudioCaptureResult) -> None:
        try:
            self._on_capture_completed(result)
        except Exception:
            logger.exception(
                "push-to-talk consumer failed after a capture result was produced"
            )

    def _emit_error(self, error: AudioCaptureError) -> None:
        try:
            self._on_capture_error(error)
        except Exception:
            logger.exception("push-to-talk error consumer failed")


def _state_after_successful_stop(reason: TerminationReason) -> PushToTalkState:
    if reason is TerminationReason.MAX_DURATION:
        return PushToTalkState.WAITING_FOR_RELEASE
    return PushToTalkState.IDLE


def _state_after_failed_stop(reason: TerminationReason) -> PushToTalkState:
    if reason is TerminationReason.MAX_DURATION:
        return PushToTalkState.WAITING_FOR_RELEASE
    return PushToTalkState.IDLE
