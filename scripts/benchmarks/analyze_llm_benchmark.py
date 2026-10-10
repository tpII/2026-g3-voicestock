"""Analiza los resultados producidos por llm_benchmark.py.

Uso: python scripts/benchmarks/analyze_llm_benchmark.py
Genera: reports/llm-benchmark/benchmark_report.md
"""

from __future__ import annotations

import argparse
import csv
import statistics
from pathlib import Path

from llm_benchmark import PROMPT

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIRECTORY = PROJECT_ROOT / "reports" / "llm-benchmark"
RUNS_FILE = RESULTS_DIRECTORY / "benchmark_runs.csv"
SUMMARY_FILE = RESULTS_DIRECTORY / "benchmark_summary.csv"
REPORT_FILE = RESULTS_DIRECTORY / "benchmark_report.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def number(row: dict[str, str], field: str) -> float | None:
    value = row.get(field, "")
    try:
        return float(value) if value != "" else None
    except ValueError:
        return None


def percent(value: float | None) -> str:
    return "N/D" if value is None else f"{value:.1f}%"


def ms(value: float | None) -> str:
    return "N/D" if value is None else f"{value:,.0f} ms"


def model_analysis(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    models = sorted({row.get("model", "") for row in rows if row.get("model")})
    analysis = []
    for model in models:
        measured = [
            row
            for row in rows
            if row.get("model") == model and row.get("warmup", "").lower() == "false"
        ]
        successful = [row for row in measured if row.get("status") == "ok"]
        exact = sum(row.get("exact_match", "").lower() == "true" for row in successful)
        valid_json = sum(
            row.get("valid_json", "").lower() == "true" for row in successful
        )
        schema_valid = sum(
            row.get("schema_valid", "").lower() == "true" for row in successful
        )
        total_values = [number(row, "total_latency_ms") for row in successful]
        total_values = [value for value in total_values if value is not None]
        speed_values = [number(row, "tokens_per_second") for row in successful]
        speed_values = [value for value in speed_values if value is not None]
        analysis.append(
            {
                "model": model,
                "params": next((row.get("params", "") for row in measured), ""),
                "runs": len(measured),
                "successful": len(successful),
                "exact_pct": 100 * exact / len(successful) if successful else None,
                "json_pct": 100 * valid_json / len(successful) if successful else None,
                "schema_pct": 100 * schema_valid / len(successful)
                if successful
                else None,
                "avg_total": statistics.mean(total_values) if total_values else None,
                "median_total": statistics.median(total_values)
                if total_values
                else None,
                "avg_speed": statistics.mean(speed_values) if speed_values else None,
                "ram_peak": max(
                    (
                        value
                        for value in (number(row, "ram_peak_mb") for row in successful)
                        if value is not None
                    ),
                    default=None,
                ),
            }
        )
    return analysis


def table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    render = [
        "| "
        + " | ".join(
            header.ljust(widths[index]) for index, header in enumerate(headers)
        )
        + " |",
        "| " + " | ".join("-" * width for width in widths) + " |",
    ]
    render.extend(
        "| "
        + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        + " |"
        for row in rows
    )
    return "\n".join(render)


def build_report(rows: list[dict[str, str]], models: list[dict[str, object]]) -> str:
    measured = [row for row in rows if row.get("warmup", "").lower() == "false"]
    errors = [row for row in measured if row.get("status") != "ok"]
    fastest = sorted(
        (model for model in models if model["avg_total"] is not None),
        key=lambda model: model["avg_total"],
    )
    most_accurate = sorted(
        (model for model in models if model["exact_pct"] is not None),
        key=lambda model: (-model["exact_pct"], model["avg_total"] or float("inf")),
    )
    rows_for_table = []
    for model in models:
        rows_for_table.append(
            [
                str(model["model"]),
                str(model["params"]),
                str(model["runs"]),
                percent(model["json_pct"]),
                percent(model["schema_pct"]),
                percent(model["exact_pct"]),
                ms(model["avg_total"]),
                f"{model['avg_speed']:.2f}"
                if model["avg_speed"] is not None
                else "N/D",
                f"{model['ram_peak']:.0f}" if model["ram_peak"] is not None else "N/D",
            ]
        )
    report = [
        "# Análisis del benchmark",
        "",
        "## Prompt utilizado",
        "",
        "```text",
        PROMPT,
        "```",
        "",
        "## Resumen",
        "",
        f"- Ejecuciones medidas analizadas: **{len(measured)}**",
        f"- Ejecuciones con error HTTP/cliente: **{len(errors)}**",
        "- Los warm-up fueron excluidos.",
        (
            "- `Total medio` es el promedio de `total_latency_m"
            "s`: desde que el cliente envía la solicitud hasta "
            "que recibe la respuesta completa."
        ),
        (
            "- En Groq incluye red y tiempo de respuesta extrem"
            "o a extremo; en Ollama corresponde al tiempo obser"
            "vado desde el cliente local."
        ),
        "- La velocidad y la latencia no se interpretan como calidad semántica.",
        "",
        "## Comparación por modelo",
        "",
        table(
            rows_for_table,
            [
                "Modelo",
                "Params",
                "Runs",
                "JSON",
                "Schema",
                "Exact",
                "Total medio",
                "Tok/s",
                "RAM pico MB",
            ],
        ),
        "",
        "## Lectura rápida",
        "",
    ]
    if fastest:
        report.append(
            (
                "- Menor latencia media: **"
                f"{fastest[0]['model']}"
                "** ("
                f"{ms(fastest[0]['avg_total'])}"
                ")."
            )
        )
    if most_accurate:
        report.append(
            (
                "- Mayor exact match: **"
                f"{most_accurate[0]['model']}"
                "** ("
                f"{percent(most_accurate[0]['exact_pct'])}"
                ")."
            )
        )
    report.extend(
        [
            (
                "- La elección final debe priorizar `exact_match` y"
                " luego contrastar latencia, velocidad y RAM."
            ),
            "",
            "## Alertas",
            "",
        ]
    )
    alerts = []
    for model in models:
        if model["exact_pct"] == 0:
            alerts.append(f"- **{model['model']}** no obtuvo ningún `exact_match`.")
        if model["json_pct"] is not None and model["json_pct"] < 100:
            alerts.append(
                f"- **{model['model']}** tuvo respuestas que no fueron JSON válido."
            )
        if model["schema_pct"] is not None and model["schema_pct"] < 100:
            alerts.append(
                f"- **{model['model']}** tuvo respuestas con esquema inválido."
            )
    if errors:
        alerts.append(
            "- Hay ejecuciones con error que deben revisarse en `benchmark_runs.csv`."
        )
    report.extend(
        alerts or ["- No se detectaron alertas con las métricas disponibles."]
    )
    return "\n".join(report) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analiza los resultados de una corrida del benchmark."
    )
    parser.add_argument("--results-directory", type=Path, default=RESULTS_DIRECTORY)
    parser.add_argument("--report-file", type=Path)
    args = parser.parse_args(argv)
    runs_file = args.results_directory / "benchmark_runs.csv"
    summary_file = args.results_directory / "benchmark_summary.csv"
    report_file = args.report_file or args.results_directory / "benchmark_report.md"
    missing = [path for path in (runs_file, summary_file) if not path.exists()]
    if missing:
        print("Faltan archivos: " + ", ".join(str(path) for path in missing))
        return 1
    rows = read_csv(runs_file)
    models = model_analysis(rows)
    report_file.write_text(build_report(rows, models), encoding="utf-8")
    print(f"Informe generado: {report_file.resolve()}")
    print(
        (
            "Modelos analizados: "
            f"{len(models)}"
            " | Ejecuciones medidas: "
            f"{sum((model['runs'] for model in models))}"
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
