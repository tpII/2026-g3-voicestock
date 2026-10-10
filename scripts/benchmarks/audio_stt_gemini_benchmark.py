"""Single-pass basic/habitual audio -> Whisper Small Q5 -> Gemini -> JSON."""

import csv
import json
import os
import platform
import subprocess
import time

from api_keys import load_api_keys
from precision_benchmark import CASES, JSON_SCHEMA, PrecisionCase, evaluate, prompt_for
from prompt_levels import LEVELS
from stt_benchmark import FIXTURES, ROOT, Monitor, read_cases, response, sha256

MODEL = "gemini-3.8-flash"


def save(out, rows, environment):
    (out / "results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    (out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n"
    )
    flat = [
        {
            "case_id": r["case_id"],
            "level": r["level"],
            "status": r["status"],
            **r.get("evaluation", {}),
            "whisper_peak_mib": r.get("stt_ram", {}).get("ram_peak_mib"),
            "api_client_peak_mib": r.get("api_client_ram", {}).get("ram_peak_mib"),
            "remote_model_ram_mib": None,
        }
        for r in rows
    ]
    if flat:
        fields = list(dict.fromkeys(k for row in flat for k in row))
        with (out / "benchmark_cases.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(flat)
    correct = sum(r.get("evaluation", {}).get("exact_match", False) for r in rows)
    lines = [
        "# Audio → Whisper Small Q5 → Gemini → JSON",
        "",
        f"Modelo solicitado: `{MODEL}`. Una corrida por prompt; "
        "sin calentamiento, reintentos ni reparación de transcripciones.",
        "El LLM recibe sólo la transcripción dentro del contrato y catálogo "
        "existentes. No recibe texto ni JSON esperado.",
        "RAM RSS en MiB muestreada cada 10 ms: trabajador Whisper y "
        "proceso Python del cliente API (incluye orquestación y SDK). "
        "La RAM de Gemini remoto no es observable y queda sin dato. "
        "No se aplican operaciones al inventario.",
        "Referencias pendientes de verificación humana del audio.",
        "",
        f"JSON exacto: **{correct}/{len(rows)}** casos procesados.",
        "",
        "| Caso | Nivel | JSON exacto | Whisper MiB | Cliente API MiB |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in flat:

        def fmt(key):
            value = row.get(key)
            return f"{value:.1f}" if value is not None else "—"

        lines.append(
            f"| {row['case_id']} | {row['level']} | "
            f"{row.get('exact_match', False)} | "
            f"{fmt('whisper_peak_mib')} | {fmt('api_client_peak_mib')} |"
        )
    for r in rows:
        lines += [
            "",
            f"## {r['case_id']}",
            "",
            "**Referencia:** " + r["reference_text"],
            "",
            "**Transcripción enviada:** " + r.get("transcription", ""),
            "",
            "**JSON esperado:**",
            "```json",
            json.dumps(r["expected_json"], ensure_ascii=False, indent=2),
            "```",
            "",
            "**Salida real:**",
            "```json",
            r.get("raw_response", ""),
            "```",
            "",
            "**Evaluación:** " + json.dumps(r.get("evaluation", {})),
            "**Error:** " + str(r.get("error")),
        ]
    (out / "benchmark_report.md").write_text("\n".join(lines) + "\n")


def main():
    from google import genai
    from google.genai import types

    load_api_keys()
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Falta GEMINI_API_KEY en entorno o config/api-keys.env")
    client = genai.Client(
        api_key=key,
        http_options=types.HttpOptions(
            timeout=600000, retry_options=types.HttpRetryOptions(attempts=1)
        ),
    )
    out = ROOT / "reports/audio-stt-llm" / time.strftime("gemini_%Y%m%d_%H%M%S")
    out.mkdir(parents=True)
    manifest = read_cases()
    selected = [c for c in manifest["cases"] if LEVELS[c["id"]] != "exigente"]
    expected = {c.case_id: c.expected for c in CASES}
    model = ROOT / "models/stt/whisper/ggml-small-q5_1.bin"
    environment = {
        "provider": "gemini",
        "llm_model": MODEL,
        "platform": platform.platform(),
        "runs_per_case": 1,
        "warmups": 0,
        "retries": 0,
        "manifest_sha256": sha256(FIXTURES / "manifest.json"),
        "whisper_sha256": sha256(model),
        "threads_whisper": 4,
        "contract_sha256": sha256(
            ROOT / "scripts/benchmarks/prompts/precision/contract.txt"
        ),
        "settings": {
            "temperature": 0,
            "thinking_level": "low",
            "response_mime_type": "application/json",
            "schema": JSON_SCHEMA,
        },
        "audio_cases": [
            {k: v for k, v in c.items() if k != "pcm_float"} for c in selected
        ],
        "remote_model_ram": None,
    }
    rows = []
    with (out / "whisper.log").open("w") as log:
        worker = subprocess.Popen(
            [str(ROOT / ".tools/stt/whisper-benchmark-worker"), str(model), "4"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log,
            text=True,
        )
        try:
            with Monitor(worker.pid) as monitor:
                response(worker, 600)
            environment["whisper_load_ram"] = monitor.metrics()
            for case in selected:
                row = {
                    "case_id": case["id"],
                    "level": LEVELS[case["id"]],
                    "reference_text": case["expected_text"],
                    "expected_json": expected[case["id"]],
                    "status": "error",
                    "error": None,
                }
                print(f"Running {case['id']}...", flush=True)
                try:
                    raw = out / "input.f32"
                    raw.write_bytes(case["pcm_float"])
                    with Monitor(worker.pid) as monitor:
                        worker.stdin.write(str(raw) + "\n")
                        worker.stdin.flush()
                        stt = response(worker, 600)
                    row["stt_ram"] = monitor.metrics()
                    if stt.get("error"):
                        raise RuntimeError(stt["error"])
                    row["transcription"] = stt["text"]
                    llm_case = PrecisionCase(
                        case["id"], stt["text"], row["expected_json"]
                    )
                    row["llm_prompt"] = prompt_for(llm_case)
                    with Monitor(os.getpid()) as monitor:
                        result = client.models.generate_content(
                            model=MODEL,
                            contents=row["llm_prompt"],
                            config=types.GenerateContentConfig(
                                temperature=0,
                                response_mime_type="application/json",
                                response_schema=JSON_SCHEMA,
                                thinking_config=types.ThinkingConfig(
                                    thinking_level="low"
                                ),
                            ),
                        )
                    row["api_client_ram"] = monitor.metrics()
                    row["raw_response"] = result.text or ""
                    row["gemini_response"] = result.model_dump(mode="json")
                    row["evaluation"] = evaluate(
                        row["raw_response"], row["expected_json"]
                    )
                    row["status"] = "ok"
                except Exception as exc:
                    row["error"] = str(exc).replace(key, "[REDACTED]")
                rows.append(row)
                save(out, rows, environment)
                print(
                    f"  {row['status']} {row.get('evaluation', {})} "
                    f"{row.get('error') or ''}",
                    flush=True,
                )
        finally:
            worker.terminate()
            try:
                worker.wait(timeout=5)
            except subprocess.TimeoutExpired:
                worker.kill()
                worker.wait()
            client.close()
            (out / "input.f32").unlink(missing_ok=True)
    print(f"Results: {out}", flush=True)
    return int(len(rows) != 6 or any(r["status"] != "ok" for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
