"""JSON-lines SSH worker: run offline STT and measure Raspberry Pi resources."""

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/benchmarks"))


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def main():
    import psutil
    from stt_benchmark import Monitor

    from pi.speech_to_text import WhisperAdapter

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    directory = args.input_dir.resolve()
    model = ROOT / "models/stt/whisper/ggml-small-q5_1.bin"
    worker = ROOT / ".tools/stt/whisper-benchmark-worker"
    log = directory / "whisper.log"
    try:
        with WhisperAdapter(worker, model, args.threads, args.timeout, log) as stt:
            with Monitor(stt.worker_pid) as monitor:
                load = stt.wait_until_loaded()
            emit(
                {
                    "event": "ready",
                    "load": load,
                    "load_resources": monitor.metrics(),
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                    "python": sys.version,
                    "logical_cpus": psutil.cpu_count(),
                    "system_ram_mib": psutil.virtual_memory().total / 1024**2,
                    "model_sha256": digest(model),
                    "worker_sha256": digest(worker),
                    "threads": args.threads,
                    "remote_repo": str(ROOT),
                }
            )
            for line in sys.stdin:
                item = json.loads(line)
                if item.get("command") == "close":
                    break
                result = {"case_id": item["case_id"], "status": "error"}
                try:
                    path = (directory / item["filename"]).resolve()
                    if path.parent != directory or path.suffix != ".wav":
                        raise ValueError("Invalid input path")
                    actual = digest(path)
                    if actual != item["sha256"]:
                        raise ValueError("Audio hash mismatch")
                    with Monitor(stt.worker_pid) as monitor:
                        text = stt.transcribe(path)
                    result.update(
                        status="ok",
                        text=text,
                        audio_sha256=actual,
                        resources=monitor.metrics(),
                    )
                except Exception as exc:
                    result["error"] = str(exc)
                emit(result)
    except Exception as exc:
        emit({"event": "fatal", "error": str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
