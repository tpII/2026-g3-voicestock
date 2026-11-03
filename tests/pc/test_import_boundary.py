"""PC product code must not import the Raspberry Pi package."""

import ast
from pathlib import Path

SRC = Path(__file__).parents[2] / "src" / "pc"


def test_pc_modules_do_not_import_pi() -> None:
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            modules: list[str | None] = []
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                modules.append(node.module)
            for module in modules:
                if module == "pi" or (module or "").startswith("pi."):
                    offenders.append(f"{path.name}: {module}")
    assert offenders == []
