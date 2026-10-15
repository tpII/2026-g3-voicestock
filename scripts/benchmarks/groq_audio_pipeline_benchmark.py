"""Compare Groq Whisper models through audio -> STT -> GPT OSS 20B -> JSON."""

import argparse
import csv
import hashlib
import json
import os
import platform
import statistics
import time
import urllib.error
import urllib.request
import uuid

from api_keys import load_api_keys
from precision_benchmark import (
    CASES,
    GROQ_JSON_SCHEMA,
    GROQ_URL,
    PrecisionCase,
    evaluate,
    prompt_for,
)
from stt_benchmark import FIXTURES, ROOT, accuracy, sha256

STT_MODELS = ("whisper-large-v3", "whisper-large-v3-turbo")
LLM_MODEL = "openai/gpt-oss-20b"
STT_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def post(url, data, content_type, key, timeout, metrics):
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": content_type,
            "User-Agent": "llm-to-json-benchmark/1.0",
        },
    )
    metrics.update(attempts=0, retries=0, retry_sleep_s=0.0, rate_limit_events=[])
    stage_started = time.perf_counter()
    try:
        while True:
            metrics["attempts"] += 1
            started = time.perf_counter()
            try:
                with urllib.request.urlopen(request, timeout=timeout) as stream:
                    result = json.load(stream)
                return result, time.perf_counter() - started
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                is_tpm = (
                    "tokens per minute" in detail.lower() or "(tpm)" in detail.lower()
                )
                if exc.code != 429 or not is_tpm:
                    raise RuntimeError(f"HTTP {exc.code}: {detail}") from None
                metrics["retries"] += 1
                metrics["rate_limit_events"].append(
                    {
                        "attempt": metrics["attempts"],
                        "request_s": time.perf_counter() - started,
                        "error": detail.replace(key, "[REDACTED]"),
                    }
                )
                print("  Token-per-minute limit: retrying in 2 s...", flush=True)
                waiting = time.perf_counter()
                time.sleep(2)
                metrics["retry_sleep_s"] += time.perf_counter() - waiting
    finally:
        metrics["stage_total_s"] = time.perf_counter() - stage_started


def multipart(audio, prompt, model):
    boundary = "voicestock-" + uuid.uuid4().hex
    parts = []
    fields = {
        "model": model,
        "language": "es",
        "temperature": "0",
        "response_format": "verbose_json",
    }
    if prompt:
        fields["prompt"] = prompt
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
            f"\r\n\r\n{value}\r\n".encode()
        )
    parts += [
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        'filename="audio.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode(),
        audio,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def llm_payload(prompt):
    return {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "reasoning_effort": "low",
        "max_completion_tokens": 2000,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "operaciones_inventario",
                "strict": True,
                "schema": GROQ_JSON_SCHEMA,
            },
        },
    }


def write_csv(path, rows):
    if rows:
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=list(dict.fromkeys(k for r in rows for k in r))
            )
            writer.writeheader()
            writer.writerows(rows)


