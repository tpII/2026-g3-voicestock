"""Transport-level contracts shared by the PC server and Raspberry Pi client."""

from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, StrictStr, field_validator, model_validator


class InterpretationRequest(BaseModel):
    """Recognized text sent by the Raspberry Pi for interpretation."""

    model_config = ConfigDict(extra="forbid")

    text: StrictStr

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        """Reject requests that do not contain meaningful recognized text."""
        if not value.strip():
            raise ValueError("text must not be blank")
        return value


class TransportError(BaseModel):
    """Machine-readable transport failure with optional diagnostic detail."""

    model_config = ConfigDict(extra="forbid")

    code: str
    detail: str | None = None


class TransportEnvelope(BaseModel):
    """Outer envelope that keeps the transported payload opaque."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["success", "error"]
    payload: Any = None
    error: TransportError | None = None

    @model_validator(mode="after")
    def status_must_match_content(self) -> Self:
        """Ensure success and failure envelopes cannot contradict themselves."""
        if self.status == "success" and self.error is not None:
            raise ValueError("a success envelope cannot contain an error")
        if self.status == "error" and self.error is None:
            raise ValueError("an error envelope must contain an error")
        if self.status == "error" and self.payload is not None:
            raise ValueError("an error envelope cannot contain a payload")
        return self

    @classmethod
    def success(cls, payload: Any) -> Self:
        """Build an envelope for an opaque handler result."""
        return cls(status="success", payload=payload)

    @classmethod
    def failure(cls, code: str, detail: str | None = None) -> Self:
        """Build an envelope for a transport-level failure."""
        return cls(status="error", error=TransportError(code=code, detail=detail))
