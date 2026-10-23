"""Reading the WAV header of audio received by the PC server."""

import io
import wave

import pytest

from pc.communication import InvalidAudioError, read_wav


def _wav(seconds: float, sample_rate_hz: int = 16_000, channels: int = 1) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate_hz)
        wav.writeframes(b"\x00\x00" * channels * int(seconds * sample_rate_hz))
    return buffer.getvalue()


def test_header_data_is_read_and_the_file_is_kept_intact() -> None:
    content = _wav(1.5)

    audio = read_wav(content)

    assert audio.wav == content
    assert audio.duration_seconds == pytest.approx(1.5)
    assert audio.sample_rate_hz == 16_000
    assert audio.channels == 1
    assert audio.sample_width_bytes == 2


def test_other_pcm_formats_are_accepted() -> None:
    # The transport checks the container, not the push-to-talk format.
    audio = read_wav(_wav(0.5, sample_rate_hz=44_100, channels=2))

    assert (audio.sample_rate_hz, audio.channels) == (44_100, 2)


@pytest.mark.parametrize(
    "content",
    [
        b"",
        b"not a wav file",
        b"RIFF\x24\x00\x00\x00WAVE",
        _wav(1.0)[:30],
    ],
    ids=["empty", "text", "header_without_chunks", "truncated_header"],
)
def test_unreadable_wav_is_rejected(content: bytes) -> None:
    with pytest.raises(InvalidAudioError):
        read_wav(content)
