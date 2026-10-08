"""FastAPI application for the Raspberry Pi operator UI.

This module builds the app. Pending-operation routes live in ``pi.web.api``
and only call application ports. Health and static files do not need those
ports, so the temporary ``voicestock-pi-web`` command can still start.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pi.pending_operation import (
    PendingOperationQueryPort,
    PendingOperationResolutionPort,
)
from pi.web.api import register_exception_handlers, router

STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"


def create_app(
    query_port: PendingOperationQueryPort | None = None,
    resolution_port: PendingOperationResolutionPort | None = None,
) -> FastAPI:
    """Build the web app and keep the ports for the versioned API."""
    if not INDEX_FILE.is_file():
        raise FileNotFoundError(f"web index was not found at {INDEX_FILE}")

    app = FastAPI(title="VoiceStock Web", version="0.1.0")
    app.state.query_port = query_port
    app.state.resolution_port = resolution_port
    register_exception_handlers(app)
    app.include_router(router)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Report that this HTTP server can answer. Not a readiness check."""
        return {"status": "ok"}

    @app.get("/")
    def index() -> FileResponse:
        """Serve the placeholder page. The pending-operation UI is later."""
        return FileResponse(INDEX_FILE)

    app.mount(
        "/static",
        StaticFiles(directory=STATIC_DIR),
        name="static",
    )
    return app
