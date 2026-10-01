"""Tests for ServiceResult invariants and serialization."""

import pytest
from pydantic import ValidationError

from pc.interpretation.results import (
    ServiceError,
    ServiceErrorCode,
    ServiceResult,
)


def test_success_result_preserves_payload() -> None:
    payload = {"operation": "opaque"}

    result = ServiceResult.success(payload)

    assert result.status == "success"
    assert result.payload is payload
    assert result.error is None


def test_failure_result_carries_typed_error() -> None:
    result = ServiceResult.failure(ServiceErrorCode.PROVIDER_FAILURE, "too slow")

    assert result.status == "error"
    assert result.payload is None
    assert result.error == ServiceError(
        code=ServiceErrorCode.PROVIDER_FAILURE, detail="too slow"
    )


def test_error_result_requires_error() -> None:
    with pytest.raises(ValidationError):
        ServiceResult(status="error")


def test_error_result_rejects_payload() -> None:
    with pytest.raises(ValidationError):
        ServiceResult(
            status="error",
            payload={"operation": "opaque"},
            error=ServiceError(code=ServiceErrorCode.PROVIDER_FAILURE),
        )


def test_success_result_rejects_error() -> None:
    with pytest.raises(ValidationError):
        ServiceResult(
            status="success",
            error=ServiceError(code=ServiceErrorCode.PROVIDER_FAILURE),
        )


def test_service_error_rejects_unknown_code() -> None:
    with pytest.raises(ValidationError):
        ServiceError(code="something_else")


def test_failure_result_serializes_code_as_string() -> None:
    result = ServiceResult.failure(ServiceErrorCode.PROVIDER_NOT_CONFIGURED)

    assert result.model_dump(mode="json") == {
        "status": "error",
        "payload": None,
        "error": {"code": "provider_not_configured", "detail": None},
    }
