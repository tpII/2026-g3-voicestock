"""Versioned HTTP adapter for the current pending operation.

Routes call application ports and map their results. They do not touch the
slot, the executor, or the FSM.
"""

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse, Response

from pi.pending_operation.resolution import ResolutionResult, ResolutionStatus
from pi.web.dependencies import (
    APIError,
    QueryPortDep,
    ResolutionPortDep,
    call_resolution,
    validated_operation_id,
)
from pi.web.schemas import PendingOperationResponse, ResolutionResponse

router = APIRouter(prefix="/api/v1")

NO_STORE = {"Cache-Control": "no-store"}

_HTTP_STATUS = {
    ResolutionStatus.SUCCESS: 200,
    ResolutionStatus.ALREADY_RESOLVED: 200,
    ResolutionStatus.NO_PENDING: 404,
    ResolutionStatus.STALE_OPERATION: 409,
    ResolutionStatus.CONFLICT: 409,
    ResolutionStatus.EXECUTION_FAILED: 503,
}


def register_exception_handlers(app: FastAPI) -> None:
    """Render ``APIError`` as the documented error body."""

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        del request
        return JSONResponse(status_code=exc.status_code, content=exc.body.model_dump())


def resolution_http_response(result: ResolutionResult) -> JSONResponse:
    """Map one application outcome to its HTTP status and body.

    ``execution_failed`` uses this same map if a cancel call returns it.
    The application cancel path does not produce that status; the map stays
    shared so confirm and cancel cannot drift.
    """
    body = ResolutionResponse.from_result(result)
    return JSONResponse(
        status_code=_HTTP_STATUS[result.status],
        content=body.model_dump(mode="json"),
    )


@router.get("/pending-operation")
def read_pending_operation(query_port: QueryPortDep) -> Response:
    """Return the current snapshot, or 204 when nothing is pending."""
    current = query_port.get_current()
    if current is None:
        return Response(status_code=204, headers=NO_STORE)
    body = PendingOperationResponse.from_view(current)
    return JSONResponse(content=body.model_dump(mode="json"), headers=NO_STORE)


@router.post("/pending-operation/{operation_id}/confirm")
def confirm_pending_operation(
    operation_id: str,
    resolution_port: ResolutionPortDep,
) -> JSONResponse:
    """Confirm the named operation through the resolution port."""
    operation_id = validated_operation_id(operation_id)
    result = call_resolution(resolution_port.confirm, operation_id)
    return resolution_http_response(result)


@router.post("/pending-operation/{operation_id}/cancel")
def cancel_pending_operation(
    operation_id: str,
    resolution_port: ResolutionPortDep,
) -> JSONResponse:
    """Cancel the named operation through the resolution port."""
    operation_id = validated_operation_id(operation_id)
    result = call_resolution(resolution_port.cancel, operation_id)
    return resolution_http_response(result)
