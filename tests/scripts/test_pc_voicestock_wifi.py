"""Run the Arch VoiceStock client regression without hardware."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGRESSION = ROOT / "tests" / "scripts" / "test_pc_voicestock_wifi.sh"


def _bash_executable() -> str:
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        git_bash = Path(program_files) / "Git" / "bin" / "bash.exe"
        if git_bash.is_file():
            return str(git_bash)
    return "bash"


def test_pc_voicestock_client_configuration() -> None:
    completed = subprocess.run(
        [_bash_executable(), str(REGRESSION)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
