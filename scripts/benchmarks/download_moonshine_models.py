"""Download Spanish Moonshine streaming models into the ignored model directory."""

import json
from pathlib import Path

from moonshine_voice import ModelArch
from moonshine_voice.download import find_model_info, get_model_for_language

ROOT = Path(__file__).resolve().parents[2]


def main():
    root = ROOT / "models/stt/moonshine"
    root.mkdir(parents=True, exist_ok=True)
    models = {}
    for name, architecture in [
        ("moonshine_tiny_es", ModelArch.TINY_STREAMING),
        ("moonshine_small_es", ModelArch.SMALL_STREAMING),
    ]:
        path, actual = get_model_for_language(
            "es", architecture, cache_root=root, on_progress=lambda *_: None
        )
        models[name] = {
            "path": path,
            "architecture": int(actual),
            "catalog": find_model_info("es", architecture),
        }
        (root / "models.json").write_text(
            json.dumps(models, indent=2, default=int) + "\n"
        )
        print(f"{name}: {path}", flush=True)


if __name__ == "__main__":
    main()
