"""Benchmark de modelos Gemini para extracción de inventario en JSON."""
from __future__ import annotations

import argparse
import os
import time
from datetime import datetime

import llm_benchmark as benchmark

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]
GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "productos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "producto": {"type": "string"},
                    "cantidad": {"type": "integer"},
                },
                "required": ["producto", "cantidad"],
            },
        }
    },
    "required": ["productos"],
}


def error_result(model: str, run: int, warmup: bool, message: str) -> benchmark.RunResult:
    return benchmark.RunResult(
        model=f"gemini:{model}", params="cloud", run=run, warmup=warmup,
        status="error", error=message, time_to_first_token_ms=None,
        total_latency_ms=None, tokens_per_second=None,
        ollama_total_duration_ms=None, load_duration_ms=None,
        prompt_eval_duration_ms=None, eval_duration_ms=None,
        inference_duration_ms=None, prompt_tokens=None, output_tokens=None,
        ram_before_mb=None, ram_mid_mb=None, ram_peak_mb=None, ram_after_mb=None,
        valid_json=False, schema_valid=False, expected_products=len(benchmark.EXPECTED),
        correct_products=0, missing_products=len(benchmark.EXPECTED), extra_products=0,
        correct_quantities=0, incorrect_quantities=len(benchmark.EXPECTED),
        excluded_water_correctly=True, exact_match=False, raw_response="",
    )


def run_once(client: object, model: str, run: int, warmup: bool) -> benchmark.RunResult:
    from google.genai import types

    started = time.perf_counter()
    first_at = None
    raw = ""
    usage = None
    try:
        stream = client.models.generate_content_stream(
            model=model,
            contents=benchmark.PROMPT,
            config=types.GenerateContentConfig(
                temperature=benchmark.TEMPERATURE,
                response_mime_type="application/json",
                response_schema=GEMINI_SCHEMA,
            ),
        )
        for chunk in stream:
            text = chunk.text or ""
            if text and first_at is None:
                first_at = time.perf_counter()
            raw += text
            if getattr(chunk, "usage_metadata", None) is not None:
                usage = chunk.usage_metadata
        ended = time.perf_counter()
        metrics = benchmark.evaluate(raw)
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        generation_seconds = ended - (first_at or started)
        tokens_per_second = (
            round(output_tokens / generation_seconds, 3)
            if output_tokens and generation_seconds > 0
            else None
        )
        return benchmark.RunResult(
            model=f"gemini:{model}", params="cloud", run=run, warmup=warmup,
            status="ok", error=None,
            time_to_first_token_ms=round(((first_at or ended) - started) * 1000, 2),
            total_latency_ms=round((ended - started) * 1000, 2),
            tokens_per_second=tokens_per_second,
            ollama_total_duration_ms=None, load_duration_ms=None,
            prompt_eval_duration_ms=None, eval_duration_ms=None,
            inference_duration_ms=None, prompt_tokens=prompt_tokens,
            output_tokens=output_tokens, ram_before_mb=None, ram_mid_mb=None,
            ram_peak_mb=None, ram_after_mb=None, raw_response=raw,
            expected_products=len(benchmark.EXPECTED), **metrics,
        )
    except Exception as exc:
        return error_result(model, run, warmup, str(exc))


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark de modelos Gemini.")
    parser.add_argument("--models", nargs="+", choices=GEMINI_MODELS, default=GEMINI_MODELS)
    parser.add_argument("--runs", type=int, default=benchmark.RUNS_PER_MODEL)
    parser.add_argument("--run-name", default=None)
    args = parser.parse_args()
    if args.runs < 1:
        print("--runs debe ser mayor o igual a 1.")
        return 2
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Falta la variable de entorno GEMINI_API_KEY.")
        return 1
    try:
        from google import genai
    except ImportError:
        print('Falta google-genai. Instalá con: python -m pip install ".[gemini]"')
        return 1
    client = genai.Client(api_key=api_key)
    base = benchmark.PROJECT_ROOT / "reports" / "llm-benchmark"
    name = args.run_name or datetime.now().strftime("gemini_%Y%m%d_%H%M%S")
    output_directory = base / name
    output_directory.mkdir(parents=True, exist_ok=False)
    benchmark.OUTPUT_DIRECTORY = output_directory
    results = []
    for model in args.models:
        print(f"\n{model}: warm-up y {args.runs} ejecuciones...")
        results.append(run_once(client, model, 1, True))
        for run in range(1, args.runs + 1):
            result = run_once(client, model, run, False)
            results.append(result)
            print(f"  ejecución {run}/{args.runs}: {result.status}")
            benchmark.write_outputs(results)
    benchmark.write_outputs(results)
    try:
        from analyze_llm_benchmark import main as analyze_results_main
        analyze_results_main([
            "--results-directory", str(output_directory),
            "--report-file", str(output_directory / "benchmark_report.md"),
        ])
    except Exception as exc:
        print(f"No se pudo generar el informe Markdown: {exc}")
    print(f"\nResultados guardados en: {output_directory.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
