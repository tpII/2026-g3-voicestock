"""Download the ready-to-run Spanish Kroko ONNX model at a pinned revision."""

import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    "https://huggingface.co/csukuangfj/"
    "sherpa-onnx-streaming-zipformer-es-kroko-2025-08-06/resolve/20cf7a4/"
)


def main():
    destination = ROOT / "models/stt/kroko"
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name in ["encoder.onnx", "decoder.onnx", "joiner.onnx", "tokens.txt"]:
        target = destination / name
        temporary = destination / (name + ".part")
        urllib.request.urlretrieve(SOURCE + name, temporary)
        temporary.replace(target)
        manifest[name] = {
            "url": SOURCE + name,
            "sha256": hashlib.file_digest(target.open("rb"), "sha256").hexdigest(),
            "bytes": target.stat().st_size,
        }
        print(f"Downloaded {name}", flush=True)
    (destination / "download-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
