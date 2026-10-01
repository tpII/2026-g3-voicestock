"""Ensure the interpretation module stays independent of network transports."""

import ast
from pathlib import Path

import voicestock.interpretation

FORBIDDEN_MODULES = {
    "fastapi",
    "starlette",
    "uvicorn",
    "httpx",
    "requests",
    "socket",
    "http",
    "voicestock.communication",
}


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_interpretation_does_not_import_transport_modules() -> None:
    package_dir = Path(voicestock.interpretation.__file__).parent
    offending = {
        f"{path.name}: {module}"
        for path in package_dir.glob("*.py")
        for module in _imported_modules(path)
        if any(
            module == forbidden or module.startswith(f"{forbidden}.")
            for forbidden in FORBIDDEN_MODULES
        )
    }

    assert offending == set()
