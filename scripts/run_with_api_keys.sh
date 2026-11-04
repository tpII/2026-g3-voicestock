#!/usr/bin/env bash
# Execute a command with the repository's local API credentials loaded.
set -euo pipefail

TASK_REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TASK_KEYS_FILE="$TASK_REPO_ROOT/config/api-keys.env"

if [[ $# -eq 0 || "${1:-}" == "--help" ]]; then
  printf 'Uso: %s <comando> [argumentos...]\n' "$0"
  printf 'Ejemplo: %s python scripts/benchmarks/precision_benchmark.py --help\n' "$0"
  exit 0
fi

if [[ ! -f "$TASK_KEYS_FILE" ]]; then
  printf 'No se encontró config/api-keys.env.\n' >&2
  exit 1
fi

# Avoid printing secrets even if the wrapper was launched with bash -x.
set +x
set -a
source "$TASK_KEYS_FILE"
set +a

# Keep the caller's PATH, including the active Conda or venv interpreter.
cd "$TASK_REPO_ROOT"
exec "$@"