def save(out, rows, environment):
    for name, data in [("results.json", rows), ("environment.json", environment)]:
        (out / name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    flat = [
        {
            "stt_model": r["stt_model"],
            "case_id": r["case_id"],
            "level": r["level"],
            "status": r["status"],
            "audio_s": r["audio_s"],
            "stt_api_s": r.get("stt_api_s"),
            "llm_api_s": r.get("llm_api_s"),
            "pipeline_s": r["pipeline_s"],
            "stt_retries": r.get("stt_request_metrics", {}).get("retries", 0),
            "llm_retries": r.get("llm_request_metrics", {}).get("retries", 0),
            "retry_sleep_s": sum(
                r.get(k, {}).get("retry_sleep_s", 0)
                for k in ("stt_request_metrics", "llm_request_metrics")
            ),
            "stt_stage_total_s": r.get("stt_request_metrics", {}).get("stage_total_s"),
            "llm_stage_total_s": r.get("llm_request_metrics", {}).get("stage_total_s"),
            "wer_pct": r.get("stt_evaluation", {}).get("wer_pct"),
            "cer_pct": r.get("stt_evaluation", {}).get("cer_pct"),
            **r.get("evaluation", {}),
            "transcription": r.get("transcription", ""),
            "error": r.get("error", ""),
        }
        for r in rows
    ]
    write_csv(out / "benchmark_cases.csv", flat)
    summaries = []
    expected_count = len(environment["audio_cases"])
    for model in STT_MODELS:
        group = [r for r in rows if r["stt_model"] == model]
        ok = [r for r in group if r["status"] == "ok"]
        exact = sum(r.get("evaluation", {}).get("exact_match", False) for r in group)
        item = {
            "stt_model": model,
            "processed": len(group),
            "expected": expected_count,
            "successful": len(ok),
            "errors": len(group) - len(ok),
            "exact_json": exact,
            "exact_json_pct": 100 * exact / expected_count,
        }
        for field in ("stt_api_s", "llm_api_s", "pipeline_s"):
            values = [r[field] for r in ok if field in r]
            for name, fn in [("mean", statistics.mean), ("min", min), ("max", max)]:
                item[f"{field}_{name}"] = fn(values) if values else None
        measured = [r["stt_evaluation"] for r in group if "stt_evaluation" in r]
        for label, numerator, denominator in [
            ("wer_pct", "word_errors", "reference_words"),
            ("cer_pct", "char_errors", "reference_chars"),
        ]:
            total = sum(x[denominator] for x in measured)
            item[label] = (
                100 * sum(x[numerator] for x in measured) / total if total else None
            )
        summaries.append(item)
    write_csv(out / "benchmark_summary.csv", summaries)

    def fmt(value):
        return f"{value:.3f}" if isinstance(value, (float, int)) else "—"

    def cell(value):
        return str(value).replace("|", "&#124;").replace("\n", "<br>")

    lines = [
        "# Audio → Groq Whisper → GPT OSS 20B → JSON",
        "",
        "Una corrida por modelo y audio; sin calentamiento. "
        "Ante HTTP 429 por tokens/minuto se reintenta cada 2 segundos "
        "hasta funcionar. "
        "Todo se coordina desde la PC. Ambos modelos STT y el LLM son remotos.",
        "Los tiempos API incluyen red, subida y procesamiento remoto; no son "
        "tiempos puros de inferencia. STT/LLM API corresponden al intento exitoso. "
        "pipeline_s empieza antes de leer el WAV y "
        "termina al recibir/procesar el JSON del LLM e incluye reintentos "
        "y esperas; excluye evaluación y escritura "
        "del reporte. Los tiempos agregados cubren sólo recorridos exitosos.",
        "El LLM recibe exclusivamente la transcripción, el contrato y el catálogo; "
        "no recibe el texto de referencia ni el JSON esperado. No hay reparación "
        "de transcripciones ni cambios al inventario.",
        "WER/CER ignoran puntuación y mayúsculas, pero distinguen números escritos "
        "y dígitos. Son métricas textuales; JSON exacto mide el recorrido completo "
        "y no garantiza fidelidad del STT. Referencias de audio pendientes de "
        "verificación humana. La RAM de los modelos remotos no es observable.",
        "",
        "## Resumen por STT",
        "",
        "| Modelo STT | JSON exacto | Errores | STT medio s | LLM medio s | "
        "Total medio s | WER % | CER % |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['stt_model']} | {s['exact_json']}/{expected_count} "
            f"({s['exact_json_pct']:.1f}%) | {s['errors']} | "
            f"{fmt(s['stt_api_s_mean'])} | {fmt(s['llm_api_s_mean'])} | "
            f"{fmt(s['pipeline_s_mean'])} | {fmt(s['wer_pct'])} | {fmt(s['cer_pct'])} |"
        )
    lines += [
        "",
        "## Resultados por nivel",
        "",
        "| STT | Nivel | Procesados/esperados | JSON exacto |",
        "|---|---|---:|---:|",
    ]
    for model in STT_MODELS:
        for level in ("basico", "habitual", "exigente"):
            expected = sum(c["level"] == level for c in environment["audio_cases"])
            subset = [
                r for r in rows if r["stt_model"] == model and r["level"] == level
            ]
            exact = sum(
                r.get("evaluation", {}).get("exact_match", False) for r in subset
            )
            lines.append(
                f"| {model} | {level} | {len(subset)}/{expected} | {exact}/{expected} |"
            )
    lines += [
        "",
        "## Tiempos y exactitud por prompt",
        "",
        "| STT | Caso | STT s | LLM s | Total s | JSON exacto | Estado |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for r in flat:
        lines.append(
            f"| {r['stt_model']} | {r['case_id']} | {fmt(r['stt_api_s'])} | "
            f"{fmt(r['llm_api_s'])} | {fmt(r['pipeline_s'])} | "
            f"{r.get('exact_match', False)} | {r['status']} |"
        )
    lines += [
        "",
        "## Comparación de transcripciones",
        "",
        "| Caso | Referencia | Large V3 | Turbo |",
        "|---|---|---|---|",
    ]
    for case in environment["audio_cases"]:
        values = []
        for model in STT_MODELS:
            row = next(
                (
                    r
                    for r in rows
                    if r["case_id"] == case["id"] and r["stt_model"] == model
                ),
                {},
            )
            values.append(row.get("transcription", "Sin transcripción"))
        lines.append(
            "| "
            + " | ".join(cell(x) for x in [case["id"], case["expected_text"], *values])
            + " |"
        )
    lines += [
        "",
        "## Reintentos por límite de tokens",
        "",
        "| STT | Caso | Reintentos STT | Reintentos LLM | Espera s |",
        "|---|---|---:|---:|---:|",
    ]
    for r in flat:
        lines.append(
            f"| {r['stt_model']} | {r['case_id']} | {r['stt_retries']} | "
            f"{r['llm_retries']} | {fmt(r['retry_sleep_s'])} |"
        )
    for r in rows:
        lines += [
            "",
            f"## {r['stt_model']} / {r['case_id']}",
            "",
            "**Referencia:** " + r["reference_text"],
            "",
            "**Transcripción:** " + r.get("transcription", ""),
            "",
            "**JSON esperado:**",
            "```json",
            json.dumps(r["expected_json"], ensure_ascii=False, indent=2),
            "```",
            "",
            "**JSON obtenido:**",
            "```json",
            r.get("raw_response", ""),
            "```",
            "",
            "**Evaluación:** " + json.dumps(r.get("evaluation", {})),
            "",
            "**Error:** " + r.get("error", "Ninguno"),
        ]
    (out / "benchmark_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    load_api_keys()
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        parser.error("GROQ_API_KEY is required in config/api-keys.env")
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    cases = manifest["cases"]
    expected = {c.case_id: c.expected for c in CASES}
    prompt_paths = [
        ROOT / "scripts/benchmarks/prompts" / name
        for name in ("contexto-stt.txt", "productos-stt.txt")
    ]
    prompt = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in prompt_paths)
    for case in cases:
        if sha256(FIXTURES / case["wav"]) != case["wav_sha256"]:
            raise RuntimeError("Fixture hash mismatch: " + case["id"])
        if case["id"] not in expected:
            raise RuntimeError("Missing expected JSON: " + case["id"])
    out = (
        ROOT
        / "reports/audio-stt-llm"
        / (
            time.strftime("groq_whisper_compare_%Y%m%d_%H%M%S")
            + "_"
            + uuid.uuid4().hex[:8]
        )
    )
    out.mkdir(parents=True)
    env = {
        "provider": "groq",
        "stt_models": STT_MODELS,
        "llm_model": LLM_MODEL,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "runs_per_case": 1,
        "warmups": 0,
        "retry_policy": "HTTP 429 tokens-per-minute: wait 2 seconds until success",
        "audio_cases": cases,
        "manifest_sha256": sha256(FIXTURES / "manifest.json"),
        "stt_prompt": prompt,
        "stt_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_files": [
            {"path": str(p.relative_to(ROOT)), "sha256": sha256(p)}
            for p in prompt_paths
        ],
        "contract_sha256": sha256(
            ROOT / "scripts/benchmarks/prompts/precision/contract.txt"
        ),
        "stt_settings": {
            "language": "es",
            "temperature": 0,
            "response_format": "verbose_json",
        },
        "llm_settings": llm_payload("config only"),
        "timeout_s": args.timeout,
        "remote_model_ram": None,
        "execution_order": "Case order from manifest, alternating model order per case",
    }
    rows = []
    save(out, rows, env)
    try:
        for i, case in enumerate(cases):
            for model in STT_MODELS if i % 2 == 0 else STT_MODELS[::-1]:
                row = {
                    "case_id": case["id"],
                    "level": case["level"],
                    "stt_model": model,
                    "audio_s": case["duration_s"],
                    "reference_text": case["expected_text"],
                    "expected_json": expected[case["id"]],
                    "status": "stt_error",
                }
                print(f"{model} / {case['id']}", flush=True)
                started = time.perf_counter()
                stage_started = started
                stage = "stt"
                try:
                    body, content_type = multipart(
                        (FIXTURES / case["wav"]).read_bytes(), prompt, model
                    )
                    stage_started = time.perf_counter()
                    row["stt_request_metrics"] = {}
                    result, row["stt_api_s"] = post(
                        STT_URL,
                        body,
                        content_type,
                        key,
                        args.timeout,
                        row["stt_request_metrics"],
                    )
                    row["stt_response"] = result
                    text = result.get("text")
                    if not isinstance(text, str) or not text.strip():
                        raise RuntimeError("Empty STT transcription")
                    row["transcription"] = text
                    stage = "llm"
                    row["status"] = "llm_error"
                    llm_prompt = prompt_for(
                        PrecisionCase(case["id"], text, row["expected_json"])
                    )
                    row["llm_prompt"] = llm_prompt
                    body = json.dumps(llm_payload(llm_prompt)).encode()
                    stage_started = time.perf_counter()
                    row["llm_request_metrics"] = {}
                    result, row["llm_api_s"] = post(
                        GROQ_URL,
                        body,
                        "application/json",
                        key,
                        args.timeout,
                        row["llm_request_metrics"],
                    )
                    row["llm_response"] = result
                    row["raw_response"] = (
                        result["choices"][0]["message"].get("content") or ""
                    )
                    row["pipeline_s"] = time.perf_counter() - started
                    row["evaluation"] = evaluate(
                        row["raw_response"], row["expected_json"]
                    )
                    row["status"] = "ok"
                except Exception as exc:
                    row.setdefault(
                        stage + "_api_s", time.perf_counter() - stage_started
                    )
                    row["error"] = str(exc).replace(key, "[REDACTED]")
                finally:
                    row.setdefault("pipeline_s", time.perf_counter() - started)
                    if "transcription" in row:
                        row["stt_evaluation"] = accuracy(
                            row["reference_text"], row["transcription"]
                        )
                    rows.append(row)
                    save(out, rows, env)
                print(
                    f"  {row['status']} "
                    f"exact={row.get('evaluation', {}).get('exact_match')} "
                    f"total={row['pipeline_s']:.3f}s {row.get('error', '')}",
                    flush=True,
                )
    except KeyboardInterrupt:
        env["interrupted"] = True
        save(out, rows, env)
        print(f"Partial results: {out}", flush=True)
        return 130
    print(f"Results: {out}", flush=True)
    return int(len(rows) != len(cases) * 2 or any(r["status"] != "ok" for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
