"""Tests for the canonical ContractPayload definition."""

import pytest
from pydantic import ValidationError

from shared.operation_contract import (
    CONTRACT_VERSION,
    OPERATIONS,
    UNITS,
    ContractPayload,
    OperationItem,
    ProductDescription,
    contract_json_schema,
)


def test_vocabularies_of_version_one() -> None:
    assert CONTRACT_VERSION == "1"
    assert OPERATIONS == ("add_stock", "remove_stock")
    assert UNITS == ("unit",)


def test_payload_built_by_a_producer_serializes_to_the_documented_shape() -> None:
    payload = ContractPayload(
        contract_version=CONTRACT_VERSION,
        operations=[
            OperationItem(
                operation="add_stock",
                product=ProductDescription(name="arroz", brand="Gallo"),
                quantity=2,
                unit="unit",
            )
        ],
    )

    assert payload.model_dump(mode="json") == {
        "contract_version": "1",
        "operations": [
            {
                "operation": "add_stock",
                "product": {
                    "name": "arroz",
                    "brand": "Gallo",
                    "variant": None,
                    "presentation": None,
                },
                "quantity": 2,
                "unit": "unit",
            }
        ],
    }


def test_product_description_has_no_identifier() -> None:
    with pytest.raises(ValidationError):
        ProductDescription(name="arroz", product_id="p-1")


def test_json_schema_fixes_version_and_forbids_unknown_fields() -> None:
    schema = contract_json_schema()
    definitions = schema["$defs"]

    assert schema["properties"]["contract_version"]["const"] == "1"
    assert schema["additionalProperties"] is False
    assert definitions["OperationItem"]["additionalProperties"] is False
    assert definitions["ProductDescription"]["additionalProperties"] is False
    assert set(schema["required"]) == {"contract_version", "operations"}
    assert set(definitions["OperationItem"]["required"]) == {
        "operation",
        "product",
        "quantity",
        "unit",
    }
    assert definitions["ProductDescription"]["required"] == ["name"]
