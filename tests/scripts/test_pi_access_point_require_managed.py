"""Run the access-point unmanaged-state regression without hardware."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGRESSION = ROOT / "tests" / "scripts" / "test_pi_access_point_require_managed.sh"


def _bash_executable() -> str:
    """Return Bash for the regression script.

    On Windows, ``bash`` on PATH is often the WSL launcher. Git Bash can
    run this test when that launcher is not usable.
    """
    if os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        git_bash = Path(program_files) / "Git" / "bin" / "bash.exe"
        if git_bash.is_file():
            return str(git_bash)
    return "bash"


def test_require_managed_state_detection() -> None:
    completed = subprocess.run(
        [_bash_executable(), str(REGRESSION)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
