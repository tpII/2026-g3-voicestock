"""FastAPI dependencies that read application ports from the app."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from pi.pending_operation import (
    PendingOperationQueryPort,
    PendingOperationResolutionPort,
)
from pi.pending_operation.resolution import ResolutionResult
from pi.web.schemas import ErrorResponse

NOT_READY_CODE = "application_not_ready"
NOT_READY_DETAIL = "pending-operation application ports are not configured"
INVALID_OPERATION_ID_CODE = "invalid_operation_id"
INVALID_OPERATION_ID_DETAIL = "operation_id must be a non-blank string"
_BLANK_OPERATION_ID = "operation_id must be a non-blank string"


class APIError(Exception):
    """HTTP failure with a stable code, raised before a route returns."""

    def __init__(self, status_code: int, code: str, detail: str) -> None:
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.body = ErrorResponse(code=code, detail=detail)


def get_query_port(request: Request) -> PendingOperationQueryPort:
    """Return the query port, or fail when the runtime has not provided one."""
    port = request.app.state.query_port
    if port is None:
        raise APIError(503, NOT_READY_CODE, NOT_READY_DETAIL)
    return port


def get_resolution_port(request: Request) -> PendingOperationResolutionPort:
    """Return the resolution port, or fail when it was not provided."""
    port = request.app.state.resolution_port
    if port is None:
        raise APIError(503, NOT_READY_CODE, NOT_READY_DETAIL)
    return port


def validated_operation_id(operation_id: str) -> str:
    """Reject a blank path id before the application port is called."""
    if not operation_id.strip():
        raise APIError(422, INVALID_OPERATION_ID_CODE, INVALID_OPERATION_ID_DETAIL)
    return operation_id


def call_resolution(
    action: Callable[[str], ResolutionResult],
    operation_id: str,
) -> ResolutionResult:
    """Call confirm or cancel, and translate only the known blank-id error."""
    try:
        return action(operation_id)
    except ValueError as exc:
        if str(exc) != _BLANK_OPERATION_ID:
            raise
        raise APIError(
            422, INVALID_OPERATION_ID_CODE, INVALID_OPERATION_ID_DETAIL
        ) from exc


QueryPortDep = Annotated[PendingOperationQueryPort, Depends(get_query_port)]
ResolutionPortDep = Annotated[
    PendingOperationResolutionPort, Depends(get_resolution_port)
]
