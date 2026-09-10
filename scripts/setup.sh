#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

info() {
  printf '==> %s\n' "$1"
}

error() {
  printf 'ERROR: %s\n' "$1" >&2
  exit 1
}

# Accept CPython 3.11+ with standard wheel tags. Skip MSYS2/MinGW builds:
# packages such as Ruff do not publish wheels for that platform.
python_is_usable() {
  "$@" -c "import sys, sysconfig
plat = sysconfig.get_platform().lower()
ok = sys.version_info >= (3, 11) and 'mingw' not in plat and 'cygwin' not in plat
raise SystemExit(0 if ok else 1)"
}

find_python() {
  local candidate
  for candidate in python3.11 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && python_is_usable "$candidate"; then
      PYTHON_CMD=("$candidate")
      return 0
    fi
  done

  if command -v py >/dev/null 2>&1; then
    local version
    for version in 3.11 3.12 3.13 3; do
      if python_is_usable py "-${version}"; then
        PYTHON_CMD=(py "-${version}")
        return 0
      fi
    done
  fi

  return 1
}

venv_python() {
  if [[ -x "$ROOT/.venv/bin/python" ]]; then
    printf '%s' "$ROOT/.venv/bin/python"
  elif [[ -x "$ROOT/.venv/Scripts/python.exe" ]]; then
    printf '%s' "$ROOT/.venv/Scripts/python.exe"
  else
    return 1
  fi
}

info "Checking Python 3.11 or newer..."
PYTHON_CMD=()
find_python || error "Python 3.11 or newer is required (official CPython). MSYS2 Python is not supported because several development wheels are unavailable."
info "Using interpreter: ${PYTHON_CMD[*]} ($("${PYTHON_CMD[@]}" -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"))"

if [[ ! -x "$ROOT/.venv/bin/python" && ! -x "$ROOT/.venv/Scripts/python.exe" ]]; then
  info "Creating virtual environment at .venv..."
  "${PYTHON_CMD[@]}" -m venv "$ROOT/.venv"
else
  info "Virtual environment already exists; reusing it."
fi

VENV_PYTHON="$(venv_python)" || error "Could not find the virtual environment interpreter."

info "Upgrading pip..."
"$VENV_PYTHON" -m pip install --upgrade pip

info "Installing VoiceStock with development dependencies..."
"$VENV_PYTHON" -m pip install -e ".[dev]"

info "Installing pre-commit hooks..."
"$VENV_PYTHON" -m pre_commit install

info "Setup completed successfully."
info "Activate the environment with:"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  info "  source .venv/bin/activate"
else
  info "  .venv\\Scripts\\Activate.ps1"
fi
info "Then run: ruff check . && pytest"
