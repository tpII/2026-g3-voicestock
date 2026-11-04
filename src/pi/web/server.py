"""Process entry that runs the web app under Uvicorn.

``voicestock-pi-web`` is a development and validation command. The production
shape is still one Python process: this module does not start a second
service, and it does not define how the future orchestrator will share this
process. That composition waits until the runtime exists.
"""

from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI

from pi.web.app import create_app
from pi.web.settings import WebServerSettings

ServerRunner = Callable[..., Any]


def run_server(
    settings: WebServerSettings | None = None,
    app: FastAPI | None = None,
    runner: ServerRunner | None = None,
) -> None:
    """Serve ``app`` with Uvicorn using ``settings``.

    ``runner`` replaces ``uvicorn.run`` in tests so they do not bind a port.
    """
    resolved = (
        settings if settings is not None else WebServerSettings.from_environment()
    )
    start = runner if runner is not None else uvicorn.run
    start(
        app if app is not None else create_app(),
        host=resolved.host,
        port=resolved.port,
    )


def main() -> None:
    """Run the temporary web server from the environment."""
    run_server()


if __name__ == "__main__":
    main()
