"""Sending push-to-talk recordings to the PC, without GPIO, microphone or network."""

import wave
from pathlib import Path

import pytest

from pi.audio.artifact import AudioArtifact
from pi.push_to_talk import (
    CAPTURED_AUDIO_FORMAT,
    AudioCaptureResult,
    PushToTalkController,
    RecordingSender,
    TerminationReason,
)
from pi.push_to_talk.manual import main as ptt_main
from shared.communication import TransportEnvelope

SUCCESS = TransportEnvelope.success({"status": "success", "payload": {}})
CONNECTION_FAILED = TransportEnvelope.failure("connection_failed", "PC unreachable")


class FakeAudioClient:
    def __init__(self, *envelopes: TransportEnvelope) -> None:
        self._envelopes = list(envelopes)
        self.sent: list[bytes] = []

    def interpret_audio(self, wav_path: Path) -> TransportEnvelope:
        # The file must still exist while it is being sent.
        self.sent.append(wav_path.read_bytes())
        return self._envelopes.pop(0)


def _write_wav(path: Path) -> Path:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16_000)
        wav.writeframes(b"\x01\x00" * 1_600)
    return path


def _result(path: Path) -> AudioCaptureResult:
    return AudioCaptureResult(
        artifact=AudioArtifact(path.stem, _write_wav(path)),
        duration=0.1,
        format=CAPTURED_AUDIO_FORMAT,
        termination_reason=TerminationReason.RELEASED,
    )


def test_recording_is_sent_and_the_answer_is_handed_over(tmp_path: Path) -> None:
    result = _result(tmp_path / "take.wav")
    client = FakeAudioClient(SUCCESS)
    sent: list[tuple[AudioCaptureResult, TransportEnvelope]] = []

    RecordingSender(client, lambda r, e: sent.append((r, e)), delete_after_send=False)(
        result
    )

    assert client.sent == [result.artifact.path.read_bytes()]
    assert sent == [(result, SUCCESS)]


@pytest.mark.parametrize("envelope", [SUCCESS, CONNECTION_FAILED])
def test_files_are_kept_unless_deletion_is_requested(
    tmp_path: Path, envelope: TransportEnvelope
) -> None:
    kept = _result(tmp_path / "kept.wav")
    deleted = _result(tmp_path / "deleted.wav")

    RecordingSender(
        FakeAudioClient(envelope), lambda r, e: None, delete_after_send=False
    )(kept)
    RecordingSender(
        FakeAudioClient(envelope), lambda r, e: None, delete_after_send=True
    )(deleted)

    assert kept.artifact.path.is_file()
    assert not deleted.artifact.path.exists()


def test_file_is_deleted_even_if_the_answer_handler_fails(tmp_path: Path) -> None:
    result = _result(tmp_path / "take.wav")

    def failing_handler(r: AudioCaptureResult, e: TransportEnvelope) -> None:
        raise RuntimeError("display failed")

    sender = RecordingSender(
        FakeAudioClient(SUCCESS), failing_handler, delete_after_send=True
    )

    with pytest.raises(RuntimeError):
        sender(result)
    assert not result.artifact.path.exists()


class OneFilePerTakeCapture:
    """AudioCapture stand-in that publishes a new WAV on every stop."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self.takes = 0

    def start(self) -> None:
        pass

    def stop(self) -> AudioArtifact:
        self.takes += 1
        path = _write_wav(self._directory / f"take-{self.takes}.wav")
        return AudioArtifact(f"take-{self.takes}", path)


class IdleTimer:
    def start(self, delay_seconds: float, callback) -> None:
        pass

    def cancel(self) -> None:
        pass


def test_a_communication_error_does_not_stop_push_to_talk(tmp_path: Path) -> None:
    client = FakeAudioClient(CONNECTION_FAILED, SUCCESS)
    answers: list[TransportEnvelope] = []
    errors: list[Exception] = []
    controller = PushToTalkController(
        OneFilePerTakeCapture(tmp_path),  # type: ignore[arg-type]
        on_capture_completed=RecordingSender(
            client, lambda r, e: answers.append(e), delete_after_send=True
        ),
        on_capture_error=errors.append,
        timer=IdleTimer(),
    )
    controller.start()
    try:
        for _ in range(2):
            controller.notify_pressed()
            controller.notify_released()
        controller.wait_until_caught_up()
    finally:
        controller.close()

    assert answers == [CONNECTION_FAILED, SUCCESS]
    assert len(client.sent) == 2
    assert errors == []
    assert list(tmp_path.iterdir()) == []


def test_delete_after_send_requires_send_to_pc(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        ptt_main(
            [
                "--pin=17",
                "--bounce-time=0.05",
                "--input-device=USB",
                "--output-directory=recordings",
                "--delete-after-send",
            ]
        )

    assert exit_info.value.code == 2
    assert "--delete-after-send requires --send-to-pc" in capsys.readouterr().err
