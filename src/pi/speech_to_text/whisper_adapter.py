"""Persistent CPU whisper.cpp worker behind the audio-to-text boundary."""

import array
import json
import selectors
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from pi.speech_to_text.contracts import TranscriptionError


class WhisperAdapter:
    """Sequential requests; create one instance and reuse its loaded model."""

    def __init__(
        self,
        worker_path: Path,
        model_path: Path,
        threads: int = 4,
        timeout: float = 600,
        log_path: Path | None = None,
    ):
        if threads < 1 or timeout <= 0:
            raise ValueError("threads and timeout must be positive")
        if not worker_path.is_file() or not model_path.is_file():
            raise TranscriptionError("Whisper worker or model not installed")
        self._timeout = timeout
        self._log = (
            log_path.open("w") if log_path else tempfile.TemporaryFile(mode="w+")
        )
        self._temporary = tempfile.TemporaryDirectory(prefix="voicestock-stt-")
        self._worker = None
        try:
            self._worker = subprocess.Popen(
                [str(worker_path.resolve()), str(model_path.resolve()), str(threads)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._log,
                text=True,
            )
        except Exception:
            self.close()
            raise

    @property
    def worker_pid(self) -> int:
        """Worker PID for external resource instrumentation."""
        if self._worker is None:
            raise TranscriptionError("Whisper is closed")
        return self._worker.pid

    def wait_until_loaded(self):
        """Read the initial load event once, before the first transcription."""
        if not hasattr(self, "load_result"):
            self.load_result = self._response()
        return self.load_result

    def _response(self):
        if self._worker is None:
            raise TranscriptionError("Whisper is closed")
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self._worker.stdout, selectors.EVENT_READ)
                if not selector.select(self._timeout):
                    self.close()
                    raise TranscriptionError("Whisper request timed out")
            line = self._worker.stdout.readline()
            if not line:
                raise TranscriptionError("Whisper worker exited")
            result = json.loads(line)
            if result.get("error"):
                raise TranscriptionError(result["error"])
            return result
        except (ValueError, OSError) as exc:
            raise TranscriptionError("Invalid Whisper worker response") from exc

    def transcribe(self, audio_path: Path) -> str:
        self.wait_until_loaded()
        try:
            with wave.open(str(audio_path), "rb") as audio:
                if (
                    audio.getnchannels(),
                    audio.getframerate(),
                    audio.getsampwidth(),
                    audio.getcomptype(),
                ) != (1, 16000, 2, "NONE"):
                    raise TranscriptionError("Expected WAV PCM16 mono 16000 Hz")
                if audio.getnframes() == 0:
                    raise TranscriptionError("Empty audio")
                samples = array.array("h", audio.readframes(audio.getnframes()))
            if sys.byteorder != "little":
                samples.byteswap()
            floats = array.array("f", (sample / 32768 for sample in samples))
            if sys.byteorder != "little":
                floats.byteswap()
            path = Path(self._temporary.name) / "input.f32"
            path.write_bytes(floats.tobytes())
            self._worker.stdin.write(str(path) + "\n")
            self._worker.stdin.flush()
            result = self._response()
            text = result.get("text")
            if not isinstance(text, str) or not text.strip():
                raise TranscriptionError("Empty transcription")
            return text.strip()
        except (wave.Error, OSError, EOFError) as exc:
            raise TranscriptionError("Unable to read audio or call Whisper") from exc

    def close(self):
        worker = self._worker
        if worker is not None:
            if worker.poll() is None:
                worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait()
            for stream in [worker.stdin, worker.stdout]:
                if stream:
                    stream.close()
            self._worker = None
        self._log.close()
        self._temporary.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
