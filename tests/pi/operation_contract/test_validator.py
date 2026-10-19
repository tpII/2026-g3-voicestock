"""Tests for the single validation entry point used by PendingOperationFlow."""

import json
from pathlib import Path
from typing import Any

import pytest

from pi.operation_contract import (
    CatalogProduct,
    InMemoryProductResolver,
    OperationValidator,
    ProductQuery,
    ProductResolution,
    RejectionReason,
    ResolutionStatus,
    ValidatedOperation,
    ValidationRejection,
    load_catalog,
)

CATALOG_PATH = (
    Path(__file__).parents[2]
    / "fixtures"
    / "operation_contract"
    / "october_catalog.json"
)


@pytest.fixture
def validator() -> OperationValidator:
    return OperationValidator(InMemoryProductResolver(load_catalog(CATALOG_PATH)))


def _payload(
    name: str = "Coca Cola Zero 2L",
    operation: str = "add_stock",
    quantity: Any = 2,
    unit: str = "unit",
    **product: Any,
) -> dict[str, Any]:
    return {
        "contract_version": "1",
        "operations": [
            {
                "operation": operation,
                "product": {"name": name, **product},
                "quantity": quantity,
                "unit": unit,
            }
        ],
    }


def _reason(result: object) -> RejectionReason:
    assert isinstance(result, ValidationRejection)
    return result.reason


@pytest.mark.parametrize("operation", ["add_stock", "remove_stock"])
def test_valid_operation_identifies_one_product(
    validator: OperationValidator, operation: str
) -> None:
    result = validator.validate(_payload(operation=operation))

    assert result == ValidatedOperation(
        operation=operation,
        product_id="coca-cola-zero-2l",
        product_name="Coca Cola Zero 2L",
        quantity=2,
        unit="unit",
    )


def test_product_id_and_label_come_from_the_catalog(
    validator: OperationValidator,
) -> None:
    result = validator.validate(_payload(name="leche la serenisima 1l"))

    assert isinstance(result, ValidatedOperation)
    assert result.product_id == "leche-la-serenisima-1l"
    assert result.product_name == "Leche La Serenísima 1L"


def test_raw_json_is_validated_end_to_end(validator: OperationValidator) -> None:
    raw = json.dumps(_payload(name="Arroz Gallo 1kg"), ensure_ascii=False)

    result = validator.validate_json(raw.encode("utf-8"))

    assert isinstance(result, ValidatedOperation)
    assert result.product_id == "arroz-gallo-1kg"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ("not a payload", RejectionReason.INVALID_STRUCTURE),
        ({**_payload(), "contract_version": "2"}, RejectionReason.UNSUPPORTED_VERSION),
        (_payload(operation="transfer_stock"), RejectionReason.UNKNOWN_OPERATION),
        ({"contract_version": "1", "operations": []}, RejectionReason.NO_OPERATIONS),
    ],
)
def test_structural_rejections_stop_before_identification(
    validator: OperationValidator, payload: object, reason: RejectionReason
) -> None:
    assert _reason(validator.validate(payload)) == reason


def test_invalid_json_is_rejected(validator: OperationValidator) -> None:
    assert _reason(validator.validate_json("{")) == RejectionReason.INVALID_JSON


def test_unknown_product_is_rejected(validator: OperationValidator) -> None:
    result = validator.validate(_payload(name="Pepsi 2L"))

    assert _reason(result) == RejectionReason.UNKNOWN_PRODUCT


def test_blank_product_name_is_insufficient(validator: OperationValidator) -> None:
    result = validator.validate(_payload(name="  "))

    assert _reason(result) == RejectionReason.INSUFFICIENT_PRODUCT_ATTRIBUTES


def test_ambiguous_product_is_rejected_with_candidates() -> None:
    validator = OperationValidator(
        InMemoryProductResolver(
            [
                CatalogProduct("coca-original", "Coca Cola", variant="Original"),
                CatalogProduct("coca-zero", "Coca Cola", variant="Zero"),
            ]
        )
    )

    result = validator.validate(_payload(name="Coca Cola"))

    assert isinstance(result, ValidationRejection)
    assert result.reason == RejectionReason.AMBIGUOUS_PRODUCT
    assert set(result.candidate_ids) == {"coca-original", "coca-zero"}


@pytest.mark.parametrize("quantity", [0, -2])
def test_non_positive_quantity_is_rejected(
    validator: OperationValidator, quantity: int
) -> None:
    result = validator.validate(_payload(quantity=quantity))

    assert _reason(result) == RejectionReason.INVALID_QUANTITY


def test_unit_incompatible_with_the_product_is_rejected() -> None:
    validator = OperationValidator(
        InMemoryProductResolver([CatalogProduct("harina", "Harina", units=("kg",))])
    )

    result = validator.validate(_payload(name="Harina"))

    assert _reason(result) == RejectionReason.INCOMPATIBLE_UNIT


def test_identification_runs_before_semantic_rules(
    validator: OperationValidator,
) -> None:
    result = validator.validate(_payload(name="Pepsi 2L", quantity=0))

    assert _reason(result) == RejectionReason.UNKNOWN_PRODUCT


def test_validator_only_reads_through_the_port() -> None:
    queries: list[ProductQuery] = []

    class RecordingResolver:
        def resolve(self, query: ProductQuery) -> ProductResolution:
            queries.append(query)
            return ProductResolution(ResolutionStatus.UNKNOWN)

    result = OperationValidator(RecordingResolver()).validate(
        _payload(name="Arroz", brand="Gallo", presentation="1 kg")
    )

    assert _reason(result) == RejectionReason.UNKNOWN_PRODUCT
    assert queries == [ProductQuery("Arroz", "Gallo", None, "1 kg")]
