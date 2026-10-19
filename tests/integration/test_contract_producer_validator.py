"""The PC producer and the Raspberry Pi validator agree on the contract.

Each golden draft is mapped on the PC side, serialized as it would travel and
validated on the Raspberry Pi: first by the structural stage alone, then by
the full validator through the ServiceResult and TransportEnvelope layers.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from pc.interpretation import ServiceResult
from pc.operation_contract import map_draft
from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    RejectionReason,
    ValidatedOperation,
    ValidationRejection,
    load_catalog,
    validate_structure_json,
)
from shared.communication import TransportEnvelope
from shared.operation_contract import ContractPayload

FIXTURES = Path(__file__).parents[1] / "fixtures" / "operation_contract"
GOLDEN_PATH = FIXTURES / "golden_drafts.json"
CATALOG_PATH = FIXTURES / "october_catalog.json"
GOLDEN_CASES = {
    case["case"]: case for case in json.loads(GOLDEN_PATH.read_text("utf-8"))
}

EXPECTED_STRUCTURAL_RESULT: dict[str, RejectionReason | None] = {
    "single_remove": None,
    "single_add_with_variant_in_name": None,
    "single_add_with_accented_name": None,
    "two_operations": RejectionReason.TOO_MANY_OPERATIONS,
    "everything_cancelled": RejectionReason.NO_OPERATIONS,
}


def test_every_golden_case_has_an_expected_result() -> None:
    assert set(EXPECTED_STRUCTURAL_RESULT) == set(GOLDEN_CASES)


@pytest.mark.parametrize("name", sorted(EXPECTED_STRUCTURAL_RESULT))
def test_mapped_payload_passes_the_raspberry_pi_structural_stage(name: str) -> None:
    case: dict[str, Any] = GOLDEN_CASES[name]
    raw = map_draft(case["draft"]).model_dump_json().encode("utf-8")

    result = validate_structure_json(raw)

    expected_reason = EXPECTED_STRUCTURAL_RESULT[name]
    if expected_reason is None:
        assert isinstance(result, ContractPayload)
        assert result.model_dump(mode="json") == case["contract"]
    else:
        assert isinstance(result, ValidationRejection)
        assert result.reason == expected_reason


EXPECTED_PRODUCT_ID: dict[str, str] = {
    "single_remove": "arroz-gallo-1kg",
    "single_add_with_variant_in_name": "coca-cola-zero-2l",
    "single_add_with_accented_name": "leche-la-serenisima-1l",
}


@pytest.mark.parametrize("name", sorted(EXPECTED_STRUCTURAL_RESULT))
def test_full_chain_from_draft_to_validated_operation(name: str) -> None:
    case: dict[str, Any] = GOLDEN_CASES[name]

    # PC: draft -> ContractPayload -> ServiceResult -> TransportEnvelope -> JSON.
    contract = map_draft(case["draft"]).model_dump(mode="json")
    service_result = ServiceResult.success(contract).model_dump(mode="json")
    wire = TransportEnvelope.success(service_result).model_dump_json()

    # Raspberry Pi: JSON -> TransportEnvelope -> ServiceResult payload -> validator.
    envelope = TransportEnvelope.model_validate_json(wire)
    assert envelope.status == "success"
    assert envelope.payload["status"] == "success"
    validator = OperationValidator(InMemoryProductResolver(load_catalog(CATALOG_PATH)))

    result = validator.validate(envelope.payload["payload"])

    if name in EXPECTED_PRODUCT_ID:
        assert isinstance(result, ValidatedOperation)
        assert result.product_id == EXPECTED_PRODUCT_ID[name]
    else:
        assert isinstance(result, ValidationRejection)
        assert result.reason == EXPECTED_STRUCTURAL_RESULT[name]
