"""HTTP adapter for Raspberry Pi to PC interpretation requests."""

from collections.abc import Callable
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic_core import PydanticSerializationError

from voicestock.communication.contracts import (
    InterpretationRequest,
    TransportEnvelope,
)
from voicestock.communication.settings import ServerSettings

InterpretationHandler = Callable[[str], Any]


def create_app(handler: InterpretationHandler) -> FastAPI:
    """Create the PC HTTP server around a replaceable interpretation handler."""
    app = FastAPI(title="VoiceStock PC Communication", version="1.0.0")

    @app.post("/api/v1/interpret")
    async def interpret(request: Request) -> JSONResponse:
        content_type = request.headers.get("content-type", "")
        if content_type.split(";", maxsplit=1)[0].strip().lower() != "application/json":
            return _error_response(
                415,
                "unsupported_media_type",
                "Content-Type must be application/json",
            )

        try:
            raw_body = await request.json()
        except (UnicodeDecodeError, ValueError):
            return _error_response(
                400, "invalid_json", "request body is not valid JSON"
            )

        try:
            parsed_request = InterpretationRequest.model_validate(raw_body)
        except ValueError:
            return _error_response(422, "invalid_request", "request body is not valid")

        try:
            payload = handler(parsed_request.text)
        except Exception:
            return _error_response(
                500,
                "handler_failure",
                "the interpretation handler failed",
            )

        try:
            content = TransportEnvelope.success(payload).model_dump(mode="json")
        except (PydanticSerializationError, TypeError, ValueError):
            return _error_response(
                500,
                "serialization_failure",
                "the handler result is not JSON serializable",
            )

        return JSONResponse(status_code=200, content=content)

    return app


def _error_response(status_code: int, code: str, detail: str) -> JSONResponse:
    envelope = TransportEnvelope.failure(code=code, detail=detail)
    return JSONResponse(
        status_code=status_code, content=envelope.model_dump(mode="json")
    )


def stub_handler(text: str) -> dict[str, str]:
    """Return an opaque deterministic payload until InterpretationService exists."""
    return {"recognized_text": text}


def main() -> None:
    """Run the development server with the replaceable stub handler."""
    settings = ServerSettings.from_environment()
    uvicorn.run(
        create_app(stub_handler),
        host=settings.host,
        port=settings.port,
    )


if __name__ == "__main__":
    main()
