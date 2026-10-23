"""Audio roundtrip from the Raspberry Pi client to the real PC server."""

from pathlib import Path

from pi.communication import ClientSettings, HttpInterpretationClient
from shared.communication import MAX_AUDIO_BYTES

WAV_FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures"
    / "speech_to_text"
    / "wav"
    / "habitual"
    / "corregir_cantidad.wav"
)


def _client(url: str) -> HttpInterpretationClient:
    return HttpInterpretationClient(ClientSettings(base_url=url, timeout_seconds=5))


def test_recorded_wav_reaches_the_pc_stub_handler(pc_server_url: str) -> None:
    with _client(pc_server_url) as client:
        envelope = client.interpret_audio(WAV_FIXTURE)

    assert envelope.status == "success"
    service_result = envelope.payload
    assert service_result["status"] == "success"
    received = service_result["payload"]["received_audio"]
    assert received["size_bytes"] == WAV_FIXTURE.stat().st_size
    assert received["sample_rate_hz"] == 16_000
    assert received["channels"] == 1


def test_non_wav_file_is_rejected_by_the_server(
    pc_server_url: str, tmp_path: Path
) -> None:
    text_file = tmp_path / "notes.wav"
    text_file.write_text("agregá dos paquetes de arroz", encoding="utf-8")

    with _client(pc_server_url) as client:
        envelope = client.interpret_audio(text_file)

    assert envelope.error is not None
    assert envelope.error.code == "invalid_audio"


def test_oversized_file_is_rejected_by_the_server(
    pc_server_url: str, tmp_path: Path
) -> None:
    big_file = tmp_path / "too-long.wav"
    big_file.write_bytes(b"\x00" * (MAX_AUDIO_BYTES + 1))

    with _client(pc_server_url) as client:
        envelope = client.interpret_audio(big_file)

    assert envelope.error is not None
    assert envelope.error.code == "audio_too_large"
