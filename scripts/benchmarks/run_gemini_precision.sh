#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

read -r -s -p "Pegá tu GEMINI_API_KEY (no se mostrará): " GEMINI_API_KEY
printf "\n"
if [[ -z "$GEMINI_API_KEY" ]]; then
    printf "La API key no puede estar vacía.\n" >&2
    exit 1
fi
export GEMINI_API_KEY

PYTHON_BIN="${PYTHON_BIN:-python3}"
exec "$PYTHON_BIN" scripts/benchmarks/precision_benchmark.py \
    --provider gemini \
    --contract contract.txt
