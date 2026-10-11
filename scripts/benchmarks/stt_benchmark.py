"""CPU STT comparison with persistent models, warm-up and resource sampling."""

from __future__ import annotations

import argparse
import array
import csv
import hashlib
import json
import os
import platform
import re
import selectors
import statistics
import subprocess
import sys
import threading
import time
import unicodedata
import wave
from importlib.metadata import version
from pathlib import Path

import psutil
from prompt_levels import LEVELS

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/speech_to_text"


def normalize(text: str) -> str:
    """Ignore case, punctuation and whitespace; preserve accents and digits."""
    text = unicodedata.normalize("NFC", text).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE).split())


def distance(reference, hypothesis) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, a in enumerate(reference, 1):
        current = [i]
        for j, b in enumerate(hypothesis, 1):
            current.append(
                min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (a != b))
            )
        previous = current
    return previous[-1]


def accuracy(reference: str, hypothesis: str) -> dict:
    ref, hyp = normalize(reference), normalize(hypothesis)
    words, chars = ref.split(), list(ref)
    word_errors = distance(words, hyp.split())
    char_errors = distance(chars, list(hyp))
    return {
        "word_errors": word_errors,
        "reference_words": len(words),
        "char_errors": char_errors,
        "reference_chars": len(chars),
        "wer_pct": 100 * word_errors / len(words) if words else None,
        "cer_pct": 100 * char_errors / len(chars) if chars else None,
        "exact_match": ref == hyp,
    }


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def vosk_worker(model: str, chunk_ms: int) -> None:
    from vosk import KaldiRecognizer, Model, SetLogLevel

    SetLogLevel(-1)
    start = time.perf_counter()
    engine = Model(model)
    print(json.dumps({"load_s": time.perf_counter() - start}), flush=True)
    for line in sys.stdin:
        try:
            with wave.open(line.strip(), "rb") as audio:
                pcm = audio.readframes(audio.getnframes())
            start = time.perf_counter()
            recognizer = KaldiRecognizer(engine, 16000)
            size = chunk_ms * 32 if chunk_ms else len(pcm)
            parts = []
            for offset in range(0, len(pcm), size):
                if recognizer.AcceptWaveform(pcm[offset : offset + size]):
                    parts.append(json.loads(recognizer.Result()).get("text", ""))
            parts.append(json.loads(recognizer.FinalResult()).get("text", ""))
            result = {
                "inference_s": time.perf_counter() - start,
                "text": " ".join(filter(None, parts)),
                "error": None,
            }
        except Exception as exc:
            result = {"error": str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)


def moonshine_worker(model: str, architecture: int) -> None:
    import numpy as np
    from moonshine_voice import ModelArch, Transcriber

    start = time.perf_counter()
    engine = Transcriber(
        model_path=model,
        model_arch=ModelArch(architecture),
        options={"ort_providers": "CPUExecutionProvider"},
    )
    print(json.dumps({"load_s": time.perf_counter() - start}), flush=True)
    for line in sys.stdin:
        try:
            samples = np.fromfile(line.strip(), dtype="<f4").tolist()
            start = time.perf_counter()
            transcript = engine.transcribe_without_streaming(samples, 16000)
            result = {
                "inference_s": time.perf_counter() - start,
                "text": " ".join(part.text for part in transcript.lines),
                "error": None,
            }
        except Exception as exc:
            result = {"error": str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)
    engine.close()


def kroko_worker(model: str, threads: int) -> None:
    import numpy as np
    import sherpa_onnx

    root = Path(model)
    start = time.perf_counter()
    engine = sherpa_onnx.OnlineRecognizer.from_transducer(
        tokens=str(root / "tokens.txt"),
        encoder=str(root / "encoder.onnx"),
        decoder=str(root / "decoder.onnx"),
        joiner=str(root / "joiner.onnx"),
        num_threads=threads,
        sample_rate=16000,
        provider="cpu",
        decoding_method="greedy_search",
        enable_endpoint_detection=False,
    )
    print(json.dumps({"load_s": time.perf_counter() - start}), flush=True)
    for line in sys.stdin:
        try:
            samples = np.fromfile(line.strip(), dtype="<f4")
            start = time.perf_counter()
            stream = engine.create_stream()
            stream.accept_waveform(16000, samples)
            # Official streaming file examples flush right context with silence.
            stream.accept_waveform(16000, np.zeros(4800, dtype=np.float32))
            stream.input_finished()
            while engine.is_ready(stream):
                engine.decode_stream(stream)
            text = engine.get_result(stream)
            result = {
                "inference_s": time.perf_counter() - start,
                "text": text,
                "error": None,
            }
        except Exception as exc:
            result = {"error": str(exc)}
        print(json.dumps(result, ensure_ascii=False), flush=True)


