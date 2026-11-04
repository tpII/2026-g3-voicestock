"""Summarize recorded STT metrics and explicit manual meaning reviews by level."""

import csv
import hashlib
import json

from prompt_levels import LEVELS
from stt_benchmark import ROOT


def main():
    review_path = ROOT / "scripts/benchmarks/reviews/stt_semantic_levels.json"
    review = json.loads(review_path.read_text())
    source = ROOT / review["source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != review["source_sha256"]:
        raise ValueError("Transcriptions changed: manual review must be renewed")
    rows = json.loads(source.read_text())
    destination = source.parent
    summaries = []
    lines = [
        "# Sentido de las transcripciones por dificultad",
        "",
        "Revisión cualitativa manual de 10 prompts, 8 configuraciones y "
        "240 transcripciones medidas. No se repitió inferencia.",
        "Las tres repeticiones cuentan como un solo caso por modelo; "
        "se revisaron todas las variantes y se adopta la más problemática.",
        "",
        "- Coherente: operación final, cantidad y artículo activo reconocibles.",
        "- Ambigua: necesita interpretar nombres o expresiones deformadas.",
        "- Sentido comprometido: pierde/cambia acción, cantidad, corrección "
        "o una prohibición explícita.",
        "",
        "Números escritos con palabras y unidades equivalentes se aceptan. "
        "Errores de nombres cancelados no invalidan una cancelación total clara. "
        "Los nombres activos dudosos se califican como ambiguos.",
        "No se escuchó el audio ni se validó un parser. Estos porcentajes son "
        "juicios sobre este corpus, no probabilidades de fiabilidad.",
        "",
        "## Corpus",
        "",
    ]
    for level in ["basico", "habitual", "exigente"]:
        cases = [case for case, value in LEVELS.items() if value == level]
        lines.append(f"- **{level}** ({len(cases)}): " + ", ".join(cases))
    lines += [
        "",
        "## Resumen",
        "",
        "Cada celda: coherentes / ambiguos / comprometidos (porcentaje coherente).",
        "",
        "| Modelo | Básico (2) | Habitual (4) | Exigente (4) |",
        "| --- | --- | --- | --- |",
    ]
    models = list(dict.fromkeys(item["configuration"] for item in review["cases"]))
    for model in models:
        cells = []
        for level in ["basico", "habitual", "exigente"]:
            items = [
                item
                for item in review["cases"]
                if item["configuration"] == model and item["level"] == level
            ]
            selected = [
                row
                for row in rows
                if row["configuration"] == model
                and LEVELS[row["case_id"]] == level
                and not row["warmup"]
            ]
            counts = [
                sum(item["assessment"] == status for item in items)
                for status in ["coherente", "ambigua", "sentido_comprometido"]
            ]
            percent = 100 * counts[0] / len(items)
            cells.append(" / ".join(map(str, counts)) + f" ({percent:.0f}%)")
            summaries.append(
                {
                    "configuration": model,
                    "level": level,
                    "cases": len(items),
                    "coherent": counts[0],
                    "ambiguous": counts[1],
                    "compromised": counts[2],
                    "coherent_pct": percent,
                    "wer_pct": 100
                    * sum(r["word_errors"] for r in selected)
                    / sum(r["reference_words"] for r in selected),
                    "cer_pct": 100
                    * sum(r["char_errors"] for r in selected)
                    / sum(r["reference_chars"] for r in selected),
                }
            )
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Interpretación",
        "",
        "Whisper Small Q5 conserva el sentido inequívoco en todos los casos "
        "básicos y habituales. Moonshine Small también conserva todos los "
        "habituales, pero deforma Sprite en el básico de agregar. "
        "Esto matiza la recomendación general anterior: con este criterio "
        "explícito, Whisper Small lidera básico/habitual.",
        "En exigente no hay ganador suficiente: Whisper Small y Moonshine Small "
        "tienen un caso coherente cada uno, y errores críticos en otros. "
        "Kroko conserva mejor la estructura del integral, pero un nombre activo "
        "dudoso impide calificarlo como inequívoco. No se descarta Kroko; "
        "se distingue preservación de instrucciones de identificación precisa.",
        "",
        "## Detalle por prompt",
        "",
    ]
    for case in LEVELS:
        items = [item for item in review["cases"] if item["case_id"] == case]
        lines += [
            f"### {case} — {LEVELS[case]}",
            "",
            "**Referencia:** " + items[0]["expected_text"],
            "",
        ]
        for item in items:
            lines += [
                f"**{item['configuration']}: {item['assessment']}** — "
                + item["reason"],
                "",
            ]
            for text in item["transcriptions"]:
                lines += ["> " + text.strip(), ""]
    (destination / "level_analysis.md").write_text("\n".join(lines) + "\n")
    with (destination / "level_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    (destination / "level_reviews.json").write_text(
        json.dumps(review, ensure_ascii=False, indent=2) + "\n"
    )
    print(destination / "level_analysis.md")


if __name__ == "__main__":
    main()
