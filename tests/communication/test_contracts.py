"""Tests for transport-level request and envelope invariants."""

import pytest
from pydantic import ValidationError

from voicestock.communication.contracts import (
    InterpretationRequest,
    TransportEnvelope,
    TransportError,
)


def test_interpretation_request_accepts_spanish_text() -> None:
    request = InterpretationRequest(text="agregá dos paquetes de arroz")

    assert request.text == "agregá dos paquetes de arroz"


@pytest.mark.parametrize("text", ["", "   ", "\n\t"])
def test_interpretation_request_rejects_blank_text(text: str) -> None:
    with pytest.raises(ValidationError):
        InterpretationRequest(text=text)


def test_success_envelope_preserves_opaque_payload() -> None:
    payload = {"nested": {"operation": "opaque"}}

    envelope = TransportEnvelope.success(payload)

    assert envelope.status == "success"
    assert envelope.payload is payload
    assert envelope.error is None


def test_error_envelope_requires_transport_error() -> None:
    with pytest.raises(ValidationError):
        TransportEnvelope(status="error")


def test_error_envelope_rejects_payload() -> None:
    with pytest.raises(ValidationError):
        TransportEnvelope(
            status="error",
            payload={"unexpected": True},
            error=TransportError(code="invalid_request"),
        )
