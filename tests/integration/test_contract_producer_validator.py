"""The PC producer and the Raspberry Pi validator agree on the contract.

Each golden draft is mapped on the PC side, serialized as it would travel and
validated by the Raspberry Pi structural stage.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from pc.operation_contract import map_draft
from pi.operation_contract import (
    RejectionReason,
    ValidationRejection,
    validate_structure_json,
)
from shared.operation_contract import ContractPayload

GOLDEN_PATH = (
    Path(__file__).parents[1] / "fixtures" / "operation_contract" / "golden_drafts.json"
)
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
