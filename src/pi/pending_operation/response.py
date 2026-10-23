"""Read a PC transport envelope without coupling that parsing to the FSM.

The envelope's payload is a service result. This module does not import the
PC package: the Raspberry Pi only depends on the JSON shape both sides share.
A transport or service failure never reaches ``OperationValidator``.
"""

from dataclasses import dataclass
from enum import StrEnum

from pi.operation_contract import (
    OperationValidator,
    ValidatedOperation,
    ValidationRejection,
)
from shared.communication import TransportEnvelope


class OutcomeKind(StrEnum):
    """Why a PC response did or did not become a validated operation."""

    ACCEPTED = "accepted"
    TRANSPORT_ERROR = "transport_error"
    SERVICE_ERROR = "service_error"
    CONTRACT_REJECTION = "contract_rejection"


@dataclass(frozen=True, slots=True)
class InterpretationOutcome:
    """Classified PC response. Only an accepted outcome carries an operation."""

    kind: OutcomeKind
    detail: str
    recognized_text: str = ""
    validated_operation: ValidatedOperation | None = None

    def __post_init__(self) -> None:
        if self.kind is OutcomeKind.ACCEPTED:
            if not isinstance(self.validated_operation, ValidatedOperation):
                raise ValueError("an accepted outcome requires a validated operation")
            return
        if self.validated_operation is not None:
            raise ValueError("a rejected outcome cannot carry a validated operation")


class PcResponseInterpreter:
    """Turn one ``TransportEnvelope`` into a validated operation or a rejection."""

    def __init__(self, validator: OperationValidator) -> None:
        self._validator = validator

    def interpret(self, envelope: TransportEnvelope) -> InterpretationOutcome:
        """Classify ``envelope``. Failures are not passed to the validator."""
        if envelope.status == "error":
            return InterpretationOutcome(
                OutcomeKind.TRANSPORT_ERROR,
                _transport_detail(envelope),
            )

        service = envelope.payload
        if not isinstance(service, dict):
            return _service("service result is not an object")

        status = service.get("status")
        if status == "error":
            return _service(_service_error_detail(service.get("error")))
        if status != "success" or service.get("error") is not None:
            return _service("service result is incomplete")
        if service.get("payload") is None:
            return _service("service result has no payload")

        contract_payload, recognized_text = _without_recognized_text(service["payload"])
        validated = self._validator.validate(contract_payload)
        if isinstance(validated, ValidationRejection):
            return InterpretationOutcome(
                OutcomeKind.CONTRACT_REJECTION,
                f"{validated.reason}: {validated.detail}",
            )
        return InterpretationOutcome(
            OutcomeKind.ACCEPTED,
            "",
            recognized_text,
            validated,
        )


def _service(detail: str) -> InterpretationOutcome:
    return InterpretationOutcome(OutcomeKind.SERVICE_ERROR, detail)


def _transport_detail(envelope: TransportEnvelope) -> str:
    error = envelope.error
    if error is None:
        return "transport error"
    if error.detail:
        return f"{error.code}: {error.detail}"
    return error.code


def _service_error_detail(error: object) -> str:
    if not isinstance(error, dict):
        return "service error is missing"
    code = error.get("code") or "service_error"
    detail = error.get("detail")
    if isinstance(detail, str) and detail:
        return f"{code}: {detail}"
    return str(code)


def _without_recognized_text(payload: object) -> tuple[object, str]:
    """Separate display text from the contract before validation.

    ``recognized_text`` is not a contract field. Leaving it in the payload
    would make a valid contract look invalid. Any other extra field stays, so
    the validator still rejects unknown data.
    """
    if not isinstance(payload, dict):
        return payload, ""
    recognized = payload.get("recognized_text")
    if not isinstance(recognized, str):
        return payload, ""
    contract = {
        key: value for key, value in payload.items() if key != "recognized_text"
    }
    return contract, recognized.strip()
