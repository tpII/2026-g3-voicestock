"""Import checks that keep the pc, pi and shared packages apart.

pc holds what runs on the PC, pi what runs on the Raspberry Pi, and shared the
contracts both sides exchange. pc and pi never import each other, and shared
imports neither.
"""

import ast
from pathlib import Path

import pc

SRC_DIR = Path(pc.__file__).parent.parent
PACKAGES = ("pc", "pi", "shared")


def _imports_by_file() -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for package in PACKAGES:
        for path in (SRC_DIR / package).rglob("*.py"):
            modules: set[str] = set()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    modules.update(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    modules.add(node.module)
            result[path.relative_to(SRC_DIR).as_posix()] = modules
    return result


def _offending(importer: str, forbidden: set[str]) -> set[str]:
    return {
        f"{name}: {module}"
        for name, modules in _imports_by_file().items()
        if name.startswith(f"{importer}/")
        for module in modules
        if module.split(".")[0] in forbidden
    }


def test_pc_does_not_import_pi() -> None:
    assert _offending("pc", {"pi"}) == set()


def test_pi_does_not_import_pc() -> None:
    assert _offending("pi", {"pc"}) == set()


def test_shared_imports_neither_side() -> None:
    assert _offending("shared", {"pc", "pi"}) == set()


def test_pc_communication_does_not_know_interpretation() -> None:
    offending = {
        f"{name}: {module}"
        for name, modules in _imports_by_file().items()
        if name.startswith("pc/communication/")
        for module in modules
        if module.startswith("pc.interpretation")
    }

    assert offending == set()


def test_http_frameworks_stay_in_http_adapters() -> None:
    """FastAPI and Uvicorn stay in the PC server and in pi/web.

    The Pi application layer, including pending operations, must not import
    an HTTP framework. Allowing every module under pi would hide that leak.
    """
    http_modules = {"fastapi", "starlette", "uvicorn", "aiohttp", "flask", "socket"}
    users = {
        name
        for name, modules in _imports_by_file().items()
        if any(module.split(".")[0] in http_modules for module in modules)
    }
    pc_adapters = {"pc/communication/server.py", "pc/main.py"}
    pi_web = {name for name in users if name.startswith("pi/web/")}

    assert users == pc_adapters | pi_web
    assert pi_web
    assert not any(name.startswith("pi/pending_operation/") for name in users)
    assert not any(name.startswith("pi/communication/") for name in users)
    assert not any(name.startswith("pi/audio/") for name in users)
    assert not any(name.startswith("shared/") for name in users)


def test_pending_operation_does_not_import_web_libraries() -> None:
    """HTTP schemas stay in pi.web. The application layer does not import them."""
    forbidden = {"fastapi", "starlette", "uvicorn", "pydantic"}
    offending = {
        f"{name}: {module}"
        for name, modules in _imports_by_file().items()
        if name.startswith("pi/pending_operation/")
        for module in modules
        if module.split(".")[0] in forbidden
    }

    assert offending == set()
