"""PC responses are classified before a pending operation can exist."""

from pathlib import Path

from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    RejectionReason,
    load_catalog,
)
from pi.pending_operation.response import OutcomeKind, PcResponseInterpreter
from shared.communication import TransportEnvelope

CATALOG = (
    Path(__file__).parents[2]
    / "fixtures"
    / "operation_contract"
    / "october_catalog.json"
)


class CountingValidator(OperationValidator):
    """Counts validate() calls. The inner validator is the production one."""

    def __init__(self) -> None:
        self.inner = OperationValidator(InMemoryProductResolver(load_catalog(CATALOG)))
        self.calls = 0

    def validate(self, payload: object):  # type: ignore[override]
        self.calls += 1
        return self.inner.validate(payload)


def _contract(recognized_text: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "1",
        "operations": [
            {
                "operation": "add_stock",
                "product": {"name": "Coca Cola Zero 2L"},
                "quantity": 2,
                "unit": "unit",
            }
        ],
    }
    if recognized_text is not None:
        payload["recognized_text"] = recognized_text
    return payload


def _service_success(payload: object) -> TransportEnvelope:
    return TransportEnvelope.success(
        {"status": "success", "payload": payload, "error": None}
    )


def test_a_valid_contract_is_accepted_and_keeps_recognized_text() -> None:
    validator = CountingValidator()
    interpreter = PcResponseInterpreter(validator)

    outcome = interpreter.interpret(_service_success(_contract("sumá dos coca zero")))

    assert outcome.kind is OutcomeKind.ACCEPTED
    assert outcome.recognized_text == "sumá dos coca zero"
    assert outcome.validated_operation is not None
    assert outcome.validated_operation.product_id == "coca-cola-zero-2l"
    assert validator.calls == 1


def test_a_transport_failure_is_not_validated() -> None:
    validator = CountingValidator()
    interpreter = PcResponseInterpreter(validator)

    outcome = interpreter.interpret(
        TransportEnvelope.failure("connection_failed", "PC unreachable")
    )

    assert outcome.kind is OutcomeKind.TRANSPORT_ERROR
    assert "connection_failed" in outcome.detail
    assert outcome.validated_operation is None
    assert validator.calls == 0


def test_a_service_error_is_not_validated() -> None:
    validator = CountingValidator()
    interpreter = PcResponseInterpreter(validator)
    envelope = TransportEnvelope.success(
        {
            "status": "error",
            "payload": None,
            "error": {"code": "provider_failure", "detail": "model down"},
        }
    )

    outcome = interpreter.interpret(envelope)

    assert outcome.kind is OutcomeKind.SERVICE_ERROR
    assert "provider_failure" in outcome.detail
    assert validator.calls == 0


def test_an_incomplete_service_result_is_not_validated() -> None:
    validator = CountingValidator()
    interpreter = PcResponseInterpreter(validator)

    outcome = interpreter.interpret(TransportEnvelope.success({"received_audio": {}}))

    assert outcome.kind is OutcomeKind.SERVICE_ERROR
    assert validator.calls == 0


def test_an_invalid_contract_is_rejected_after_validation() -> None:
    validator = CountingValidator()
    interpreter = PcResponseInterpreter(validator)

    outcome = interpreter.interpret(
        _service_success(
            {
                "contract_version": "1",
                "operations": [
                    {
                        "operation": "add_stock",
                        "product": {"name": "Producto inexistente"},
                        "quantity": 1,
                        "unit": "unit",
                    }
                ],
            }
        )
    )

    assert outcome.kind is OutcomeKind.CONTRACT_REJECTION
    assert outcome.detail.startswith(RejectionReason.UNKNOWN_PRODUCT)
    assert outcome.validated_operation is None
    assert validator.calls == 1


def test_the_audio_stub_payload_is_a_contract_rejection() -> None:
    validator = CountingValidator()
    interpreter = PcResponseInterpreter(validator)
    envelope = _service_success(
        {
            "received_audio": {
                "size_bytes": 10,
                "duration_seconds": 1,
            }
        }
    )

    outcome = interpreter.interpret(envelope)

    assert outcome.kind is OutcomeKind.CONTRACT_REJECTION
    assert validator.calls == 1
