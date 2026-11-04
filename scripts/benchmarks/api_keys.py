"""Load local API credentials without shell execution or overriding the environment."""

import os
import shlex
from pathlib import Path

KEYS_FILE = Path(__file__).resolve().parents[2] / "config/api-keys.env"
ALLOWED_KEYS = {"GEMINI_API_KEY", "GROQ_API_KEY", "LLM_API_KEY"}


def load_api_keys():
    if not KEYS_FILE.exists():
        return
    for number, line in enumerate(KEYS_FILE.read_text().splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        name = name.strip()
        if name.startswith("export "):
            name = name[7:].strip()
        if not separator or name not in ALLOWED_KEYS:
            raise ValueError(f"Invalid API key assignment at line {number}")
        try:
            parts = shlex.split(value, comments=True, posix=True)
        except ValueError:
            raise ValueError(f"Invalid API key quoting at line {number}") from None
        if len(parts) > 1:
            raise ValueError(f"Quote the API key value at line {number}")
        decoded = parts[0] if parts else ""
        if decoded and not os.environ.get(name):
            os.environ[name] = decoded