class Monitor:
    """Sample worker RSS only, in MiB, every 10 ms; CPU includes all threads."""

    def __init__(self, pid: int):
        self.process = psutil.Process(pid)
        self.stop = threading.Event()
        self.peak = 0
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        while not self.stop.is_set():
            try:
                self.peak = max(self.peak, self.process.memory_info().rss)
            except psutil.Error:
                break
            self.stop.wait(0.01)

    def __enter__(self):
        self.base = self.process.memory_info().rss
        self.peak = self.base
        times = self.process.cpu_times()
        self.cpu_start = times.user + times.system
        self.start = time.perf_counter()
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()
        self.wall = time.perf_counter() - self.start
        try:
            times = self.process.cpu_times()
            self.cpu = times.user + times.system - self.cpu_start
            self.peak = max(self.peak, self.process.memory_info().rss)
        except psutil.Error:
            self.cpu = None

    def metrics(self):
        return {
            "ram_base_mib": self.base / 1024**2,
            "ram_peak_mib": self.peak / 1024**2,
            "cpu_s": self.cpu,
            "cpu_pct": 100 * self.cpu / self.wall if self.cpu is not None else None,
            "request_wall_s": self.wall,
        }


def response(worker: subprocess.Popen, timeout: float) -> dict:
    with selectors.DefaultSelector() as selector:
        selector.register(worker.stdout, selectors.EVENT_READ)
        if not selector.select(timeout):
            raise TimeoutError(f"Worker exceeded {timeout}s")
    line = worker.stdout.readline()
    if not line:
        raise RuntimeError(f"Worker exited with code {worker.poll()}")
    return json.loads(line)


def read_cases():
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    for case in manifest["cases"]:
        path = FIXTURES / case["wav"]
        with wave.open(str(path), "rb") as audio:
            if (
                audio.getnchannels(),
                audio.getframerate(),
                audio.getsampwidth(),
                audio.getcomptype(),
            ) != (1, 16000, 2, "NONE"):
                raise ValueError(f"Invalid capture format: {path}")
            case["duration_s"] = audio.getnframes() / 16000
            if case["duration_s"] <= 0:
                raise ValueError(f"Empty audio: {path}")
            pcm = array.array("h", audio.readframes(audio.getnframes()))
        if sys.byteorder != "little":
            pcm.byteswap()
        samples = array.array("f", (sample / 32768 for sample in pcm))
        if sys.byteorder != "little":
            samples.byteswap()
        case["pcm_float"] = samples.tobytes()
    return manifest


