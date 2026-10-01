"""Typed result returned by InterpretationService for every interpretation."""

from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, model_validator


class ServiceErrorCode(StrEnum):
    """Stable categories a caller can branch on without reading free text."""

    INVALID_INPUT = "invalid_input"
    PROVIDER_NOT_CONFIGURED = "provider_not_configured"
    PROVIDER_FAILURE = "provider_failure"


class ServiceError(BaseModel):
    """Machine-readable service failure with non-contractual diagnostic detail."""

    model_config = ConfigDict(extra="forbid")

    code: ServiceErrorCode
    detail: str | None = None


class ServiceResult(BaseModel):
    """Outcome of one interpretation, independent of the active provider."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "error"]
    payload: Any = None
    error: ServiceError | None = None

    @model_validator(mode="after")
    def status_must_match_content(self) -> Self:
        """Ensure success and failure results cannot contradict themselves."""
        if self.status == "success" and self.error is not None:
            raise ValueError("a success result cannot contain an error")
        if self.status == "error" and self.error is None:
            raise ValueError("an error result must contain an error")
        if self.status == "error" and self.payload is not None:
            raise ValueError("an error result cannot contain a payload")
        return self

    @classmethod
    def success(cls, payload: Any) -> Self:
        """Build a result for a payload produced by the provider."""
        return cls(status="success", payload=payload)

    @classmethod
    def failure(cls, code: ServiceErrorCode, detail: str | None = None) -> Self:
        """Build a result for a typed service failure."""
        return cls(status="error", error=ServiceError(code=code, detail=detail))
