"""Combine compatible saved STT runs, retaining source provenance."""

import argparse
import csv
import json
import time
from pathlib import Path

from stt_benchmark import ROOT, write_outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-directories", type=Path, nargs="+", required=True)
    args = parser.parse_args()
    rows, loads, sources = [], [], []
    configurations = set()
    baseline = None
    for directory in args.results_directories:
        environment = json.loads((directory / "environment.json").read_text())
        if baseline is None:
            baseline = environment
        for key in [
            "platform",
            "python",
            "runs",
            "warmups_per_audio",
            "threads_whisper",
            "whisper_settings",
            "whisper_commit",
            "manifest_sha256",
        ]:
            if environment[key] != baseline[key]:
                raise ValueError(f"Incompatible {key} in {directory}")
        saved = json.loads((directory / "raw_transcriptions.json").read_text())
        names = {row["configuration"] for row in saved}
        if names & configurations:
            raise ValueError(
                "Duplicate configurations; compare separate runs explicitly"
            )
        configurations.update(names)
        for row in saved:
            row["source_run"] = str(directory)
        rows.extend(saved)
        with (directory / "benchmark_summary.csv").open() as stream:
            for summary in csv.DictReader(stream):
                loads.append(
                    {
                        "configuration": summary["configuration"],
                        "load_s": float(summary["load_s"]),
                        "load_ram_peak_mib": float(summary["load_ram_peak_mib"]),
                    }
                )
        sources.append({"directory": str(directory), "environment": environment})
    destination = (
        ROOT / "reports/stt-benchmark" / time.strftime("comparison_%Y%m%d_%H%M%S")
    )
    destination.mkdir(parents=True, exist_ok=False)
    metadata = {
        **baseline,
        "source_runs": sources,
        "comparison_note": "Saved runs at different times; machine load may differ.",
    }
    write_outputs(destination, rows, loads, metadata)
    report = destination / "benchmark_report.md"
    report.write_text(
        report.read_text()
        + "\n## Source runs\n\n"
        + "\n".join(f"- `{source['directory']}`" for source in sources)
        + "\n\nExecuted at different times; timings may reflect machine load.\n"
    )
    print(f"Comparison: {destination}")


if __name__ == "__main__":
    main()
