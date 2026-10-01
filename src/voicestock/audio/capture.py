"""Record PCM from a backend into a published WAV file."""

import os
import threading
import uuid
import wave
from enum import Enum
from pathlib import Path

from voicestock.audio.artifact import AudioArtifact
from voicestock.audio.backend import AudioInputBackend
from voicestock.audio.config import (
    CHANNELS,
    SAMPLE_RATE_HZ,
    SAMPLE_WIDTH_BYTES,
    AudioCaptureConfig,
)
from voicestock.audio.errors import (
    AudioCaptureError,
    AudioCaptureStateError,
    AudioStreamError,
)

_WORKER_JOIN_TIMEOUT_SECONDS = 5.0


class _State(Enum):
    IDLE = "idle"
    RECORDING = "recording"


class AudioCapture:
    """Start and stop one recording at a time.

    Construction does not open a device. ``start`` asks the backend for PCM
    and a worker writes each chunk to a temporary ``.recording`` file. ``stop``
    finalizes that file and, only when it is a valid WAV, renames it to
    ``.wav`` and returns an ``AudioArtifact``. The caller then owns the file.
    """

    def __init__(
        self,
        config: AudioCaptureConfig,
        backend: AudioInputBackend,
    ) -> None:
        self._config = config
        self._backend = backend
        self._state = _State.IDLE
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._started_event = threading.Event()
        self._stop_in_progress = False
        self._worker: threading.Thread | None = None
        self._startup_error: BaseException | None = None
        self._worker_error: BaseException | None = None
        self._wav: wave.Wave_write | None = None
        self._artifact_id: str | None = None
        self._recording_path: Path | None = None
        self._final_path: Path | None = None

    def start(self) -> None:
        """Begin a new recording.

        Raises:
            AudioCaptureStateError: a recording is already in progress.
        """
        with self._lock:
            if self._state is not _State.IDLE:
                raise AudioCaptureStateError(
                    "cannot start audio capture while it is already recording"
                )
            try:
                self._open_temp_file()
            except Exception:
                self._discard_temp()
                raise
            self._stop_event.clear()
            self._started_event.clear()
            self._startup_error = None
            self._worker_error = None
            self._state = _State.RECORDING
            worker = threading.Thread(
                target=self._run,
                name="voicestock-audio-capture",
            )
            self._worker = worker
            worker.start()

        if not self._started_event.wait(_WORKER_JOIN_TIMEOUT_SECONDS):
            self._stop_event.set()
            self._release_backend()
            worker.join(_WORKER_JOIN_TIMEOUT_SECONDS)
            self._fail(AudioStreamError("audio capture did not start"))

        if self._startup_error is not None:
            worker.join(_WORKER_JOIN_TIMEOUT_SECONDS)
            self._fail(self._startup_error)

    def stop(self) -> AudioArtifact:
        """Finish the recording and transfer the WAV to the caller.

        Raises:
            AudioCaptureStateError: there is no recording in progress.
            AudioCaptureError: the recording failed before a valid WAV existed.
        """
        with self._lock:
            if self._state is not _State.RECORDING or self._stop_in_progress:
                raise AudioCaptureStateError(
                    "cannot stop audio capture when it is idle"
                )
            self._stop_in_progress = True
            worker = self._worker
            self._stop_event.set()

        self._unblock_backend()
        if worker is not None:
            worker.join(_WORKER_JOIN_TIMEOUT_SECONDS)
            if worker.is_alive():
                self._fail(AudioStreamError("audio capture worker did not stop"))

        if self._worker_error is not None:
            self._fail(self._worker_error)

        try:
            artifact = self._publish()
        except AudioCaptureError as exc:
            self._fail(exc)

        with self._lock:
            self._state = _State.IDLE
            self._stop_in_progress = False
            self._worker = None
        return artifact

    def _run(self) -> None:
        try:
            self._backend.start()
        except Exception as exc:
            self._startup_error = exc
            self._started_event.set()
            self._release_backend()
            return

        self._started_event.set()
        try:
            while not self._stop_event.is_set():
                chunk = self._backend.read()
                if chunk:
                    self._write_chunk(chunk)
        except Exception as exc:
            self._worker_error = exc
        finally:
            self._release_backend()

    def _write_chunk(self, chunk: bytes) -> None:
        frame_bytes = SAMPLE_WIDTH_BYTES * CHANNELS
        if len(chunk) % frame_bytes != 0:
            raise AudioStreamError(
                "PCM chunk is not aligned to signed 16-bit mono frames"
            )
        if self._wav is None:
            raise AudioStreamError("audio capture has no open recording")
        self._wav.writeframes(chunk)

    def _open_temp_file(self) -> None:
        directory = self._config.output_directory
        directory.mkdir(parents=True, exist_ok=True)
        artifact_id = str(uuid.uuid4())
        recording_path = directory / f"{artifact_id}.recording"
        self._artifact_id = artifact_id
        self._recording_path = recording_path
        self._final_path = directory / f"{artifact_id}.wav"
        wav = wave.open(str(recording_path), "wb")
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_WIDTH_BYTES)
        wav.setframerate(SAMPLE_RATE_HZ)
        self._wav = wav

    def _publish(self) -> AudioArtifact:
        self._close_wav()
        recording = self._recording_path
        final = self._final_path
        artifact_id = self._artifact_id
        if recording is None or final is None or artifact_id is None:
            raise AudioStreamError("audio capture has no recording to publish")
        try:
            _validate_wav(recording)
            os.replace(recording, final)
            _validate_wav(final)
        except AudioCaptureError:
            final.unlink(missing_ok=True)
            recording.unlink(missing_ok=True)
            raise
        except Exception as exc:
            final.unlink(missing_ok=True)
            recording.unlink(missing_ok=True)
            raise AudioStreamError("audio capture failed to publish") from exc
        self._recording_path = None
        self._final_path = None
        self._artifact_id = None
        return AudioArtifact(artifact_id, final)

    def _fail(self, error: BaseException) -> None:
        self._discard_temp()
        with self._lock:
            self._state = _State.IDLE
            self._stop_in_progress = False
            self._worker = None
            self._startup_error = None
            self._worker_error = None
        if isinstance(error, AudioCaptureError):
            raise error
        raise AudioStreamError("audio capture failed") from error

    def _discard_temp(self) -> None:
        self._close_wav()
        recording = self._recording_path
        final = self._final_path
        self._recording_path = None
        self._final_path = None
        self._artifact_id = None
        for path in (recording, final):
            if path is not None:
                path.unlink(missing_ok=True)

    def _close_wav(self) -> None:
        wav = self._wav
        self._wav = None
        if wav is not None:
            wav.close()

    def _unblock_backend(self) -> None:
        try:
            self._backend.stop()
        except Exception as exc:
            if self._worker_error is None and self._startup_error is None:
                self._worker_error = exc

    def _release_backend(self) -> None:
        self._unblock_backend()
        try:
            self._backend.close()
        except Exception as exc:
            if self._worker_error is None and self._startup_error is None:
                self._worker_error = exc


def _validate_wav(path: Path) -> None:
    try:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
    except wave.Error as exc:
        raise AudioStreamError("captured audio is not a valid WAV file") from exc
    if (
        channels != CHANNELS
        or sample_width != SAMPLE_WIDTH_BYTES
        or sample_rate != SAMPLE_RATE_HZ
    ):
        raise AudioStreamError(
            "captured audio does not match the 16 kHz mono 16-bit PCM contract"
        )
