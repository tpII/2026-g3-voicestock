"""Benchmark de precisión para interpretar operaciones de inventario."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIRECTORY = PROJECT_ROOT / "reports" / "llm-benchmark"
PROMPTS_DIRECTORY = Path(__file__).resolve().parent / "prompts" / "precision"
OLLAMA_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen3:4b-instruct"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "qwen/qwen3.8-27b"
GROQ_GPT_OSS_MODELS = {"openai/gpt-oss-20b", "openai/gpt-oss-120b"}
GROQ_MAX_COMPLETION_TOKENS = 1000
GROQ_CASE_DELAY_SECONDS = 5
GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]
TEMPERATURE = 0
TIMEOUT_SECONDS = 180
GEMINI_RETRY_FALLBACK_SECONDS = 30
GEMINI_UNAVAILABLE_RETRY_SECONDS = 5
GEMINI_MODEL_DELAY_SECONDS = 30
GEMINI_MAX_RETRIES = 4
GEMINI_THINKING_LEVELS = {
    "gemini-3.8-flash": "low",
    "gemini-3.7-flash": "low",
}

PRODUCTS = [
    "Coca Cola 2L",
    "Coca Cola 1.5L",
    "Coca Cola Zero 2L",
    "Sprite 2L",
    "Sprite 1.5L",
    "Agua Villavicencio 1.5L",
    "Arroz Gallo 1kg",
    "Fideos Matarazzo 500g",
    "Detergente Magistral 750ml",
    "Leche La Serenísima 1L",
]

PRODUCT_DETAILS = {
    "Coca Cola 2L": "tipo: común; tamaño: 2 L",
    "Coca Cola 1.5L": "tipo: común; tamaño: 1,5 L",
    "Coca Cola Zero 2L": "tipo: Zero; tamaño: 2 L",
    "Sprite 2L": "tipo: común; tamaño: 2 L",
    "Sprite 1.5L": "tipo: común; tamaño: 1,5 L",
    "Agua Villavicencio 1.5L": "tipo: agua; tamaño: 1,5 L",
    "Arroz Gallo 1kg": "tipo: arroz Gallo; paquete de 1 kg",
    "Fideos Matarazzo 500g": "tipo: fideos Matarazzo; paquete de 500 g",
    "Detergente Magistral 750ml": "tipo: detergente Magistral; envase de 750 ml",
    "Leche La Serenísima 1L": "tipo: leche La Serenísima; envase de 1 L",
}

JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "operaciones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "operacion": {
                        "type": "string",
                        "enum": ["agregar_stock", "restar_stock"],
                    },
                    "producto": {"type": "string", "enum": PRODUCTS},
                    "cantidad": {"type": "integer", "minimum": 1},
                },
                "required": ["operacion", "producto", "cantidad"],
            },
        }
    },
    "required": ["operaciones"],
}
GROQ_JSON_SCHEMA = {
    **JSON_SCHEMA,
    "additionalProperties": False,
    "properties": {
        "operaciones": {
            **JSON_SCHEMA["properties"]["operaciones"],
            "items": {
                **JSON_SCHEMA["properties"]["operaciones"]["items"],
                "additionalProperties": False,
            },
        },
    },
}


def load_prompt_file(filename: str) -> str:
    return (PROMPTS_DIRECTORY / filename).read_text(encoding="utf-8").strip()


PROMPT_CONTRACT = load_prompt_file("contract.txt")


@dataclass(frozen=True)
class PrecisionCase:
    case_id: str
    message: str
    expected: dict[str, list[dict[str, str | int]]]


CASES = [
    PrecisionCase(
        "solo_agregar",
        load_prompt_file("solo_agregar.txt"),
        {
            "operaciones": [
                {
                    "operacion": "agregar_stock",
                    "producto": "Coca Cola 2L",
                    "cantidad": 3,
                },
                {
                    "operacion": "agregar_stock",
                    "producto": "Sprite 1.5L",
                    "cantidad": 4,
                },
            ]
        },
    ),
    PrecisionCase(
        "solo_restar",
        load_prompt_file("solo_restar.txt"),
        {
            "operaciones": [
                {
                    "operacion": "restar_stock",
                    "producto": "Arroz Gallo 1kg",
                    "cantidad": 2,
                },
            ]
        },
    ),
    PrecisionCase(
        "negar_agregacion",
        load_prompt_file("negar_agregacion.txt"),
        {"operaciones": []},
    ),
    PrecisionCase(
        "negar_restacion",
        load_prompt_file("negar_restacion.txt"),
        {"operaciones": []},
    ),
    PrecisionCase(
        "restar_ambos",
        load_prompt_file("restar_ambos.txt"),
        {
            "operaciones": [
                {
                    "operacion": "restar_stock",
                    "producto": "Coca Cola Zero 2L",
                    "cantidad": 2,
                },
                {
                    "operacion": "restar_stock",
                    "producto": "Detergente Magistral 750ml",
                    "cantidad": 4,
                },
            ]
        },
    ),
    PrecisionCase(
        "corregir_cantidad",
        load_prompt_file("corregir_cantidad.txt"),
        {
            "operaciones": [
                {
                    "operacion": "agregar_stock",
                    "producto": "Coca Cola 2L",
                    "cantidad": 2,
                },
            ]
        },
    ),
    PrecisionCase(
        "negar_agregacion_y_restacion",
        load_prompt_file("negar_agregacion_y_restacion.txt"),
        {"operaciones": []},
    ),
    PrecisionCase(
        "negar_varias_agregaciones",
        load_prompt_file("negar_varias_agregaciones.txt"),
        {
            "operaciones": [
                {
                    "operacion": "agregar_stock",
                    "producto": "Arroz Gallo 1kg",
                    "cantidad": 5,
                },
            ]
        },
    ),
    PrecisionCase(
        "negar_varias_restaciones",
        load_prompt_file("negar_varias_restaciones.txt"),
        {
            "operaciones": [
                {
                    "operacion": "restar_stock",
                    "producto": "Detergente Magistral 750ml",
                    "cantidad": 4,
                },
            ]
        },
    ),
    PrecisionCase(
        "caso_integral",
        load_prompt_file("caso_integral.txt"),
        {
            "operaciones": [
                {
                    "operacion": "agregar_stock",
                    "producto": "Coca Cola 2L",
                    "cantidad": 2,
                },
                {
                    "operacion": "restar_stock",
                    "producto": "Arroz Gallo 1kg",
                    "cantidad": 2,
                },
                {
                    "operacion": "restar_stock",
                    "producto": "Fideos Matarazzo 500g",
                    "cantidad": 3,
                },
            ]
        },
    ),
]


@dataclass
class PrecisionResult:
    provider: str
    model: str
    case_id: str
    status: str
    error: str | None
    latency_ms: float | None
    prompt_tokens: int | None
    output_tokens: int | None
    tokens_per_second: float | None
    valid_json: bool
    schema_valid: bool
    correct_operation: bool
    correct_product: bool
    correct_quantity: bool
    exact_match: bool
    expected_json: str
    raw_response: str


def prompt_for(case: PrecisionCase) -> str:
    products = "\n".join(
        f"- Nombre exacto: {product}; {PRODUCT_DETAILS[product]}"
        for product in PRODUCTS
    )
    return PROMPT_CONTRACT.format(products=products, message=case.message)


def evaluate(
    raw: str,
    expected: dict[str, list[dict[str, str | int]]],
) -> dict[str, bool]:
    try:
        decoded = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {
            "valid_json": False,
            "schema_valid": False,
            "correct_operation": False,
            "correct_product": False,
            "correct_quantity": False,
            "exact_match": False,
        }
    operations = decoded.get("operaciones") if isinstance(decoded, dict) else None
    schema_valid = (
        isinstance(decoded, dict)
        and set(decoded) == {"operaciones"}
        and isinstance(operations, list)
        and all(
            isinstance(operation, dict)
            and set(operation) == {"operacion", "producto", "cantidad"}
            and operation.get("operacion") in {"agregar_stock", "restar_stock"}
            and operation.get("producto") in PRODUCTS
            and isinstance(operation.get("cantidad"), int)
            and not isinstance(operation.get("cantidad"), bool)
            and operation["cantidad"] > 0
            for operation in operations
        )
    )
    expected_operations = expected["operaciones"]
    correct_operation = schema_valid and [
        operation["operacion"] for operation in operations
    ] == [operation["operacion"] for operation in expected_operations]
    correct_product = schema_valid and [
        operation["producto"] for operation in operations
    ] == [operation["producto"] for operation in expected_operations]
    correct_quantity = schema_valid and [
        operation["cantidad"] for operation in operations
    ] == [operation["cantidad"] for operation in expected_operations]
    return {
        "valid_json": True,
        "schema_valid": schema_valid,
        "correct_operation": correct_operation,
        "correct_product": correct_product,
        "correct_quantity": correct_quantity,
        "exact_match": schema_valid and decoded == expected,
    }


def error_result(
    provider: str, model: str, case: PrecisionCase, error: str
) -> PrecisionResult:
    return PrecisionResult(
        provider=provider,
        model=model,
        case_id=case.case_id,
        status="error",
        error=error,
        latency_ms=None,
        prompt_tokens=None,
        output_tokens=None,
        tokens_per_second=None,
        valid_json=False,
        schema_valid=False,
        correct_operation=False,
        correct_product=False,
        correct_quantity=False,
        exact_match=False,
        expected_json=json.dumps(case.expected, ensure_ascii=False),
        raw_response="",
    )


def run_ollama(model: str, case: PrecisionCase, output_format: str) -> PrecisionResult:
    started = time.perf_counter()
    try:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt_for(case),
            "stream": False,
            "think": False,
            "options": {"temperature": TEMPERATURE},
        }
        if output_format == "schema":
            payload["format"] = JSON_SCHEMA
        elif output_format == "json":
            payload["format"] = "json"
        request = urllib.request.Request(
            OLLAMA_URL + "/api/generate",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        ended = time.perf_counter()
        raw = body.get("response", "")
        output_tokens = body.get("eval_count")
        eval_duration = body.get("eval_duration")
        tokens_per_second = (
            round(output_tokens / (eval_duration / 1e9), 3)
            if output_tokens and eval_duration
            else None
        )
        return PrecisionResult(
            provider="ollama",
            model=model,
            case_id=case.case_id,
            status="ok",
            error=None,
            latency_ms=round((ended - started) * 1000, 2),
            prompt_tokens=body.get("prompt_eval_count"),
            output_tokens=output_tokens,
            tokens_per_second=tokens_per_second,
            expected_json=json.dumps(case.expected, ensure_ascii=False),
            raw_response=raw,
            **evaluate(raw, case.expected),
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        return error_result("ollama", model, case, str(exc))


def run_groq(model: str, case: PrecisionCase, api_key: str) -> PrecisionResult:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_for(case)}],
        "temperature": TEMPERATURE,
        "reasoning_effort": "low" if model in GROQ_GPT_OSS_MODELS else "none",
        "max_completion_tokens": GROQ_MAX_COMPLETION_TOKENS,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "operaciones_inventario",
                "strict": True,
                "schema": GROQ_JSON_SCHEMA,
            },
        },
    }
    request = urllib.request.Request(
        GROQ_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "llm-to-json-benchmark/1.0",
        },
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        elapsed_seconds = time.perf_counter() - started
        raw = body["choices"][0]["message"]["content"] or ""
        usage = body.get("usage") or {}
        output_tokens = usage.get("completion_tokens")
        tokens_per_second = (
            round(output_tokens / elapsed_seconds, 3)
            if output_tokens and elapsed_seconds > 0
            else None
        )
        return PrecisionResult(
            provider="groq",
            model=model,
            case_id=case.case_id,
            status="ok",
            error=None,
            latency_ms=round(elapsed_seconds * 1000, 2),
            prompt_tokens=usage.get("prompt_tokens"),
            output_tokens=output_tokens,
            tokens_per_second=tokens_per_second,
            expected_json=json.dumps(case.expected, ensure_ascii=False),
            raw_response=raw,
            **evaluate(raw, case.expected),
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        return error_result("groq", model, case, f"HTTP {exc.code}: {detail}")
    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        OSError,
        KeyError,
        IndexError,
        TypeError,
    ) as exc:
        return error_result("groq", model, case, str(exc))


def gemini_retry_delay(error: str) -> float:
    match = re.search(r"retry in ([0-9.]+)s", error, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1
    return GEMINI_RETRY_FALLBACK_SECONDS


def run_gemini(client: Any, model: str, case: PrecisionCase) -> PrecisionResult:
    from google.genai import types

    thinking_level = GEMINI_THINKING_LEVELS.get(model, "minimal")
    for attempt in range(GEMINI_MAX_RETRIES + 1):
        started = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt_for(case),
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=JSON_SCHEMA,
                    thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
                ),
            )
            ended = time.perf_counter()
            raw = response.text or ""
            usage = response.usage_metadata
            output_tokens = getattr(usage, "candidates_token_count", None)
            elapsed_seconds = ended - started
            tokens_per_second = (
                round(output_tokens / elapsed_seconds, 3)
                if output_tokens and elapsed_seconds > 0
                else None
            )
            return PrecisionResult(
                provider="gemini",
                model=model,
                case_id=case.case_id,
                status="ok",
                error=None,
                latency_ms=round(elapsed_seconds * 1000, 2),
                prompt_tokens=getattr(usage, "prompt_token_count", None),
                output_tokens=output_tokens,
                tokens_per_second=tokens_per_second,
                expected_json=json.dumps(case.expected, ensure_ascii=False),
                raw_response=raw,
                **evaluate(raw, case.expected),
            )
        except Exception as exc:
            error = str(exc)
            is_rate_limit = "429" in error or "RESOURCE_EXHAUSTED" in error
            is_unavailable = "503" in error or "UNAVAILABLE" in error
            if (is_rate_limit or is_unavailable) and attempt < GEMINI_MAX_RETRIES:
                if is_rate_limit:
                    delay = gemini_retry_delay(error)
                    reason = "cuota agotada"
                else:
                    delay = GEMINI_UNAVAILABLE_RETRY_SECONDS * (2**attempt)
                    reason = "servicio no disponible (503)"
                print(
                    (
                        "  "
                        f"{reason}"
                        "; reintento "
                        f"{attempt + 1}"
                        "/"
                        f"{GEMINI_MAX_RETRIES}"
                        " en "
                        f"{delay:.1f}"
                        " s"
                    )
                )
                time.sleep(delay)
                continue
            return error_result("gemini", model, case, error)
    return error_result("gemini", model, case, "Se agotaron los reintentos.")


def percentage(results: list[PrecisionResult], field: str) -> float:
    if not results:
        return 0.0
    correct = sum(bool(getattr(result, field)) for result in results)
    return round(100 * correct / len(results), 1)


def build_summary(
    results: list[PrecisionResult],
) -> list[dict[str, str | int | float | None]]:
    summary = []
    model_keys = sorted({(result.provider, result.model) for result in results})
    for provider, model in model_keys:
        model_results = [
            result
            for result in results
            if result.provider == provider and result.model == model
        ]
        successful = [result for result in model_results if result.status == "ok"]
        latencies = [
            result.latency_ms for result in successful if result.latency_ms is not None
        ]
        speeds = [
            result.tokens_per_second
            for result in successful
            if result.tokens_per_second is not None
        ]
        summary.append(
            {
                "provider": provider,
                "model": model,
                "cases": len(model_results),
                "successful": len(successful),
                "request_success_pct": round(
                    100 * len(successful) / len(model_results), 1
                ),
                "valid_json_pct": percentage(successful, "valid_json"),
                "schema_valid_pct": percentage(successful, "schema_valid"),
                "correct_operation_pct": percentage(successful, "correct_operation"),
                "correct_product_pct": percentage(successful, "correct_product"),
                "correct_quantity_pct": percentage(successful, "correct_quantity"),
                "exact_match_pct": percentage(successful, "exact_match"),
                "end_to_end_exact_pct": percentage(model_results, "exact_match"),
                "avg_latency_ms": (
                    round(statistics.mean(latencies), 2) if latencies else None
                ),
                "median_latency_ms": (
                    round(statistics.median(latencies), 2) if latencies else None
                ),
                "avg_tokens_per_second": (
                    round(statistics.mean(speeds), 3) if speeds else None
                ),
            }
        )
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def write_report(
    output_directory: Path,
    results: list[PrecisionResult],
    summary: list[dict[str, Any]],
    ollama_format: str,
    contract_filename: str,
    cases: list[PrecisionCase],
) -> None:
    model_rows = [
        [
            str(row["provider"]),
            str(row["model"]),
            str(row["cases"]),
            str(row["successful"]),
            f"{row['request_success_pct']:.1f}%",
            f"{row['valid_json_pct']:.1f}%",
            f"{row['schema_valid_pct']:.1f}%",
            f"{row['correct_operation_pct']:.1f}%",
            f"{row['correct_product_pct']:.1f}%",
            f"{row['correct_quantity_pct']:.1f}%",
            f"{row['exact_match_pct']:.1f}%",
            f"{row['end_to_end_exact_pct']:.1f}%",
            str(row["avg_latency_ms"] or "N/D"),
            str(row["avg_tokens_per_second"] or "N/D"),
        ]
        for row in summary
    ]
    case_results = {
        (result.provider, result.model, result.case_id): result for result in results
    }
    case_headers = ["Proveedor", "Modelo"] + [case.case_id for case in cases]
    case_rows = []
    for provider, model in sorted(
        {(result.provider, result.model) for result in results}
    ):
        row = [provider, model]
        for case in cases:
            result = case_results.get((provider, model, case.case_id))
            row.append(
                "Sí"
                if result and result.status == "ok" and result.exact_match
                else "No"
            )
        case_rows.append(row)
    failed_rows = [
        [
            result.provider,
            result.model,
            result.case_id,
            result.error or "respuesta incorrecta",
        ]
        for result in results
        if result.status != "ok" or not result.exact_match
    ]
    report = [
        "# Benchmark de precisión de interpretación",
        "",
        "## Contrato JSON",
        "",
        "```json",
        (
            '{"operaciones":[{"operacion":"agregar_stock|restar'
            '_stock","producto":"nombre canónico","cantidad":1}'
            "]}"
        ),
        "```",
        "",
        f"- Contrato utilizado: `{contract_filename}`.",
        f"- Ollama se ejecuta con `think: false` y formato `{ollama_format}`.",
        "- Gemini 3.7 Flash y 3.8 Flash se ejecutan con `thinking_level: low`.",
        "- Los demás modelos Gemini se ejecutan con `thinking_level: minimal`.",
        "- Todos los proveedores usan temperatura 0.",
        (
            "- Gemini y Groq restringen la salida con schema; O"
            "llama usa el modo indicado arriba."
        ),
        (
            "- Groq usa `reasoning_effort: low` para GPT-OSS y "
            "`none` para Qwen; schema estricto."
        ),
        "- Las métricas marcadas con `*` se calculan solo sobre solicitudes exitosas.",
        (
            "- `Exact total` incluye los errores de API y repre"
            "senta el resultado de punta a punta."
        ),
        "",
        "## Resultados por modelo",
        "",
        markdown_table(
            [
                "Proveedor",
                "Modelo",
                "Casos",
                "Exitosas",
                "API OK",
                "JSON*",
                "Schema*",
                "Operación*",
                "Producto*",
                "Cantidad*",
                "Exact*",
                "Exact total",
                "Latencia ms",
                "Tok/s",
            ],
            model_rows,
        ),
        "",
        "## Resultado por caso",
        "",
        (
            "`Sí` significa que la respuesta coincidió exactame"
            "nte con la salida esperada; `No` indica que el cas"
            "o falló o que la solicitud no se completó."
        ),
        "",
        markdown_table(case_headers, case_rows),
        "",
        "## Casos evaluados",
        "",
    ]
    for case in cases:
        report.extend(
            [
                f"### {case.case_id}",
                "",
                case.message,
                "",
                "```json",
                json.dumps(case.expected, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    report.extend(["## Errores y respuestas no exactas", ""])
    if failed_rows:
        report.append(
            markdown_table(["Proveedor", "Modelo", "Caso", "Detalle"], failed_rows)
        )
    else:
        report.append("Todos los modelos obtuvieron exact match en todos los casos.")
    (output_directory / "benchmark_report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )


def write_outputs(
    output_directory: Path,
    results: list[PrecisionResult],
    ollama_format: str,
    contract_filename: str,
    cases: list[PrecisionCase],
) -> None:
    output_directory.mkdir(parents=True, exist_ok=False)
    result_rows = [asdict(result) for result in results]
    summary = build_summary(results)
    write_csv(output_directory / "benchmark_runs.csv", result_rows)
    write_csv(output_directory / "benchmark_summary.csv", summary)
    (output_directory / "raw_responses.json").write_text(
        json.dumps(result_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(
        output_directory,
        results,
        summary,
        ollama_format,
        contract_filename,
        cases,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark de precisión de interpretación."
    )
    parser.add_argument(
        "--provider", choices=["all", "ollama", "gemini", "groq"], default="all"
    )
    parser.add_argument("--ollama-model", default=OLLAMA_MODEL)
    parser.add_argument("--groq-model", default=GROQ_MODEL)
    parser.add_argument(
        "--ollama-format",
        choices=["schema", "json", "none", "all"],
        default="schema",
        help="Control de salida enviado a Ollama: schema, json, ninguno o todos.",
    )
    parser.add_argument(
        "--gemini-models", nargs="+", choices=GEMINI_MODELS, default=GEMINI_MODELS
    )
    parser.add_argument(
        "--cases",
        nargs="+",
        choices=[case.case_id for case in CASES],
        help="IDs de los casos a probar, separados por espacios (por defecto: todos).",
    )
    parser.add_argument(
        "--contract",
        choices=sorted(path.name for path in PROMPTS_DIRECTORY.glob("contract*.txt")),
        default="contract.txt",
        help="Archivo de contrato ubicado en la carpeta de prompts.",
    )
    parser.add_argument("--run-name")
    args = parser.parse_args()
    selected_cases = (
        [case for case in CASES if case.case_id in args.cases]
        if args.cases is not None
        else CASES
    )

    global PROMPT_CONTRACT
    PROMPT_CONTRACT = load_prompt_file(args.contract)

    if args.ollama_format == "all" and args.provider != "ollama":
        parser.error("--ollama-format all requiere --provider ollama")

    gemini_client = None
    if args.provider in {"all", "gemini"}:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Falta la variable de entorno GEMINI_API_KEY.")
            return 1
        try:
            from google import genai
        except ImportError:
            print('Falta google-genai. Instalá con: python -m pip install ".[gemini]"')
            return 1
        gemini_client = genai.Client(api_key=api_key)

    groq_api_key = None
    if args.provider == "groq":
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            print("Falta la variable de entorno GROQ_API_KEY.")
            return 1

    run_name = args.run_name or datetime.now().strftime("precision_%Y%m%d_%H%M%S")
    output_directory = REPORTS_DIRECTORY / run_name
    results: list[PrecisionResult] = []

    if args.provider in {"all", "ollama"}:
        ollama_formats = (
            ["none", "json", "schema"]
            if args.ollama_format == "all"
            else [args.ollama_format]
        )
        for ollama_format in ollama_formats:
            format_results: list[PrecisionResult] = []
            for case in selected_cases:
                print(f"ollama/{args.ollama_model} [{ollama_format}]: {case.case_id}")
                format_results.append(
                    run_ollama(args.ollama_model, case, ollama_format)
                )
            if args.ollama_format == "all":
                write_outputs(
                    output_directory / ollama_format,
                    format_results,
                    ollama_format,
                    args.contract,
                    selected_cases,
                )
            else:
                results.extend(format_results)

        if args.ollama_format == "all":
            print(f"Resultados guardados en: {output_directory.resolve()}")
            return 0

    if args.provider in {"all", "gemini"}:
        for model_index, model in enumerate(args.gemini_models):
            for case in selected_cases:
                print(f"gemini/{model}: {case.case_id}")
                results.append(run_gemini(gemini_client, model, case))
            if model_index < len(args.gemini_models) - 1:
                print(
                    (
                        "Pausa de "
                        f"{GEMINI_MODEL_DELAY_SECONDS}"
                        " s antes del siguiente modelo."
                    )
                )
                time.sleep(GEMINI_MODEL_DELAY_SECONDS)

    if args.provider == "groq":
        for case_index, case in enumerate(selected_cases):
            if case_index:
                print(f"Pausa de {GROQ_CASE_DELAY_SECONDS} s antes del siguiente caso.")
                time.sleep(GROQ_CASE_DELAY_SECONDS)
            print(f"groq/{args.groq_model}: {case.case_id}")
            results.append(run_groq(args.groq_model, case, groq_api_key))

    write_outputs(
        output_directory,
        results,
        args.ollama_format,
        args.contract,
        selected_cases,
    )
    print(f"Resultados guardados en: {output_directory.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
