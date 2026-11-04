"""Explain saved STT errors per prompt without running inference again."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

from stt_benchmark import normalize


def align_words(reference: str, hypothesis: str) -> list[dict]:
    """Minimum edit alignment; deterministic ties prefer substitution, then deletion."""
    ref, hyp = normalize(reference).split(), normalize(hypothesis).split()
    matrix = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        matrix[i][0] = i
    for j in range(len(hyp) + 1):
        matrix[0][j] = j
    for i, a in enumerate(ref, 1):
        for j, b in enumerate(hyp, 1):
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,
                matrix[i][j - 1] + 1,
                matrix[i - 1][j - 1] + (a != b),
            )
    errors = []
    i, j = len(ref), len(hyp)
    while i or j:
        if i and j and ref[i - 1] == hyp[j - 1]:
            i, j = i - 1, j - 1
        elif i and j and matrix[i][j] == matrix[i - 1][j - 1] + 1:
            errors.append(
                {
                    "type": "substitution",
                    "expected": ref[i - 1],
                    "returned": hyp[j - 1],
                    "reference_index": i - 1,
                    "hypothesis_index": j - 1,
                }
            )
            i, j = i - 1, j - 1
        elif i and matrix[i][j] == matrix[i - 1][j] + 1:
            errors.append(
                {
                    "type": "deletion",
                    "expected": ref[i - 1],
                    "returned": "",
                    "reference_index": i - 1,
                    "hypothesis_index": j,
                }
            )
            i -= 1
        else:
            errors.append(
                {
                    "type": "insertion",
                    "expected": "",
                    "returned": hyp[j - 1],
                    "reference_index": i,
                    "hypothesis_index": j - 1,
                }
            )
            j -= 1
    return errors[::-1]


def write_analysis(directory: Path) -> None:
    rows = json.loads((directory / "raw_transcriptions.json").read_text())
    measured = [r for r in rows if not r["warmup"]]
    details, csv_rows = [], []
    for row in measured:
        errors = align_words(row["expected_text"], row["text"])
        counts = {
            kind: sum(e["type"] == kind for e in errors)
            for kind in ["substitution", "deletion", "insertion"]
        }
        if row["word_errors"] is not None and len(errors) != row["word_errors"]:
            raise ValueError("Alignment does not match recorded WER")
        detail = {**row, **counts, "word_alignment_errors": errors}
        details.append(detail)
        csv_rows.append(
            {k: v for k, v in detail.items() if k != "word_alignment_errors"}
        )
    (directory / "prompt_errors.json").write_text(
        json.dumps(details, ensure_ascii=False, indent=2) + "\n"
    )
    if csv_rows:
        with (directory / "prompt_errors.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]))
            writer.writeheader()
            writer.writerows(csv_rows)
    configs = list(dict.fromkeys(r["configuration"] for r in measured))
    cases = list(dict.fromkeys(r["case_id"] for r in measured))
    stats = {}
    for config in configs:
        for case in cases:
            group = [
                r
                for r in details
                if r["configuration"] == config and r["case_id"] == case
            ]
            ok = [r for r in group if r["status"] == "ok"]
            if ok:
                stats[config, case] = {
                    "wer": statistics.mean(r["wer_pct"] for r in ok),
                    "cer": statistics.mean(r["cer_pct"] for r in ok),
                    "min": min(r["wer_pct"] for r in ok),
                    "max": max(r["wer_pct"] for r in ok),
                    "seconds": statistics.mean(r["inference_s"] for r in ok),
                    "substitution": statistics.mean(r["substitution"] for r in ok),
                    "deletion": statistics.mean(r["deletion"] for r in ok),
                    "insertion": statistics.mean(r["insertion"] for r in ok),
                }
    report = [
        "# Análisis STT por prompt",
        "",
        "Repeticiones medidas agrupadas por configuración; calentamientos excluidos.",
        (
            "Los textos esperados vienen de los prompts "
            "y requieren revisión humana del audio."
        ),
        (
            "WER estricto: números en palabras/dígitos, acentos y marcas "
            "cuentan como diferencias."
        ),
        "Las alineaciones explican diferencias textuales, no evalúan el significado.",
        "Una alineación mínima puede tener otras alternativas igualmente válidas.",
        "",
        "## WER medio por prompt (%)",
        "",
        "| Prompt | " + " | ".join(configs) + " |",
        "| --- | " + " | ".join("---" for _ in configs) + " |",
    ]
    for case in cases:
        report.append(
            "| "
            + case
            + " | "
            + " | ".join(
                f"{stats[config, case]['wer']:.2f}" if (config, case) in stats else "—"
                for config in configs
            )
            + " |"
        )
    report += ["", "## Casos con mayor WER por configuración", ""]
    for config in configs:
        ranked = sorted(
            [
                (case, stats[config, case]["wer"])
                for case in cases
                if (config, case) in stats
            ],
            key=lambda x: x[1],
            reverse=True,
        )
        report.append(
            f"- **{config}:** "
            + "; ".join(f"{case} ({wer:.2f} %)" for case, wer in ranked[:3])
        )
    for case in cases:
        reference = next(r["expected_text"] for r in measured if r["case_id"] == case)
        report += [
            "",
            f"## {case}",
            "",
            "**Texto esperado:**",
            "",
            "> " + reference,
            "",
            "| Configuración | WER medio | CER medio | WER min–max | "
            "Sustituciones | Omisiones | Agregados | Tiempo medio |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for config in configs:
            if (config, case) not in stats:
                continue
            s = stats[config, case]
            report.append(
                f"| {config} | {s['wer']:.2f} % | {s['cer']:.2f} % | "
                f"{s['min']:.2f}–{s['max']:.2f} % | {s['substitution']:.2f} | "
                f"{s['deletion']:.2f} | {s['insertion']:.2f} | {s['seconds']:.3f} s |"
            )
        report += ["", "Los conteos de la tabla son promedios de las repeticiones."]
        for config in configs:
            group = [
                r
                for r in details
                if r["configuration"] == config and r["case_id"] == case
            ]
            if not group:
                continue
            report += ["", f"### {config}", ""]
            variants = {}
            for row in group:
                variants.setdefault((row["status"], row["text"]), []).append(row)
            for (status, text), variant in variants.items():
                runs = ", ".join(str(r["run"]) for r in variant)
                report += [
                    f"**Repeticiones {runs} — estado: {status}**",
                    "",
                    "> " + (text or "[sin transcripción]"),
                    "",
                ]
                example = variant[0]
                if example["error"]:
                    report.append(f"Error de ejecución: {example['error']}")
                errors = example["word_alignment_errors"]
                if not errors:
                    report.append("Sin diferencias después de normalizar.")
                for label, kind in [
                    ("Sustituciones", "substitution"),
                    ("Omisiones", "deletion"),
                    ("Agregados", "insertion"),
                ]:
                    found = [e for e in errors if e["type"] == kind]
                    if not found:
                        continue
                    fragments = [
                        f"`{e['expected']}` → `{e['returned']}`"
                        if kind == "substitution"
                        else f"`{e['expected'] or e['returned']}`"
                        for e in found
                    ]
                    report.append(f"- **{label}:** " + "; ".join(fragments))
                report.append("")
    (directory / "prompt_analysis.md").write_text("\n".join(report) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-directory", required=True, type=Path)
    args = parser.parse_args()
    write_analysis(args.results_directory)
    print(f"Analysis: {args.results_directory / 'prompt_analysis.md'}")


if __name__ == "__main__":
    main()
