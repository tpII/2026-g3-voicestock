"""HTTP adapter for Raspberry Pi to PC interpretation requests."""

from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic_core import PydanticSerializationError

from pc.communication.audio import AudioHandler, InvalidAudioError, read_wav
from shared.communication.contracts import (
    MAX_AUDIO_BYTES,
    WAV_MEDIA_TYPE,
    InterpretationRequest,
    TransportEnvelope,
)

InterpretationHandler = Callable[[str], Any]

_Input = TypeVar("_Input")


def create_app(
    handler: InterpretationHandler,
    audio_handler: AudioHandler | None = None,
) -> FastAPI:
    """Create the PC HTTP server around replaceable handlers.

    ``handler`` serves recognized text. ``audio_handler`` serves WAV
    recordings; without it the audio endpoint is not exposed.
    """
    app = FastAPI(title="VoiceStock PC Communication", version="1.0.0")

    @app.post("/api/v1/interpret")
    async def interpret(request: Request) -> JSONResponse:
        if _media_type(request) != "application/json":
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

        return _run_handler(handler, parsed_request.text)

    if audio_handler is not None:

        @app.post("/api/v1/interpret-audio")
        async def interpret_audio(request: Request) -> JSONResponse:
            if _media_type(request) != WAV_MEDIA_TYPE:
                return _error_response(
                    415,
                    "unsupported_media_type",
                    f"Content-Type must be {WAV_MEDIA_TYPE}",
                )

            content = await _read_limited_body(request, MAX_AUDIO_BYTES)
            if content is None:
                return _error_response(
                    413,
                    "audio_too_large",
                    f"audio body exceeds {MAX_AUDIO_BYTES} bytes",
                )
            if not content:
                return _error_response(422, "empty_audio", "audio body is empty")

            try:
                audio = read_wav(content)
            except InvalidAudioError:
                return _error_response(
                    422, "invalid_audio", "audio body is not a readable WAV file"
                )

            return _run_handler(audio_handler, audio)

    return app


def _media_type(request: Request) -> str:
    content_type = request.headers.get("content-type", "")
    return content_type.split(";", maxsplit=1)[0].strip().lower()


async def _read_limited_body(request: Request, limit: int) -> bytes | None:
    """Return the body, or None as soon as it is known to exceed ``limit``."""
    declared_length = request.headers.get("content-length", "")
    if declared_length.isdigit() and int(declared_length) > limit:
        return None

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > limit:
            return None
    return bytes(body)


def _run_handler(handler: Callable[[_Input], Any], value: _Input) -> JSONResponse:
    try:
        payload = handler(value)
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


def _error_response(status_code: int, code: str, detail: str) -> JSONResponse:
    envelope = TransportEnvelope.failure(code=code, detail=detail)
    return JSONResponse(
        status_code=status_code, content=envelope.model_dump(mode="json")
    )
