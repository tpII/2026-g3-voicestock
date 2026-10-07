"""Benchmark controlado de extracción de inventario con modelos locales Ollama.

Uso: python scripts/benchmarks/llm_benchmark.py
Opcional (mejor medición de RAM por proceso): pip install ".[benchmark]"
"""
from __future__ import annotations

import csv
import argparse
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Configuración centralizada.
OLLAMA_URL = "http://127.0.0.1:11434"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "qwen/qwen3-32b"
GROQ_REASONING_EFFORT = "none"
GROQ_MAX_TOKENS = 320
MODELS = {
    "llama3.2:1b": "~1B",
    "qwen3:1.7b": "~1.7B",
    "granite3.1-dense:2b": "~2B",
    "qwen3.5:2b": "~2B",
    "qwen2.5:3b-instruct": "~3B",
    "qwen3:4b-instruct": "~4B",
}
RUNS_PER_MODEL = 5
WARMUP_RUNS = 1
TEMPERATURE = 0
CONTEXT_SIZE = 4096
TIMEOUT_SECONDS = 180
RAM_MIDDLE_SAMPLE_DELAY_SECONDS = 1.0
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIRECTORY = PROJECT_ROOT / "reports" / "llm-benchmark"
ACTIVE_MODELS = MODELS.copy()

PROMPT = '''Sos un sistema de extracción de datos para un inventario.

Tu única tarea es leer el mensaje del usuario, identificar todos los productos mencionados y devolverlos en formato JSON.

Respondé ÚNICAMENTE con JSON válido.
No saludes.
No expliques.
No agregues comentarios.
No muestres tu razonamiento.
No escribas nada antes ni después del JSON.

BASE DE DATOS DE PRODUCTOS:

- Coca Cola 2L
- Coca Cola 1.5L
- Coca Cola Zero 2L
- Sprite 2L
- Sprite 1.5L
- Agua Villavicencio 1.5L
- Arroz Gallo 1kg
- Fideos Matarazzo 500g
- Detergente Magistral 750ml
- Leche La Serenísima 1L

REGLAS:

- Detectá TODOS los productos mencionados en el mensaje.
- "producto" debe contener EXACTAMENTE el nombre correspondiente de la base de datos.
- Interpretá nombres coloquiales, abreviaciones y formas naturales de hablar.
- Usá marca, tamaño, tipo y presentación para distinguir productos.
- Convertí cantidades escritas con palabras a números.
- Cada producto debe aparecer como un objeto separado.
- No combines productos diferentes.
- Nunca inventes productos que no estén en la base de datos.
- Ignorá información que no corresponda a producto o cantidad.
- Si un producto no puede identificarse con seguridad, usá null.
- Si falta la cantidad de un producto, usá null.

FORMATO OBLIGATORIO:

{
  "productos": [
    {
      "producto": "nombre exacto",
      "cantidad": 0
    }
  ]
}

MENSAJE DEL USUARIO:

"Bueno, anotame lo que acaba de llegar porque fueron varias cosas. Primero bajaron veinte cocas comunes de dos litros y también dejaron doce Coca Zero, las grandes de dos litros. Después trajeron ocho Sprite de litro y medio y otras seis Sprite grandes de dos litros. De almacén llegaron quince paquetes de arroz Gallo de un kilo y veinticuatro paquetes de fideos Matarazzo de medio kilo. También dejaron nueve detergentes Magistral de 750 y, antes de que me olvide, llegaron dieciocho leches La Serenísima de un litro. Las aguas que estaban en el camión al final no las bajaron, así que esas no las cargues."'''

EXPECTED = {
    "Coca Cola 2L": 20, "Coca Cola Zero 2L": 12, "Sprite 1.5L": 8,
    "Sprite 2L": 6, "Arroz Gallo 1kg": 15, "Fideos Matarazzo 500g": 24,
    "Detergente Magistral 750ml": 9, "Leche La Serenísima 1L": 18,
}
WATER = "Agua Villavicencio 1.5L"


@dataclass
class RunResult:
    model: str; params: str; run: int; warmup: bool; status: str
    error: str | None; time_to_first_token_ms: float | None
    total_latency_ms: float | None; tokens_per_second: float | None
    ollama_total_duration_ms: float | None; load_duration_ms: float | None
    prompt_eval_duration_ms: float | None; eval_duration_ms: float | None
    inference_duration_ms: float | None
    prompt_tokens: int | None; output_tokens: int | None
    ram_before_mb: float | None; ram_mid_mb: float | None
    ram_peak_mb: float | None; ram_after_mb: float | None
    valid_json: bool; schema_valid: bool; expected_products: int
    correct_products: int; missing_products: int; extra_products: int
    correct_quantities: int; incorrect_quantities: int
    excluded_water_correctly: bool; exact_match: bool; raw_response: str


