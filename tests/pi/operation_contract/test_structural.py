"""Tests for the structural validation stage on the Raspberry Pi."""

import copy
import json
from typing import Any

import pytest

from pi.operation_contract import (
    RejectionReason,
    ValidationRejection,
    validate_structure,
    validate_structure_json,
)
from shared.operation_contract import (
    ContractPayload,
    OperationItem,
    ProductDescription,
)

VALID_PAYLOAD: dict[str, Any] = {
    "contract_version": "1",
    "operations": [
        {
            "operation": "add_stock",
            "product": {
                "name": "Coca Cola",
                "brand": None,
                "variant": "Zero",
                "presentation": "1.5 L",
            },
            "quantity": 2,
            "unit": "unit",
        }
    ],
}


def _payload(**changes: Any) -> dict[str, Any]:
    """Return a copy of VALID_PAYLOAD with nested keys replaced or removed.

    Keys are paths separated by ``__``, with list indexes as digits; a value of
    ``...`` removes the key.
    """
    payload = copy.deepcopy(VALID_PAYLOAD)
    for path, value in changes.items():
        *parents, key = path.split("__")
        target: Any = payload
        for part in parents:
            target = target[int(part)] if part.isdigit() else target[part]
        if value is ...:
            del target[key]
        else:
            target[key] = value
    return payload


def _reason(result: object) -> RejectionReason:
    assert isinstance(result, ValidationRejection)
    return result.reason


def test_valid_payload_is_accepted() -> None:
    result = validate_structure(VALID_PAYLOAD)

    assert isinstance(result, ContractPayload)
    item = result.operations[0]
    assert item.operation == "add_stock"
    assert item.product.name == "Coca Cola"
    assert item.product.variant == "Zero"
    assert item.quantity == 2


def test_valid_raw_json_is_accepted_from_text_and_utf8_bytes() -> None:
    raw = json.dumps(VALID_PAYLOAD, ensure_ascii=False)

    assert isinstance(validate_structure_json(raw), ContractPayload)
    assert isinstance(validate_structure_json(raw.encode("utf-8")), ContractPayload)


def test_optional_product_attributes_may_be_omitted() -> None:
    payload = _payload(
        operations__0__product={"name": "leche La Serenísima"},
    )

    result = validate_structure(payload)

    assert isinstance(result, ContractPayload)
    assert result.operations[0].product.brand is None


def test_payload_emitted_by_the_shared_model_passes_the_validator() -> None:
    emitted = ContractPayload(
        contract_version="1",
        operations=[
            OperationItem(
                operation="remove_stock",
                product=ProductDescription(name="fideos", brand="Matarazzo"),
                quantity=3,
                unit="unit",
            )
        ],
    ).model_dump_json()

    assert validate_structure_json(emitted) == ContractPayload.model_validate_json(
        emitted
    )


@pytest.mark.parametrize(
    "raw",
    ["", "not json", "{", '{"contract_version": "1",}', b"\xff\xfe", "NaN NaN"],
)
def test_non_json_is_rejected(raw: str | bytes) -> None:
    assert _reason(validate_structure_json(raw)) == RejectionReason.INVALID_JSON


@pytest.mark.parametrize("data", [None, "texto", 3, [VALID_PAYLOAD]])
def test_non_object_is_rejected(data: object) -> None:
    assert _reason(validate_structure(data)) == RejectionReason.INVALID_STRUCTURE


def test_missing_version_is_rejected_as_invalid_structure() -> None:
    result = validate_structure(_payload(contract_version=...))

    assert _reason(result) == RejectionReason.INVALID_STRUCTURE


@pytest.mark.parametrize("version", ["2", "1.0", 1, None])
def test_other_versions_are_unsupported(version: object) -> None:
    result = validate_structure(_payload(contract_version=version))

    assert _reason(result) == RejectionReason.UNSUPPORTED_VERSION


def test_version_is_checked_before_fields() -> None:
    result = validate_structure({"contract_version": "2", "something": "else"})

    assert _reason(result) == RejectionReason.UNSUPPORTED_VERSION


@pytest.mark.parametrize(
    "path",
    [
        "operations",
        "operations__0__operation",
        "operations__0__product",
        "operations__0__product__name",
        "operations__0__quantity",
        "operations__0__unit",
    ],
)
def test_missing_required_field_is_rejected(path: str) -> None:
    result = validate_structure(_payload(**{path: ...}))

    assert _reason(result) == RejectionReason.INVALID_STRUCTURE


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("operations", {"operation": "add_stock"}),
        ("operations__0__quantity", "2"),
        ("operations__0__quantity", 2.0),
        ("operations__0__quantity", True),
        ("operations__0__product", "Coca Cola"),
        ("operations__0__product__name", 5),
        ("operations__0__product__brand", ["Coca Cola"]),
        ("operations__0__operation", 1),
        ("operations__0__unit", None),
    ],
)
def test_invalid_type_is_rejected(path: str, value: object) -> None:
    result = validate_structure(_payload(**{path: value}))

    assert _reason(result) == RejectionReason.INVALID_STRUCTURE


@pytest.mark.parametrize(
    "path",
    ["extra", "operations__0__extra", "operations__0__product__product_id"],
)
def test_unknown_fields_are_rejected_at_every_level(path: str) -> None:
    result = validate_structure(_payload(**{path: "unexpected"}))

    assert _reason(result) == RejectionReason.INVALID_STRUCTURE


def test_unknown_operation_is_rejected() -> None:
    result = validate_structure(_payload(operations__0__operation="transfer_stock"))

    assert _reason(result) == RejectionReason.UNKNOWN_OPERATION


@pytest.mark.parametrize("operation", ["agregar_stock", "ADD_STOCK"])
def test_operation_vocabulary_is_exact(operation: str) -> None:
    result = validate_structure(_payload(operations__0__operation=operation))

    assert _reason(result) == RejectionReason.UNKNOWN_OPERATION


def test_unknown_unit_is_rejected() -> None:
    result = validate_structure(_payload(operations__0__unit="kg"))

    assert _reason(result) == RejectionReason.UNKNOWN_UNIT


def test_unknown_operation_with_other_errors_is_invalid_structure() -> None:
    result = validate_structure(
        _payload(operations__0__operation="transfer_stock", operations__0__quantity=...)
    )

    assert _reason(result) == RejectionReason.INVALID_STRUCTURE


def test_empty_operation_list_is_rejected() -> None:
    result = validate_structure(_payload(operations=[]))

    assert _reason(result) == RejectionReason.NO_OPERATIONS


def test_more_than_one_operation_is_rejected() -> None:
    operation = VALID_PAYLOAD["operations"][0]
    result = validate_structure(_payload(operations=[operation, operation]))

    assert _reason(result) == RejectionReason.TOO_MANY_OPERATIONS


@pytest.mark.parametrize("quantity", [0, -3])
def test_quantity_sign_is_left_to_semantic_validation(quantity: int) -> None:
    result = validate_structure(_payload(operations__0__quantity=quantity))

    assert isinstance(result, ContractPayload)


def test_unknown_product_is_left_to_product_identification() -> None:
    result = validate_structure(
        _payload(operations__0__product={"name": "producto inexistente"})
    )

    assert isinstance(result, ContractPayload)


def test_rejection_detail_names_the_failing_field() -> None:
    result = validate_structure(_payload(operations__0__quantity="dos"))

    assert isinstance(result, ValidationRejection)
    assert "operations.0.quantity" in result.detail
