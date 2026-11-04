"""Preserve recorded originals and produce canonical PTT WAV evaluation inputs."""

import argparse
import hashlib
import json
import shutil
import wave
from pathlib import Path

import av
from prompt_levels import LEVELS, prompt_path

ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT / "tests/fixtures/speech_to_text"
CASES = {
    "Solo_agregar": "solo_agregar",
    "Solo_restar": "solo_restar",
    "Restar_ambos": "restar_ambos",
    "Corregir-cantidad": "corregir_cantidad",
    "Negar_agregaciones": "negar_agregacion",
    "Negar_restaciones": "negar_restacion",
    "Negar_varias_agregaciones": "negar_varias_agregaciones",
    "Negar_varias_restaciones": "negar_varias_restaciones",
    "Negar_agregacion_y_restacion": "negar_agregacion_y_restacion",
    "Caso_integral": "caso_integral",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "audio-prompts")
    args = parser.parse_args()
    originals = DESTINATION / "originals"
    originals.mkdir(parents=True, exist_ok=True)
    (DESTINATION / "wav").mkdir(exist_ok=True)
    cases = []
    for source_name, case_id in CASES.items():
        level = LEVELS[case_id]
        original = originals / level / f"{case_id}.m4a"
        original.parent.mkdir(parents=True, exist_ok=True)
        source = args.source / f"{source_name}.m4a"
        if source.exists():
            if original.exists():
                raise FileExistsError(original)
            shutil.move(source, original)
        if not original.exists():
            raise FileNotFoundError(original)
        target = DESTINATION / "wav" / level / f"{case_id}.wav"
        target.parent.mkdir(parents=True, exist_ok=True)
        with (
            av.open(str(original)) as container,
            wave.open(str(target), "wb") as output,
        ):
            stream = container.streams.audio[0]
            source_info = {
                "rate": stream.codec_context.sample_rate,
                "layout": stream.codec_context.layout.name,
            }
            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            for frame in container.decode(stream):
                for converted in resampler.resample(frame):
                    output.writeframes(
                        bytes(converted.planes[0])[: converted.samples * 2]
                    )
            for converted in resampler.resample(None):
                output.writeframes(bytes(converted.planes[0])[: converted.samples * 2])
        with wave.open(str(target), "rb") as audio:
            duration = audio.getnframes() / audio.getframerate()
        prompt = prompt_path(ROOT / "scripts/benchmarks/prompts/precision", case_id)
        cases.append(
            {
                "id": case_id,
                "level": level,
                "text_prompt": str(prompt.relative_to(ROOT)),
                "original": str(original.relative_to(DESTINATION)),
                "wav": str(target.relative_to(DESTINATION)),
                "source_audio": source_info,
                "duration_s": duration,
                "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                "wav_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "expected_text": prompt.read_text().strip(),
                "reference_verified_by_human": False,
            }
        )
        print(f"{case_id}: {duration:.2f} seconds", flush=True)
    manifest = {
        "format": "WAV PCM signed 16-bit mono 16000 Hz",
        "reference_source": "LLM precision prompts; human verification pending",
        "converter": f"PyAV {av.__version__}",
        "cases": cases,
    }
    (DESTINATION / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    if args.source.exists() and not any(args.source.iterdir()):
        args.source.rmdir()


if __name__ == "__main__":
    main()
