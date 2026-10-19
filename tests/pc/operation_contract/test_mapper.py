"""Tests for the PC mapper from the interpreter draft to ContractPayload."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from pc.operation_contract import DraftMappingError, map_draft
from shared.operation_contract import ContractPayload

GOLDEN_PATH = (
    Path(__file__).parents[2] / "fixtures" / "operation_contract" / "golden_drafts.json"
)
GOLDEN_CASES: list[dict[str, Any]] = json.loads(GOLDEN_PATH.read_text("utf-8"))

VALID_DRAFT: dict[str, Any] = {
    "operaciones": [
        {"operacion": "agregar_stock", "producto": "Sprite 2L", "cantidad": 2}
    ]
}


def _with_operation(**changes: Any) -> dict[str, Any]:
    """Return VALID_DRAFT with fields of its operation replaced or removed."""
    draft = copy.deepcopy(VALID_DRAFT)
    operation = draft["operaciones"][0]
    for key, value in changes.items():
        if value is ...:
            del operation[key]
        else:
            operation[key] = value
    return draft


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda case: case["case"])
def test_golden_drafts_map_to_the_expected_contract(case: dict[str, Any]) -> None:
    payload = map_draft(case["draft"])

    assert payload.model_dump(mode="json") == case["contract"]


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda case: case["case"])
def test_golden_contracts_conform_to_the_canonical_model(case: dict[str, Any]) -> None:
    payload = ContractPayload.model_validate(case["contract"])

    assert payload.model_dump(mode="json") == case["contract"]


def test_mapped_payload_serializes_as_utf8_json() -> None:
    draft = _with_operation(producto="Leche La Serenísima 1L")

    raw = map_draft(draft).model_dump_json()

    assert "Serenísima" in raw
    assert json.loads(raw)["contract_version"] == "1"


def test_product_name_is_passed_through_unchanged() -> None:
    draft = _with_operation(producto="  coca-cola ZERO 2l ")

    payload = map_draft(draft)

    # Normalization and identification belong to the Raspberry Pi (ADR-0006).
    assert payload.operations[0].product.name == "  coca-cola ZERO 2l "


@pytest.mark.parametrize("quantity", [0, -1])
def test_quantity_sign_is_left_to_the_raspberry_pi(quantity: int) -> None:
    payload = map_draft(_with_operation(cantidad=quantity))

    assert payload.operations[0].quantity == quantity


@pytest.mark.parametrize("draft", [None, [], "texto", 3])
def test_non_object_draft_is_rejected(draft: object) -> None:
    with pytest.raises(DraftMappingError):
        map_draft(draft)


@pytest.mark.parametrize(
    "draft",
    [
        {},
        {"operaciones": "agregar"},
        {"operaciones": [], "comentario": "extra"},
        {"operaciones": ["agregar_stock"]},
    ],
)
def test_malformed_draft_is_rejected(draft: object) -> None:
    with pytest.raises(DraftMappingError):
        map_draft(draft)


@pytest.mark.parametrize("field", ["operacion", "producto", "cantidad"])
def test_missing_operation_field_is_not_invented(field: str) -> None:
    with pytest.raises(DraftMappingError, match=field):
        map_draft(_with_operation(**{field: ...}))


def test_unknown_operation_field_is_rejected() -> None:
    with pytest.raises(DraftMappingError, match="unidad"):
        map_draft(_with_operation(unidad="kg"))


@pytest.mark.parametrize(
    "operation", ["transferir_stock", "add_stock", "AGREGAR_STOCK", None, 1]
)
def test_unknown_operation_vocabulary_is_rejected(operation: object) -> None:
    with pytest.raises(DraftMappingError, match="operacion"):
        map_draft(_with_operation(operacion=operation))


@pytest.mark.parametrize("product", ["", "   ", None, 7])
def test_blank_or_non_text_product_is_rejected(product: object) -> None:
    with pytest.raises(DraftMappingError, match="producto"):
        map_draft(_with_operation(producto=product))


@pytest.mark.parametrize("quantity", ["2", 2.0, 2.5, True, None])
def test_non_integer_quantity_is_rejected(quantity: object) -> None:
    with pytest.raises(DraftMappingError, match="cantidad"):
        map_draft(_with_operation(cantidad=quantity))