def http_json(path: str, payload: dict | None = None, timeout: int = TIMEOUT_SECONDS) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(OLLAMA_URL + path, data=data,
        headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_ram_mb() -> float | None:
    """Working set total de procesos ollama/llama-server, o None sin psutil."""
    try:
        import psutil  # type: ignore
        total = 0
        for proc in psutil.process_iter(["name", "memory_info"]):
            name = (proc.info["name"] or "").lower()
            if "ollama" in name or "llama-server" in name:
                total += proc.info["memory_info"].rss
        return round(total / 1024 / 1024, 2)
    except Exception:
        return None


def evaluate(raw: str) -> dict[str, Any]:
    result = dict(valid_json=False, schema_valid=False, correct_products=0,
        missing_products=len(EXPECTED), extra_products=0, correct_quantities=0,
        incorrect_quantities=len(EXPECTED), excluded_water_correctly=True, exact_match=False)
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return result
    result["valid_json"] = True
    if not isinstance(decoded, dict) or set(decoded) != {"productos"} or not isinstance(decoded["productos"], list):
        return result
    products: dict[str, Any] = {}
    for item in decoded["productos"]:
        if not isinstance(item, dict) or set(item) != {"producto", "cantidad"} or not isinstance(item.get("producto"), str):
            return result
        # Duplicados no se aceptan: no pueden representar los pares esperados exactamente.
        if item["producto"] in products:
            return result
        products[item["producto"]] = item["cantidad"]
    result["schema_valid"] = True
    matching = set(products) & set(EXPECTED)
    result["correct_products"] = len(matching)
    result["missing_products"] = len(set(EXPECTED) - set(products))
    result["extra_products"] = len(set(products) - set(EXPECTED))
    result["correct_quantities"] = sum(products[p] == EXPECTED[p] for p in matching)
    result["incorrect_quantities"] = len(EXPECTED) - result["correct_quantities"]
    result["excluded_water_correctly"] = WATER not in products
    result["exact_match"] = (len(products) == len(EXPECTED) and products == EXPECTED)
    return result


def run_once(model: str, params: str, run: int, warmup: bool) -> RunResult:
    before, middle, raw, first_at, started, final = ollama_ram_mb(), None, "", None, time.perf_counter(), {}
    try:
        payload = {"model": model, "prompt": PROMPT, "stream": True, "keep_alive": "30m",
               "think": False,
                   "options": {"temperature": TEMPERATURE, "num_ctx": CONTEXT_SIZE}}
        request = urllib.request.Request(OLLAMA_URL + "/api/generate", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            for line in response:
                if not line.strip(): continue
                fragment = json.loads(line.decode("utf-8"))
                if fragment.get("response") and first_at is None: first_at = time.perf_counter()
                raw += fragment.get("response", "")
                if (middle is None and first_at is not None and
                        time.perf_counter() - first_at >= RAM_MIDDLE_SAMPLE_DELAY_SECONDS):
                    middle = ollama_ram_mb()
                if fragment.get("done"): final = fragment
        ended, after = time.perf_counter(), ollama_ram_mb()
        metrics = evaluate(raw)
        eval_duration = final.get("eval_duration", 0)
        output_tokens = final.get("eval_count")
        tps = round(output_tokens / (eval_duration / 1e9), 3) if output_tokens and eval_duration else None
        duration_ms = lambda field: round(final[field] / 1e6, 2) if final.get(field) else None
        inference_duration_ms = None
        if final.get("prompt_eval_duration") is not None and final.get("eval_duration") is not None:
            inference_duration_ms = round((final["prompt_eval_duration"] + final["eval_duration"]) / 1e6, 2)
        ram_values = [value for value in (before, middle, after) if value is not None]
        return RunResult(model, params, run, warmup, "ok", None,
            round(((first_at or ended) - started) * 1000, 2), round((ended - started) * 1000, 2), tps,
            duration_ms("total_duration"), duration_ms("load_duration"),
            duration_ms("prompt_eval_duration"), duration_ms("eval_duration"), inference_duration_ms,
            final.get("prompt_eval_count"), output_tokens, before, middle, max(ram_values, default=None), after, raw_response=raw,
            expected_products=len(EXPECTED), **metrics)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except OSError:
            detail = ""
        message = f"HTTP {exc.code} {exc.reason}"
        if detail:
            message += f": {detail}"
        return RunResult(model, params, run, warmup, "error", message, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None,
            False, False, len(EXPECTED), 0, len(EXPECTED), 0, 0,
            len(EXPECTED), True, False, raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        after = ollama_ram_mb()
        return RunResult(model, params, run, warmup, "error", str(exc), None, None, None,
            None, None, None, None, None, None, None, before, middle, max(
                (value for value in (before, middle, after) if value is not None), default=None), after,
            False, False, len(EXPECTED), 0, len(EXPECTED), 0, 0,
            len(EXPECTED), True, False, raw)


def run_groq_once(model: str, params: str, run: int, warmup: bool, api_key: str) -> RunResult:
    raw, first_at, started, usage = "", None, time.perf_counter(), {}
    try:
        payload = {
            "model": model.removeprefix("groq:"),
            "messages": [{"role": "user", "content": PROMPT}],
            "stream": True,
            "temperature": TEMPERATURE,
            "reasoning_effort": GROQ_REASONING_EFFORT,
            "max_tokens": GROQ_MAX_TOKENS,
            "stream_options": {"include_usage": True},
        }
        request = urllib.request.Request(
            GROQ_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream",
                "User-Agent": "llm-to-json-benchmark/1.0",
            },
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            for line in response:
                text = line.decode("utf-8").strip()
                if not text.startswith("data:"):
                    continue
                data = text[5:].strip()
                if data == "[DONE]":
                    continue
                fragment = json.loads(data)
                if fragment.get("usage"):
                    usage = fragment["usage"]
                choices = fragment.get("choices") or []
                delta = choices[0].get("delta", {}) if choices else {}
                content = delta.get("content") or ""
                if content and first_at is None:
                    first_at = time.perf_counter()
                raw += content
        ended = time.perf_counter()
        metrics = evaluate(raw)
        prompt_tokens = usage.get("prompt_tokens")
        output_tokens = usage.get("completion_tokens")
        generation_seconds = ended - (first_at or started)
        tps = round(output_tokens / generation_seconds, 3) if output_tokens and generation_seconds else None
        return RunResult(model, params, run, warmup, "ok", None,
            round(((first_at or ended) - started) * 1000, 2), round((ended - started) * 1000, 2), tps,
            None, None, None, None, None, prompt_tokens, output_tokens,
            None, None, None, None, raw_response=raw,
            expected_products=len(EXPECTED), **metrics)
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except OSError:
            detail = ""
        message = f"HTTP {exc.code} {exc.reason}"
        if detail:
            message += f": {detail}"
        return RunResult(model, params, run, warmup, "error", message, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None,
            False, False, len(EXPECTED), 0, len(EXPECTED), 0, 0,
            len(EXPECTED), True, False, raw)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return RunResult(model, params, run, warmup, "error", str(exc), None, None, None,
            None, None, None, None, None, None, None, None, None, None, None,
            False, False, len(EXPECTED), 0, len(EXPECTED), 0, 0,
            len(EXPECTED), True, False, raw)


def unload(model: str) -> None:
    try: http_json("/api/generate", {"model": model, "keep_alive": 0})
    except Exception: pass


def parameter_sort_key(model: str) -> float:
    """Obtiene el tamaño aproximado del nombre/configuración del modelo."""
    match = re.search(r"(?:^|:)(\d+(?:\.\d+)?)[bB](?:-|$)", model)
    return float(match.group(1)) if match else float("inf")


def print_model_inventory(installed: set[str], configured: dict[str, str]) -> tuple[list[str], list[str]]:
    """Informa el inventario local y devuelve (disponibles, faltantes) ordenados."""
    ordered = sorted(configured, key=parameter_sort_key)
    available = [model for model in ordered if model in installed]
    missing = [model for model in ordered if model not in installed]
    print("\nModelos configurados (ordenados por cantidad de parámetros):")
    for model in ordered:
        status = "ENCONTRADO localmente" if model in installed else "NO encontrado"
        print(f"  - {model} ({configured[model]}): {status}")
    if not missing:
        print("\nTodos los modelos se encontraron y se probarán.")
    else:
        print(f"\nSe encontraron {len(available)} de {len(ordered)} modelos; se omitirán los faltantes.")
    return available, missing


def write_outputs(results: list[RunResult]) -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    rows = [asdict(r) for r in results]
    with (OUTPUT_DIRECTORY / "benchmark_runs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else list(RunResult.__annotations__))
        writer.writeheader(); writer.writerows(rows)
    with (OUTPUT_DIRECTORY / "raw_responses.json").open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    summary = []
    model_params = {}
    for result in results:
        model_params.setdefault(result.model, result.params)
    for model, params in model_params.items():
        measured = [r for r in results if r.model == model and not r.warmup and r.status == "ok"]
        if not measured: continue
        vals = lambda field: [getattr(r, field) for r in measured if getattr(r, field) is not None]
        avg = lambda field: round(statistics.mean(vals(field)), 2) if vals(field) else None
        med = lambda field: round(statistics.median(vals(field)), 2) if vals(field) else None
        total = vals("total_latency_ms")
        summary.append({"model": model, "params": params, "successful_runs": len(measured),
          "avg_ttft_ms": avg("time_to_first_token_ms"), "median_ttft_ms": med("time_to_first_token_ms"),
          "avg_total_latency_ms": avg("total_latency_ms"), "median_total_latency_ms": med("total_latency_ms"),
          "min_total_latency_ms": min(total) if total else None, "max_total_latency_ms": max(total) if total else None,
                    "avg_tokens_per_second": avg("tokens_per_second"),
                    "avg_ollama_total_duration_ms": avg("ollama_total_duration_ms"),
                    "avg_load_duration_ms": avg("load_duration_ms"),
                    "avg_prompt_eval_duration_ms": avg("prompt_eval_duration_ms"),
                    "avg_eval_duration_ms": avg("eval_duration_ms"),
                    "avg_inference_duration_ms": avg("inference_duration_ms"),
                    "ram_peak_mb": max(vals("ram_peak_mb"), default=None),
          "valid_json_pct": round(100 * sum(r.valid_json for r in measured) / len(measured), 1),
          "schema_valid_pct": round(100 * sum(r.schema_valid for r in measured) / len(measured), 1),
          "correct_products_pct": round(100 * sum(r.correct_products for r in measured) / (len(measured) * len(EXPECTED)), 1),
          "correct_quantities_pct": round(100 * sum(r.correct_quantities for r in measured) / (len(measured) * len(EXPECTED)), 1),
          "exact_match_pct": round(100 * sum(r.exact_match for r in measured) / len(measured), 1)})
    summary_fields = ["model", "params", "successful_runs", "avg_ttft_ms", "median_ttft_ms",
        "avg_total_latency_ms", "median_total_latency_ms", "min_total_latency_ms", "max_total_latency_ms",
        "avg_tokens_per_second", "avg_ollama_total_duration_ms", "avg_load_duration_ms",
        "avg_prompt_eval_duration_ms", "avg_eval_duration_ms", "avg_inference_duration_ms",
        "ram_peak_mb", "valid_json_pct", "schema_valid_pct",
        "correct_products_pct", "correct_quantities_pct", "exact_match_pct"]
    with (OUTPUT_DIRECTORY / "benchmark_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields); writer.writeheader(); writer.writerows(summary)
    if summary:
        print("\nModelo                         TTFT ms    Total ms    Infer ms   tok/s    RAM MB   JSON  Exact")
        print("-" * 98)
        for x in summary:
            print(f"{x['model']:<30} {x['avg_ttft_ms']!s:<10} {x['avg_total_latency_ms']!s:<11} {x['avg_inference_duration_ms']!s:<10} {x['avg_tokens_per_second']!s:<8} {x['ram_peak_mb']!s:<8} {x['valid_json_pct']!s:<5} {x['exact_match_pct']!s}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark controlado de modelos Ollama.")
    parser.add_argument(
        "--models", nargs="+", metavar="MODELO",
        help="Modelos a probar. Si se omite, se prueban todos los configurados.",
    )
    parser.add_argument(
        "--run-name", metavar="NOMBRE",
        help="Nombre de la corrida. Por defecto usa la fecha y hora actuales.",
    )
    parser.add_argument(
        "--runs", type=int, default=RUNS_PER_MODEL, metavar="N",
        help=f"Cantidad de pasadas medidas por modelo (por defecto: {RUNS_PER_MODEL}).",
    )
    parser.add_argument(
        "--groq", action="store_true",
        help="Incluye una corrida cloud de Groq usando GROQ_API_KEY.",
    )
    parser.add_argument(
        "--groq-only", action="store_true",
        help="Ejecuta únicamente Groq y omite todos los modelos locales.",
    )
    parser.add_argument(
        "--groq-model", default=GROQ_MODEL, metavar="MODELO",
        help=f"Modelo de Groq (por defecto: {GROQ_MODEL}).",
    )
    return parser.parse_args()


def create_run_directory(run_name: str | None) -> Path:
    base_name = run_name or datetime.now().strftime("run_%Y%m%d_%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", base_name).strip("._") or "run"
    candidate = OUTPUT_DIRECTORY / safe_name
    suffix = 2
    while candidate.exists():
        candidate = OUTPUT_DIRECTORY / f"{safe_name}_{suffix}"
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


def generate_report(run_directory: Path) -> None:
    try:
        from analyze_llm_benchmark import main as analyze_results_main
        result = analyze_results_main([
            "--results-directory", str(run_directory),
            "--report-file", str(run_directory / "benchmark_report.md"),
        ])
        if result != 0:
            print("No se pudo generar automáticamente el informe.", file=sys.stderr)
    except Exception as exc:
        print(f"No se pudo generar automáticamente el informe: {exc}", file=sys.stderr)


def main() -> int:
    global ACTIVE_MODELS, OUTPUT_DIRECTORY, RUNS_PER_MODEL
    args = parse_args()
    if args.runs < 1:
        print("--runs debe ser un entero mayor o igual a 1.", file=sys.stderr)
        return 2
    RUNS_PER_MODEL = args.runs
    if args.groq_only:
        args.groq = True
        ACTIVE_MODELS = {}
    if args.models:
        unknown = [model for model in args.models if model not in MODELS]
        if unknown:
            print("Modelos no configurados: " + ", ".join(unknown), file=sys.stderr)
            print("Modelos disponibles: " + ", ".join(MODELS), file=sys.stderr)
            return 2
        ACTIVE_MODELS = {model: MODELS[model] for model in dict.fromkeys(args.models)}
    OUTPUT_DIRECTORY = create_run_directory(args.run_name)
    try:
        installed = ({x["name"] for x in http_json("/api/tags").get("models", [])}
                     if ACTIVE_MODELS else set())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"No se puede conectar con Ollama en {OLLAMA_URL}: {exc}", file=sys.stderr); return 1
    available, missing = print_model_inventory(installed, ACTIVE_MODELS) if ACTIVE_MODELS else ([], [])
    groq_api_key = os.environ.get("GROQ_API_KEY") if args.groq else None
    if args.groq and not groq_api_key:
        print("Falta la variable de entorno GROQ_API_KEY.", file=sys.stderr)
        return 1
    if not available and not args.groq:
        print("No hay modelos configurados disponibles.", file=sys.stderr); return 1
    all_results: list[RunResult] = []
    for model in available:
        print(f"\n{model}: warm-up y {RUNS_PER_MODEL} ejecuciones...")
        for i in range(WARMUP_RUNS): all_results.append(run_once(model, ACTIVE_MODELS[model], i + 1, True))
        for i in range(RUNS_PER_MODEL):
            result = run_once(model, ACTIVE_MODELS[model], i + 1, False); all_results.append(result)
            print(f"  ejecución {i + 1}/{RUNS_PER_MODEL}: {result.status}")
            write_outputs(all_results)  # persiste incluso ante fallos/interrupciones posteriores
        unload(model)
    if args.groq and groq_api_key:
        groq_model = f"groq:{args.groq_model}"
        groq_params = "cloud"
        print(f"\n{groq_model}: warm-up y {RUNS_PER_MODEL} ejecuciones...")
        for i in range(WARMUP_RUNS):
            all_results.append(run_groq_once(groq_model, groq_params, i + 1, True, groq_api_key))
        for i in range(RUNS_PER_MODEL):
            result = run_groq_once(groq_model, groq_params, i + 1, False, groq_api_key)
            all_results.append(result)
            print(f"  ejecución {i + 1}/{RUNS_PER_MODEL}: {result.status}")
            write_outputs(all_results)
    write_outputs(all_results)
    print(f"\nResultados guardados en: {OUTPUT_DIRECTORY.resolve()}")
    generate_report(OUTPUT_DIRECTORY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
