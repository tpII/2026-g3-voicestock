"""PC coordinator: transfer prompt WAVs, run Pi STT over SSH, then call Groq."""

import argparse
import csv
import hashlib
import json
import os
import re
import selectors
import shlex
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/benchmarks"))
MODEL = "openai/gpt-oss-20b"


def receive(process, timeout):
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        if not selector.select(timeout):
            raise TimeoutError("Remote STT did not respond before timeout")
    line = process.stdout.readline()
    if not line:
        raise RuntimeError("SSH worker stopped; inspect ssh.log")
    result = json.loads(line)
    if result.get("event") == "fatal":
        raise RuntimeError(result["error"])
    return result


def save(out, rows, metadata):
    (out / "results.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    )
    (out / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    flat = [
        {
            "case_id": r["case_id"],
            "level": r["level"],
            "status": r["status"],
            **r.get("evaluation", {}),
            "pi_stt_peak_mib": r.get("remote_stt", {})
            .get("resources", {})
            .get("ram_peak_mib"),
            "pc_api_client_peak_mib": r.get("api_resources", {}).get("ram_peak_mib"),
            "pi_stt_s": r.get("remote_stt", {})
            .get("resources", {})
            .get("request_wall_s"),
            "llm_api_s": r.get("api_resources", {}).get("request_wall_s"),
            "pi_cpu_pct": r.get("remote_stt", {}).get("resources", {}).get("cpu_pct"),
            "error": r.get("error"),
        }
        for r in rows
    ]
    if flat:
        with (out / "benchmark_cases.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=list(dict.fromkeys(k for r in flat for k in r))
            )
            writer.writeheader()
            writer.writerows(flat)
    exact = sum(r.get("evaluation", {}).get("exact_match", False) for r in rows)
    lines = [
        "# Raspberry STT → SSH → PC Groq integration",
        "",
        f"Whisper {metadata['stt_model']} on remote host → {MODEL} from PC.",
        f"Exact JSON: {exact}/{len(rows)} processed; six expected cases.",
        "One transcription and one API request per case; no warm-up or retries.",
        (
            "Pi STT resources cover the Whisper process; "
            "PC resources cover the Python coordinator."
        ),
        (
            "Remote Groq model RAM is not observable. "
            "References require human audio verification."
        ),
        "SSH/scp configuration and host hardware are recorded in environment.json.",
        "No microphone capture or inventory updates occur in this fixture experiment.",
    ]
    expected_count = len(metadata.get("audio_cases", [])) or 6
    lines += [
        "",
        "## Summary",
        "",
        f"Exact JSON success: {exact}/{expected_count} "
        f"({100 * exact / expected_count:.1f}%).",
        f"Processed: {len(rows)}/{expected_count}; execution errors: "
        f"{sum(r.get('status') != 'ok' for r in rows)}.",
    ]
    for level in ("basico", "habitual"):
        expected_level = sum(
            c.get("level") == level for c in metadata.get("audio_cases", [])
        )
        correct = sum(
            r.get("level") == level
            and r.get("evaluation", {}).get("exact_match", False)
            for r in rows
        )
        if expected_level:
            lines += [
                "",
                f"{level}: {correct}/{expected_level} exact "
                f"({100 * correct / expected_level:.1f}%).",
            ]
    lines += [
        "",
        "| Case | Exact JSON | Pi STT (s) | LLM API (s) | Whisper peak RAM (MiB) |",
        "|---|---|---:|---:|---:|",
    ]
    stt_times, api_times, peaks = [], [], []

    def number(value):
        return f"{value:.3f}" if isinstance(value, (int, float)) else "N/A"

    for row in flat:
        stt = row["pi_stt_s"]
        api = row["llm_api_s"]
        peak = row["pi_stt_peak_mib"]
        if stt is not None:
            stt_times.append(stt)
        if api is not None:
            api_times.append(api)
        if peak is not None:
            peaks.append(peak)
        lines.append(
            f"| {row['case_id']} | {row.get('exact_match', False)} | "
            f"{number(stt)} | {number(api)} | {number(peak)} |"
        )
    audio_durations = {
        c["id"]: c.get("duration_s") for c in metadata.get("audio_cases", [])
    }
    lines += [
        "",
        "### Resources and audio duration",
        "",
        "| Case | Audio (s) | Pi CPU (%) | PC client RAM (MiB) | STT + API (s) |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in flat:
        combined = (
            row["pi_stt_s"] + row["llm_api_s"]
            if row["pi_stt_s"] is not None and row["llm_api_s"] is not None
            else None
        )
        lines.append(
            f"| {row['case_id']} | {number(audio_durations.get(row['case_id']))} | "
            f"{number(row['pi_cpu_pct'])} | "
            f"{number(row['pc_api_client_peak_mib'])} | {number(combined)} |"
        )
    lines += [
        "",
        "CPU: 100% represents one logical core. "
        "PC RAM is the API client, not the model hosted by Groq.",
    ]
    load = metadata.get("remote_environment", {}).get("load", {}).get("load_s")
    lines += [
        "",
        "### Overall metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Exact JSON success | {exact}/{expected_count} "
        f"({100 * exact / expected_count:.1f}%) |",
        f"| Initial model load (s) | {number(load)} |",
    ]
    for label, values in [("Pi STT", stt_times), ("LLM API", api_times)]:
        if values:
            lines.append(f"| {label} mean (s) | {number(sum(values) / len(values))} |")
            lines.append(
                f"| {label} min–max (s) | {number(min(values))}–{number(max(values))} |"
            )
    if peaks:
        lines.append(f"| Whisper peak RAM (MiB) | {number(max(peaks))} |")
    client_peaks = [
        r["pc_api_client_peak_mib"]
        for r in flat
        if r["pc_api_client_peak_mib"] is not None
    ]
    if client_peaks:
        lines.append(f"| PC client peak RAM (MiB) | {number(max(client_peaks))} |")
    for label, values in [("Pi STT", stt_times), ("LLM API", api_times)]:
        if values:
            lines += [
                "",
                f"{label}: mean {sum(values) / len(values):.3f} s; "
                f"range {min(values):.3f}–{max(values):.3f} s; "
                f"sum {sum(values):.3f} s ({len(values)} measurements).",
            ]
    load = metadata.get("remote_environment", {}).get("load", {}).get("load_s")
    lines += ["", f"Initial model load: {number(load)} s."]
    if peaks:
        lines += ["", f"Whisper maximum sampled RSS: {max(peaks):.2f} MiB."]
    lines += [
        "",
        "Pi STT includes WAV reading/conversion and inference. "
        "LLM API includes network and response handling. Stage sums exclude "
        "SSH transfers, model load and orchestration; they are not total run duration.",
    ]

    def cell(value):
        return (
            str(value)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("|", "&#124;")
            .replace("\r", "")
            .replace("\n", "<br>")
        )

    lines += [
        "",
        "### Reference, transcription and JSON comparison",
        "",
        "| Case | Reference | STT output | Expected JSON | Actual JSON |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        expected_json = json.dumps(r["expected_json"], ensure_ascii=False)
        lines.append(
            f"| {cell(r['case_id'])} | {cell(r['reference_text'])} | "
            f"{cell(r.get('transcription', 'N/A'))} | {cell(expected_json)} | "
            f"{cell(r.get('raw_response', 'N/A'))} |"
        )
    fields = [
        "valid_json",
        "schema_valid",
        "correct_operation",
        "correct_product",
        "correct_quantity",
        "exact_match",
    ]
    lines += [
        "",
        "### Validation by case",
        "",
        "| Case | Level | Status | Valid JSON | Schema | Operation | "
        "Product | Quantity | Exact JSON | Error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        values = [r["case_id"], r["level"], r["status"]]
        values += [r.get("evaluation", {}).get(field, "N/A") for field in fields]
        values.append(r.get("error") or "None")
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    lines += [
        "",
        "### Component resources by case",
        "",
        "| Case | Component | Wall time (s) | Base RAM (MiB) | "
        "Peak RAM (MiB) | CPU time (s) | CPU (%) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    resource_fields = [
        "request_wall_s",
        "ram_base_mib",
        "ram_peak_mib",
        "cpu_s",
        "cpu_pct",
    ]
    for r in rows:
        components = [
            ("Pi Whisper", r.get("remote_stt", {}).get("resources", {})),
            ("PC API client", r.get("api_resources", {})),
        ]
        for label, resources in components:
            values = [number(resources.get(field)) for field in resource_fields]
            lines.append(
                f"| {cell(r['case_id'])} | {label} | " + " | ".join(values) + " |"
            )
    load_resources = metadata.get("remote_environment", {}).get("load_resources", {})
    if load_resources:
        lines += [
            "",
            "### Initial load resources",
            "",
            "| Metric | Value |",
            "|---|---:|",
        ]
        for field in resource_fields:
            lines.append(f"| {field} | {number(load_resources.get(field))} |")
    lines += [
        "",
        "Exact JSON evaluates the complete pipeline; it does not "
        "measure STT semantic accuracy or prove that quantities were present "
        "in the transcription. Missing measurements are shown as N/A.",
    ]
    for r in rows:
        lines += [
            "",
            f"## {r['case_id']} ({r['level']})",
            "",
            "**Reference:** " + r["reference_text"],
            "",
            "**Pi transcription:** " + r.get("transcription", ""),
            "",
            "**Expected JSON:**",
            "```json",
            json.dumps(r["expected_json"], indent=2, ensure_ascii=False),
            "```",
            "",
            "**Actual JSON:**",
            "```json",
            r.get("raw_response", ""),
            "```",
            "",
            "**Evaluation:** " + json.dumps(r.get("evaluation", {})),
            "**Pi resources:** "
            + json.dumps(r.get("remote_stt", {}).get("resources", {})),
            "**PC resources:** " + json.dumps(r.get("api_resources", {})),
            "**Error:** " + str(r.get("error")),
        ]
    if metadata.get("fatal_error"):
        lines += ["", "**Run stopped:** " + metadata["fatal_error"]]
    (out / "benchmark_report.md").write_text("\n".join(lines).rstrip() + "\n")


def main():
    from api_keys import load_api_keys
    from precision_benchmark import (
        CASES,
        GROQ_JSON_SCHEMA,
        GROQ_URL,
        PrecisionCase,
        evaluate,
        prompt_for,
    )
    from prompt_levels import LEVELS
    from stt_benchmark import Monitor, sha256

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--host", required=True, help="SSH config alias or user@address"
    )
    parser.add_argument(
        "--remote-repo", required=True, help="Absolute repository path on Pi"
    )
    parser.add_argument("--remote-python", default="python3")
    parser.add_argument("--stt-model", default="ggml-small-q5_1.bin")
    parser.add_argument(
        "--stt-prompt",
        type=Path,
        nargs="+",
        action="extend",
        help="Local UTF-8 context files, concatenated in the given order",
    )
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument(
        "--ssh-password",
        action="store_true",
        help="Allow SSH to prompt for a password in the local terminal",
    )
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_@.\[\]:-]+", args.host) or args.host.startswith(
        "-"
    ):
        parser.error("Invalid SSH host")
    if not args.remote_repo.startswith("/") or "\n" in args.remote_repo:
        parser.error("remote-repo must be an absolute path")
    if args.threads < 1 or args.timeout <= 0 or not 1 <= args.port <= 65535:
        parser.error("Invalid threads, timeout or port")
    if Path(args.stt_model).name != args.stt_model or not args.stt_model.endswith(
        ".bin"
    ):
        parser.error("stt-model must be a model filename ending in .bin")
    prompt_bytes = None
    prompt_files = []
    if args.stt_prompt:
        texts = []
        for path in args.stt_prompt:
            try:
                data = path.read_bytes()
                text = data.decode("utf-8").strip()
                if not text:
                    parser.error(f"STT prompt is empty: {path}")
            except (OSError, UnicodeError):
                parser.error(f"STT prompt must be a readable UTF-8 file: {path}")
            texts.append(text)
            prompt_files.append(
                {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}
            )
        prompt_bytes = ("\n\n".join(texts) + "\n").encode("utf-8")
    load_api_keys()
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        parser.error("Set GROQ_API_KEY in config/api-keys.env on the PC")
    fixtures = ROOT / "tests/fixtures/speech_to_text"
    manifest = json.loads((fixtures / "manifest.json").read_text())
    cases = [c for c in manifest["cases"] if LEVELS[c["id"]] in {"basico", "habitual"}]
    expected = {c.case_id: c.expected for c in CASES}
    for case in cases:
        if sha256(fixtures / case["wav"]) != case["wav_sha256"]:
            raise RuntimeError(f"Local fixture changed: {case['id']}")
    run_id = time.strftime("pi_ssh_%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    out = ROOT / "reports/audio-stt-llm" / run_id
    out.mkdir(parents=True)
    remote_dir = args.remote_repo.rstrip("/") + "/.cache/integration/" + run_id
    ssh = [
        "ssh",
        "-T",
        "-o",
        "BatchMode=no" if args.ssh_password else "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-p",
        str(args.port),
        args.host,
    ]
    metadata = {
        "host": args.host,
        "remote_repo": args.remote_repo,
        "remote_inputs": remote_dir,
        "llm_model": MODEL,
        "stt_model": args.stt_model,
        "stt_prompt_files": prompt_files,
        "stt_prompt_text": prompt_bytes.decode("utf-8")
        if prompt_bytes is not None
        else None,
        "stt_prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest()
        if prompt_bytes is not None
        else None,
        "runs_per_case": 1,
        "warmups": 0,
        "retries": 0,
        "manifest_sha256": sha256(fixtures / "manifest.json"),
        "local_model_sha256": sha256(ROOT / "models/stt/whisper" / args.stt_model)
        if (ROOT / "models/stt/whisper" / args.stt_model).exists()
        else None,
        "contract_sha256": sha256(
            ROOT / "scripts/benchmarks/prompts/precision/contract.txt"
        ),
        "groq_settings": {
            "temperature": 0,
            "reasoning_effort": "low",
            "max_completion_tokens": 1000,
            "schema": GROQ_JSON_SCHEMA,
        },
        "audio_cases": cases,
    }
    rows = []
    process = None
    try:
        with tempfile.TemporaryFile() as archive:
            with tarfile.open(fileobj=archive, mode="w") as tar:
                for case in cases:
                    tar.add(fixtures / case["wav"], arcname=case["id"] + ".wav")
                if prompt_bytes is not None:
                    prompt_copy = out / "stt_prompt.txt"
                    prompt_copy.write_bytes(prompt_bytes)
                    tar.add(prompt_copy, arcname="stt_prompt.txt")
            archive.seek(0)
            command = (
                "mkdir -p "
                + shlex.quote(remote_dir)
                + " && tar -xf - -C "
                + shlex.quote(remote_dir)
            )
            subprocess.run(
                [*ssh, command], stdin=archive, check=True, timeout=args.timeout
            )
        command = (
            "cd "
            + shlex.quote(args.remote_repo)
            + " && exec "
            + shlex.join(
                [
                    args.remote_python,
                    "scripts/integration/stt_remote_worker.py",
                    "--input-dir",
                    remote_dir,
                    "--stt-model",
                    args.stt_model,
                    *(
                        ["--stt-prompt", remote_dir + "/stt_prompt.txt"]
                        if args.stt_prompt
                        else []
                    ),
                    "--threads",
                    str(args.threads),
                    "--timeout",
                    str(args.timeout),
                ]
            )
        )
        with (out / "ssh.log").open("w") as log:
            process = subprocess.Popen(
                [*ssh, command],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=log,
                text=True,
            )
            ready = receive(process, args.timeout)
            if ready.get("event") != "ready":
                raise RuntimeError("Missing remote ready event")
            metadata["remote_environment"] = ready
            if ready.get("stt_prompt_sha256") != metadata["stt_prompt_sha256"]:
                raise RuntimeError("Pi and PC STT prompt hashes differ")
            if (
                metadata["local_model_sha256"]
                and ready["model_sha256"] != metadata["local_model_sha256"]
            ):
                raise RuntimeError("Pi and PC model hashes differ")
            save(out, rows, metadata)
            for case in cases:
                row = {
                    "case_id": case["id"],
                    "level": LEVELS[case["id"]],
                    "reference_text": case["expected_text"],
                    "expected_json": expected[case["id"]],
                    "status": "error",
                    "error": None,
                }
                print(f"Running {case['id']} on {args.host}...", flush=True)
                try:
                    process.stdin.write(
                        json.dumps(
                            {
                                "case_id": case["id"],
                                "filename": case["id"] + ".wav",
                                "sha256": case["wav_sha256"],
                            }
                        )
                        + "\n"
                    )
                    process.stdin.flush()
                    remote = receive(process, args.timeout)
                    row["remote_stt"] = remote
                    if (
                        remote.get("case_id") != case["id"]
                        or remote.get("status") != "ok"
                    ):
                        raise RuntimeError(remote.get("error", "Invalid remote result"))
                    row["transcription"] = remote["text"]
                    row["llm_prompt"] = prompt_for(
                        PrecisionCase(case["id"], remote["text"], row["expected_json"])
                    )
                    payload = {
                        "model": MODEL,
                        "messages": [{"role": "user", "content": row["llm_prompt"]}],
                        "temperature": 0,
                        "reasoning_effort": "low",
                        "max_completion_tokens": 1000,
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
                        data=json.dumps(payload).encode(),
                        headers={
                            "Authorization": "Bearer " + key,
                            "Content-Type": "application/json",
                            "User-Agent": "llm-to-json-benchmark/1.0",
                        },
                    )
                    with Monitor(os.getpid()) as monitor:
                        with urllib.request.urlopen(
                            request, timeout=args.timeout
                        ) as stream:
                            result = json.load(stream)
                    row["api_resources"] = monitor.metrics()
                    row["raw_response"] = (
                        result["choices"][0]["message"].get("content") or ""
                    )
                    row["groq_response"] = result
                    row["evaluation"] = evaluate(
                        row["raw_response"], row["expected_json"]
                    )
                    row["status"] = "ok"
                except Exception as exc:
                    row["error"] = str(exc).replace(key, "[REDACTED]")
                    if isinstance(exc, TimeoutError):
                        raise
                finally:
                    rows.append(row)
                    save(out, rows, metadata)
                print(f"  {row['status']}: {row.get('evaluation', {})}", flush=True)
            process.stdin.write('{"command":"close"}\n')
            process.stdin.flush()
            process.stdin.close()
            process.wait(timeout=15)
    except Exception as exc:
        metadata["fatal_error"] = str(exc).replace(key, "[REDACTED]")
        save(out, rows, metadata)
        print("Run stopped: " + metadata["fatal_error"], file=sys.stderr)
    finally:
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    print(f"Results: {out}", flush=True)
    return int(
        bool(metadata.get("fatal_error"))
        or len(rows) != 6
        or any(
            r["status"] != "ok" or not r.get("evaluation", {}).get("exact_match")
            for r in rows
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
