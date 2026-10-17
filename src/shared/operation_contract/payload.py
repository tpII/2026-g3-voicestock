"""Versioned ContractPayload: the operation contract the PC emits and the Pi validates.

This module is the single canonical definition of the contract. The PC mapper
builds it and the Raspberry Pi validates incoming payloads against it, so
neither side keeps its own copy of field names, types or vocabularies.
"""

from typing import Any, Literal, get_args

from pydantic import BaseModel, ConfigDict, StrictInt, StrictStr

ContractVersion = Literal["1"]
Operation = Literal["add_stock", "remove_stock"]
Unit = Literal["unit"]

CONTRACT_VERSION: str = get_args(ContractVersion)[0]
OPERATIONS: tuple[str, ...] = get_args(Operation)
UNITS: tuple[str, ...] = get_args(Unit)


class ProductDescription(BaseModel):
    """Attributes that describe a product, as defined by ADR-0006.

    They describe the product; they do not identify it. Only the Raspberry Pi
    assigns a product identity, so the contract has no product identifier.
    """

    model_config = ConfigDict(extra="forbid")

    name: StrictStr
    brand: StrictStr | None = None
    variant: StrictStr | None = None
    presentation: StrictStr | None = None


class OperationItem(BaseModel):
    """One requested inventory operation over one described product."""

    model_config = ConfigDict(extra="forbid")

    operation: Operation
    product: ProductDescription
    quantity: StrictInt
    unit: Unit


class ContractPayload(BaseModel):
    """Version 1 of the operation contract.

    Unknown fields are rejected at every level. ``operations`` is a list so a
    later version can carry several operations without changing its shape;
    which counts are accepted is decided by the validator, not by the schema.
    """

    model_config = ConfigDict(extra="forbid")

    contract_version: ContractVersion
    operations: list[OperationItem]


def contract_json_schema() -> dict[str, Any]:
    """Return the JSON Schema of the supported contract version."""
    return ContractPayload.model_json_schema()
