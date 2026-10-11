"""Single-pass basic/habitual audio -> Whisper Small Q5 -> local Qwen -> JSON."""

import argparse
import csv
import json
import os
import platform
import subprocess
import threading
import time
import urllib.request

import psutil
from precision_benchmark import (
    CASES,
    JSON_SCHEMA,
    OLLAMA_MODEL,
    OLLAMA_URL,
    PrecisionCase,
    evaluate,
    prompt_for,
)
from prompt_levels import LEVELS
from stt_benchmark import FIXTURES, ROOT, read_cases, response, sha256


def http_json(endpoint, payload=None, timeout=600):
    request = urllib.request.Request(
        OLLAMA_URL + endpoint,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as stream:
        return json.load(stream)


class MemorySampler:
    """Sample separate components and simultaneous summed RSS every 10 ms."""

    def __init__(self, whisper_pid):
        self.whisper_pid = whisper_pid
        self.stop = threading.Event()
        self.samples = []
        self.errors = set()
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def snapshot(self):
        whisper = psutil.Process(self.whisper_pid).memory_info().rss
        ollama = 0
        pids = []
        for process in psutil.process_iter(["pid", "name"]):
            name = (process.info["name"] or "").lower()
            if name == "ollama" or name.startswith("ollama_") or name == "llama-server":
                try:
                    ollama += process.memory_info().rss
                    pids.append(process.pid)
                except psutil.NoSuchProcess:
                    continue
                except psutil.AccessDenied:
                    self.errors.add(f"RAM access denied: {process.pid}")
        return {
            "whisper_mib": whisper / 1024**2,
            "ollama_mib": ollama / 1024**2,
            "combined_mib": (whisper + ollama) / 1024**2,
            "ollama_pids": pids,
        }

    def sample(self):
        while not self.stop.is_set():
            try:
                self.samples.append(self.snapshot())
            except psutil.Error as exc:
                self.errors.add(str(exc))
            self.stop.wait(0.01)

    def __enter__(self):
        self.samples.append(self.snapshot())
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()
        self.samples.append(self.snapshot())

    def metrics(self):
        return {
            "before": self.samples[0],
            "after": self.samples[-1],
            "peak_whisper_mib": max(s["whisper_mib"] for s in self.samples),
            "peak_ollama_mib": max(s["ollama_mib"] for s in self.samples),
            "peak_combined_mib": max(s["combined_mib"] for s in self.samples),
            "samples": len(self.samples),
            "errors": sorted(self.errors),
        }


def save(out, rows, environment):
    (out / "results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    (out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n"
    )
    flat = []
    for row in rows:
        stt = row.get("stt_ram", {})
        llm = row.get("llm_ram", {})
        flat.append(
            {
                "case_id": row["case_id"],
                "level": row["level"],
                "status": row["status"],
                **row.get("evaluation", {}),
                "stt_peak_mib": stt.get("peak_whisper_mib"),
                "llm_peak_mib": llm.get("peak_ollama_mib"),
                "simultaneous_peak_mib": max(
                    stt.get("peak_combined_mib") or 0,
                    llm.get("peak_combined_mib") or 0,
                )
                or None,
                "transcription": row.get("transcription", ""),
                "raw_json": row.get("raw_response", ""),
            }
        )
    if flat:
        fields = list(dict.fromkeys(key for row in flat for key in row))
        with (out / "benchmark_cases.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(flat)
    correct = sum(r.get("evaluation", {}).get("exact_match", False) for r in rows)
    report = [
        "# Audio → STT → LLM → JSON",
        "",
        f"Whisper Small Q5_1 → {environment['llm_model']}. "
        "Una corrida por prompt, sin calentamiento, reintentos ni corrección manual.",
        "El LLM recibe la transcripción, el contrato y el catálogo existentes; "
        "no recibe el texto esperado ni el JSON de referencia.",
        "Temperatura 0, think=false, formato JSON_SCHEMA. "
        "El esquema garantiza estructura, no contenido correcto.",
        "RSS en MiB cada 10 ms. Whisper: proceso trabajador; "
        "Qwen: suma de procesos Ollama (servidor y runner). "
        "Whisper permanece cargado mientras Qwen procesa. "
        "La suma de RSS puede contar páginas compartidas varias veces; "
        "no representa memoria física exclusiva ni VRAM. "
        "La primera solicitud incluye la carga de Qwen si no estaba residente.",
        "Referencias pendientes de verificación escuchando el audio. "
        "No se modificó inventario ni se aplicaron las operaciones generadas.",
        "",
        "**Cobertura RAM:** "
        + environment.get("ram_measurement_note", "Full sampling."),
        "",
        f"**JSON exacto esperado: {correct}/{len(rows)} casos procesados.**",
        "",
        "| Caso | Nivel | JSON exacto | Whisper MiB | Ollama MiB | "
        "Pico simultáneo MiB |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in flat:

        def fmt(key):
            value = row.get(key)
            return f"{value:.1f}" if value is not None else "—"

        report.append(
            f"| {row['case_id']} | {row['level']} | "
            f"{row.get('exact_match', False)} | {fmt('stt_peak_mib')} | "
            f"{fmt('llm_peak_mib')} | {fmt('simultaneous_peak_mib')} |"
        )
    for row in rows:
        report += [
            "",
            f"## {row['case_id']}",
            "",
            "**Texto esperado:** " + row["reference_text"],
            "",
            "**Transcripción recibida por Qwen:** " + row.get("transcription", ""),
            "",
            "**JSON esperado:**",
            "```json",
            json.dumps(row["expected_json"], ensure_ascii=False, indent=2),
            "```",
            "",
            "**Salida real:**",
            "```json",
            row.get("raw_response", ""),
            "```",
            "",
            "**Evaluación:** " + json.dumps(row.get("evaluation", {})),
            "**Error:** " + str(row.get("error")),
        ]
    (out / "benchmark_report.md").write_text("\n".join(report) + "\n")


def main():
    from api_keys import load_api_keys

    load_api_keys()

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    if args.threads < 1 or args.timeout <= 0:
        parser.error("threads and timeout must be positive")
    tags = http_json("/api/tags")
    if OLLAMA_MODEL not in {m["name"] for m in tags["models"]}:
        raise RuntimeError(f"Missing installed model: {OLLAMA_MODEL}")
    resident = http_json("/api/ps")
    if any(m["name"] != OLLAMA_MODEL for m in resident["models"]):
        raise RuntimeError("Other models loaded: cannot attribute Ollama RSS to Qwen")
    model = ROOT / "models/stt/whisper/ggml-small-q5_1.bin"
    out = ROOT / "reports/audio-stt-llm" / time.strftime("run_%Y%m%d_%H%M%S")
    out.mkdir(parents=True)
    manifest = read_cases()
    selected = [c for c in manifest["cases"] if LEVELS[c["id"]] != "exigente"]
    expected = {c.case_id: c for c in CASES}
    environment = {
        "platform": platform.platform(),
        "python": os.sys.version,
        "llm_model": OLLAMA_MODEL,
        "ollama_tags": tags,
        "ollama_initial_resident": resident,
        "whisper_sha256": sha256(model),
        "threads_whisper": args.threads,
        "whisper_settings": "es, CPU, greedy, temperature=0, no_context, no VAD",
        "whisper_commit": subprocess.check_output(
            ["git", "-C", str(ROOT / ".tools/stt/whisper.cpp"), "rev-parse", "HEAD"],
            text=True,
        ).strip(),
        "manifest_sha256": sha256(FIXTURES / "manifest.json"),
        "contract_sha256": sha256(
            ROOT / "scripts/benchmarks/prompts/precision/contract.txt"
        ),
        "audio_cases": [
            {k: v for k, v in c.items() if k != "pcm_float"} for c in selected
        ],
        "runs_per_case": 1,
        "warmups": 0,
        "retries": 0,
        "llm_settings": {
            "format": JSON_SCHEMA,
            "think": False,
            "temperature": 0,
            "keep_alive": "10m",
        },
    }
    rows = []
    with (out / "whisper.log").open("w") as log:
        worker = subprocess.Popen(
            [
                str(ROOT / ".tools/stt/whisper-benchmark-worker"),
                str(model),
                str(args.threads),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log,
            text=True,
        )
        try:
            with MemorySampler(worker.pid) as sampler:
                response(worker, args.timeout)
            environment["whisper_load_ram"] = sampler.metrics()
            for case in selected:
                row = {
                    "case_id": case["id"],
                    "level": LEVELS[case["id"]],
                    "reference_text": case["expected_text"],
                    "expected_json": expected[case["id"]].expected,
                    "status": "error",
                    "error": None,
                }
                print(f"Running {case['id']}...", flush=True)
                try:
                    raw = out / "input.f32"
                    raw.write_bytes(case["pcm_float"])
                    with MemorySampler(worker.pid) as sampler:
                        worker.stdin.write(str(raw) + "\n")
                        worker.stdin.flush()
                        transcription = response(worker, args.timeout)
                    row["stt_ram"] = sampler.metrics()
                    if transcription.get("error"):
                        raise RuntimeError(transcription["error"])
                    row["transcription"] = transcription["text"]
                    if not row["transcription"].strip():
                        raise RuntimeError("Empty transcription")
                    llm_case = PrecisionCase(
                        case["id"], row["transcription"], row["expected_json"]
                    )
                    row["llm_prompt"] = prompt_for(llm_case)
                    with MemorySampler(worker.pid) as sampler:
                        body = http_json(
                            "/api/generate",
                            {
                                "model": OLLAMA_MODEL,
                                "prompt": row["llm_prompt"],
                                "stream": False,
                                "think": False,
                                "format": JSON_SCHEMA,
                                "options": {"temperature": 0},
                                "keep_alive": "10m",
                            },
                            args.timeout,
                        )
                    row["llm_ram"] = sampler.metrics()
                    row["raw_response"] = body.get("response", "")
                    row["ollama_response"] = body
                    row["ollama_resident_after"] = http_json("/api/ps")
                    row["evaluation"] = evaluate(
                        row["raw_response"], row["expected_json"]
                    )
                    row["status"] = "ok"
                    if row["stt_ram"]["errors"] or row["llm_ram"]["errors"]:
                        row["status"] = "ram_measurement_error"
                except Exception as exc:
                    row["error"] = str(exc)
                rows.append(row)
                save(out, rows, environment)
                print(f"  {row['status']} {row.get('evaluation', {})}", flush=True)
        finally:
            worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait()
            (out / "input.f32").unlink(missing_ok=True)
    save(out, rows, environment)
    print(f"Results: {out}", flush=True)
    return int(len(rows) != 6 or any(r["status"] != "ok" for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