def write_outputs(out: Path, rows: list, loads: list, metadata: dict):
    serial = [{k: v for k, v in row.items()} for row in rows]
    (out / "raw_transcriptions.json").write_text(
        json.dumps(serial, ensure_ascii=False, indent=2) + "\n"
    )
    if rows:
        with (out / "benchmark_runs.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    case_summaries = []
    for configuration, case_id in dict.fromkeys(
        (r["configuration"], r["case_id"]) for r in rows
    ):
        measured = [
            r
            for r in rows
            if r["configuration"] == configuration
            and r["case_id"] == case_id
            and not r["warmup"]
        ]
        ok = [r for r in measured if r["status"] == "ok"]
        item = {
            "configuration": configuration,
            "case_id": case_id,
            "level": LEVELS[case_id],
            "measured_runs": len(measured),
            "successful_runs": len(ok),
        }
        if ok:
            item.update(
                {
                    "duration_s": ok[0]["duration_s"],
                    "mean_inference_s": statistics.mean(r["inference_s"] for r in ok),
                    "mean_wer_pct": statistics.mean(r["wer_pct"] for r in ok),
                    "mean_cer_pct": statistics.mean(r["cer_pct"] for r in ok),
                    "ram_peak_mib": max(r["ram_peak_mib"] for r in ok),
                    "mean_cpu_pct": statistics.mean(r["cpu_pct"] for r in ok),
                }
            )
        case_summaries.append(item)
    if case_summaries:
        fields = list(dict.fromkeys(k for item in case_summaries for k in item))
        with (out / "benchmark_cases.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(case_summaries)
    summaries = []
    for load in loads:
        measured = [
            r
            for r in rows
            if r["configuration"] == load["configuration"] and not r["warmup"]
        ]
        ok = [r for r in measured if r["status"] == "ok"]
        summary = {
            **load,
            "measured_runs": len(measured),
            "successful_runs": len(ok),
            "failed_runs": len(measured) - len(ok),
            "expected_measured_runs": metadata["runs"]
            * len(metadata.get("audio_cases", [])),
        }
        if ok:
            summary.update(
                {
                    "wer_pct": 100
                    * sum(r["word_errors"] for r in ok)
                    / sum(r["reference_words"] for r in ok),
                    "cer_pct": 100
                    * sum(r["char_errors"] for r in ok)
                    / sum(r["reference_chars"] for r in ok),
                    "exact_match_pct": 100
                    * sum(r["exact_match"] for r in ok)
                    / len(ok),
                    "mean_inference_s": statistics.mean(r["inference_s"] for r in ok),
                    "median_inference_s": statistics.median(
                        r["inference_s"] for r in ok
                    ),
                    "max_inference_s": max(r["inference_s"] for r in ok),
                    "mean_rtf": statistics.mean(r["rtf"] for r in ok),
                    "ram_peak_mib": max(r["ram_peak_mib"] for r in ok),
                    "mean_cpu_pct": statistics.mean(r["cpu_pct"] for r in ok),
                }
            )
        summaries.append(summary)
    if summaries:
        fields = list(dict.fromkeys(k for row in summaries for k in row))
        with (out / "benchmark_summary.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(summaries)
    (out / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    report = [
        "# STT CPU benchmark",
        "",
        "PC exploration; not Raspberry Pi acceptance.",
        (
            "Reference texts are copied from the prompts "
            "and require human audio verification."
        ),
        (
            "WER/CER ignore case, punctuation and whitespace, "
            "but preserve accents and digits."
        ),
        "Numeric words versus digits count as errors under this normalization.",
        "Models remain loaded; one warm-up per audio is excluded from summaries.",
        "RAM is sampled worker RSS (MiB, 10 ms); short peaks may be missed.",
        "CPU uses process user+system time; 100% equals one fully used core.",
        (
            "WAV reading/conversion is excluded from inference_s; "
            "request_wall_s includes I/O."
        ),
        (
            "Errors are reported separately; "
            "accuracy summaries cover successful requests only."
        ),
        "",
        (
            "| Configuration | OK/total | WER % | CER % | Exact % | "
            "Mean s | RTF | RAM MiB | Load s |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in summaries:

        def fmt(key):
            value = s.get(key)
            return f"{value:.2f}" if isinstance(value, (float, int)) else "—"

        report.append(
            f"| {s['configuration']} | {s['successful_runs']}/{s['measured_runs']} | "
            + " | ".join(
                fmt(k)
                for k in [
                    "wer_pct",
                    "cer_pct",
                    "exact_match_pct",
                    "mean_inference_s",
                    "mean_rtf",
                    "ram_peak_mib",
                    "load_s",
                ]
            )
            + " |"
        )
    report += ["", "[Análisis por prompt](prompt_analysis.md)"]
    (out / "benchmark_report.md").write_text("\n".join(report) + "\n")
    from analyze_stt_benchmark import write_analysis

    write_analysis(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--vosk-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--model")
    parser.add_argument("--kroko-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--moonshine-worker", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--chunk-ms", type=int, default=250)
    parser.add_argument(
        "--configurations",
        nargs="+",
        choices=[
            "vosk_full",
            "vosk_chunks",
            "whisper_tiny",
            "whisper_base",
            "whisper_small_q5_1",
            "moonshine_tiny_es",
            "moonshine_small_es",
            "kroko_es",
        ],
        default=["vosk_full", "vosk_chunks", "whisper_tiny", "whisper_base"],
        help="Select configurations; vosk_chunks uses --chunk-ms.",
    )
    args = parser.parse_args()
    if args.kroko_worker:
        kroko_worker(args.model, args.threads)
        return
    if args.moonshine_worker is not None:
        moonshine_worker(args.model, args.moonshine_worker)
        return
    if args.vosk_worker:
        vosk_worker(args.model, args.chunk_ms)
        return
    if args.runs < 1 or args.threads < 1 or args.timeout <= 0 or args.chunk_ms <= 0:
        parser.error("runs, threads, timeout and chunk-ms must be positive")
    manifest = read_cases()
    out = ROOT / "reports/stt-benchmark" / time.strftime("cpu_%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=False)
    configurations = [
        ("vosk_full", ROOT / "models/stt/vosk/vosk-model-small-es-0.42", 0),
        (
            f"vosk_{args.chunk_ms}ms",
            ROOT / "models/stt/vosk/vosk-model-small-es-0.42",
            args.chunk_ms,
        ),
        ("whisper_tiny", ROOT / "models/stt/whisper/ggml-tiny.bin", None),
        ("whisper_base", ROOT / "models/stt/whisper/ggml-base.bin", None),
        ("whisper_small_q5_1", ROOT / "models/stt/whisper/ggml-small-q5_1.bin", None),
    ]
    configurations.append(("kroko_es", ROOT / "models/stt/kroko", None))
    moonshine_models = {}
    if any(name.startswith("moonshine_") for name in args.configurations):
        moonshine_models = json.loads(
            (ROOT / "models/stt/moonshine/models.json").read_text()
        )
        configurations.extend(
            (name, Path(info["path"]), None) for name, info in moonshine_models.items()
        )
    selected = set(args.configurations)
    configurations = [
        item
        for item in configurations
        if (
            "vosk_chunks"
            if item[0].startswith("vosk_") and item[0] != "vosk_full"
            else item[0]
        )
        in selected
    ]
    for name, model, chunk in configurations:
        if not model.exists():
            parser.error(f"Missing model for {name}: {model}")
    metadata = {
        "platform": platform.platform(),
        "python": sys.version,
        "cpu": platform.processor(),
        "logical_cpus": psutil.cpu_count(),
        "system_ram_mib": psutil.virtual_memory().total / 1024**2,
        "runs": args.runs,
        "warmups_per_audio": 1,
        "threads_whisper": args.threads,
        "vosk_threads": f"engine defaults; OMP_NUM_THREADS={args.threads}",
        "engine_versions": {"vosk": version("vosk"), "psutil": version("psutil")},
        "whisper_commit": subprocess.check_output(
            ["git", "-C", str(ROOT / ".tools/stt/whisper.cpp"), "rev-parse", "HEAD"],
            text=True,
        ).strip(),
        "audio_cases": [
            {k: v for k, v in c.items() if k != "pcm_float"} for c in manifest["cases"]
        ],
        "whisper_settings": (
            "CPU, es, greedy best_of=1, temperature=0, no fallback, no_context, no VAD"
        ),
        "manifest": {k: v for k, v in manifest.items() if k != "cases"},
        "manifest_sha256": sha256(FIXTURES / "manifest.json"),
        "vosk_chunk_ms": args.chunk_ms,
        "model_hashes": {
            name: sha256(model)
            for name, model, chunk in configurations
            if model.is_file()
        },
        "vosk_archive_sha256": sha256(
            ROOT / "models/stt/vosk/vosk-model-small-es-0.42.zip"
        ),
    }
    if moonshine_models:
        metadata["engine_versions"]["moonshine-voice"] = version("moonshine-voice")
        metadata["moonshine_settings"] = {
            "mode": "transcribe_without_streaming, complete file, flags=0, no hints",
            "provider": "CPUExecutionProvider",
            "threads": "engine defaults; OMP_NUM_THREADS=" + str(args.threads),
            "timing": (
                "includes Python-to-ctypes conversion; "
                "excludes WAV and float preparation"
            ),
        }
        metadata["moonshine_models"] = {
            name: {
                **info,
                "files": {
                    str(path.relative_to(Path(info["path"]))): {
                        "sha256": sha256(path),
                        "bytes": path.stat().st_size,
                    }
                    for path in sorted(Path(info["path"]).rglob("*"))
                    if path.is_file()
                },
            }
            for name, info in moonshine_models.items()
            if name in selected
        }
    if "kroko_es" in selected:
        metadata["engine_versions"]["sherpa-onnx"] = version("sherpa-onnx")
        metadata["kroko_settings"] = {
            "mode": "complete audio, fresh stream per request, endpoint detection off",
            "provider": "cpu",
            "num_threads": args.threads,
            "decoding": "greedy_search, no hints",
            "tail_padding_s": 0.3,
            "source": "https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-es-kroko-2025-08-06/tree/20cf7a4",
            "files": {
                path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
                for path in sorted((ROOT / "models/stt/kroko").iterdir())
                if path.is_file()
            },
        }
    rows, loads = [], []
    for name, model, chunk in configurations:
        print(f"Loading {name}...", flush=True)
        command = (
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--vosk-worker",
                "--model",
                str(model),
                "--chunk-ms",
                str(chunk),
            ]
            if chunk is not None
            else [
                str(ROOT / ".tools/stt/whisper-benchmark-worker"),
                str(model),
                str(args.threads),
            ]
        )
        if name.startswith("moonshine_"):
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--moonshine-worker",
                str(moonshine_models[name]["architecture"]),
                "--model",
                str(model),
            ]
        if name == "kroko_es":
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--kroko-worker",
                "--model",
                str(model),
                "--threads",
                str(args.threads),
            ]
        with (out / f"{name}.log").open("w") as log:
            worker = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                text=True,
                env={**os.environ, "OMP_NUM_THREADS": str(args.threads)},
            )
            try:
                with Monitor(worker.pid) as monitor:
                    load = response(worker, args.timeout)
                loads.append(
                    {
                        "configuration": name,
                        "load_s": load["load_s"],
                        "load_ram_peak_mib": monitor.peak / 1024**2,
                    }
                )
                for case in manifest["cases"]:
                    raw = out / "input.f32"
                    raw.write_bytes(case["pcm_float"])
                    path = FIXTURES / case["wav"] if chunk is not None else raw
                    for run in range(args.runs + 1):
                        row = {
                            "configuration": name,
                            "case_id": case["id"],
                            "level": LEVELS[case["id"]],
                            "run": run,
                            "warmup": run == 0,
                            "duration_s": case["duration_s"],
                            "expected_text": case["expected_text"],
                            "text": "",
                            "status": "error",
                            "error": None,
                            "inference_s": None,
                            "rtf": None,
                            "ram_base_mib": None,
                            "ram_peak_mib": None,
                            "cpu_s": None,
                            "cpu_pct": None,
                            "request_wall_s": None,
                            "word_errors": None,
                            "reference_words": None,
                            "char_errors": None,
                            "reference_chars": None,
                            "wer_pct": None,
                            "cer_pct": None,
                            "exact_match": False,
                        }
                        try:
                            with Monitor(worker.pid) as monitor:
                                worker.stdin.write(str(path) + "\n")
                                worker.stdin.flush()
                                result = response(worker, args.timeout)
                            row.update(monitor.metrics())
                            if result.get("error"):
                                raise RuntimeError(result["error"])
                            row.update(result)
                            row.update(accuracy(case["expected_text"], result["text"]))
                            row["rtf"] = row["inference_s"] / case["duration_s"]
                            row["status"] = "ok" if result["text"].strip() else "empty"
                        except Exception as exc:
                            row["error"] = str(exc)
                            if isinstance(exc, TimeoutError):
                                worker.kill()
                        rows.append(row)
                        print(
                            f"  {case['id']} run={run} {row['status']} "
                            f"time={row['inference_s']} WER={row['wer_pct']}",
                            flush=True,
                        )
                        write_outputs(out, rows, loads, metadata)
                        if worker.poll() is not None:
                            raise RuntimeError("Worker stopped; see log")
            except Exception as exc:
                print(f"{name} failed: {exc}", flush=True)
                if not any(load["configuration"] == name for load in loads):
                    loads.append(
                        {
                            "configuration": name,
                            "load_s": None,
                            "load_ram_peak_mib": None,
                            "load_error": str(exc),
                        }
                    )
            finally:
                if worker.poll() is None:
                    worker.terminate()
                try:
                    worker.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait()
                raw = out / "input.f32"
                raw.unlink(missing_ok=True)
    write_outputs(out, rows, loads, metadata)
    print(f"Results: {out}", flush=True)
    measured = [row for row in rows if not row["warmup"]]
    return int(
        len(measured) != len(configurations) * len(manifest["cases"]) * args.runs
        or any(row["status"] != "ok" for row in measured)
    )


if __name__ == "__main__":
    sys.exit(main())
