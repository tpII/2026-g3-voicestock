"""Map the interpreter output to the versioned ContractPayload.

This mapper is the only producer of ``ContractPayload`` on the PC. The
interpreter does not know the contract, and the contract does not know the
interpreter's vocabulary: the translation between them lives here.

Until StructuredCommandInterpretation defines a typed ``InterpretationDraft``,
the draft is the decoded JSON the model returns::

    {"operaciones": [{"operacion": "agregar_stock",
                      "producto": "Coca Cola Zero 2L",
                      "cantidad": 2}]}

The mapper does not validate the domain (it does not check products, the sign
of the quantity or how many operations are accepted): the Raspberry Pi does.
It only refuses drafts it cannot translate faithfully.
"""

from collections.abc import Mapping
from typing import Any

from shared.operation_contract import (
    CONTRACT_VERSION,
    ContractPayload,
    OperationItem,
    ProductDescription,
)

DRAFT_OPERATIONS = {
    "agregar_stock": "add_stock",
    "restar_stock": "remove_stock",
}

# Contract version 1 only counts units, and the draft carries no unit: every
# product of the October catalog is counted by item (bottles, packages).
CONTRACT_UNIT = "unit"

_DRAFT_KEYS = {"operaciones"}
_DRAFT_OPERATION_KEYS = {"operacion", "producto", "cantidad"}


class DraftMappingError(ValueError):
    """The draft cannot be translated into a ContractPayload without guessing."""


def map_draft(draft: object) -> ContractPayload:
    """Translate one interpreter draft into a ContractPayload.

    Raises ``DraftMappingError`` when the draft is missing data, has unknown
    fields or uses a vocabulary the mapper does not know. The mapper never
    completes or invents a field to produce a payload.
    """
    if not isinstance(draft, Mapping):
        raise DraftMappingError("draft must be a JSON object")
    _require_keys(draft, _DRAFT_KEYS, "draft")

    operations = draft["operaciones"]
    if not isinstance(operations, list):
        raise DraftMappingError("draft.operaciones must be a list")

    return ContractPayload(
        contract_version=CONTRACT_VERSION,
        operations=[
            _map_operation(item, f"draft.operaciones.{index}")
            for index, item in enumerate(operations)
        ],
    )


def _map_operation(item: object, location: str) -> OperationItem:
    if not isinstance(item, Mapping):
        raise DraftMappingError(f"{location} must be a JSON object")
    _require_keys(item, _DRAFT_OPERATION_KEYS, location)

    operation = item["operacion"]
    if not isinstance(operation, str) or operation not in DRAFT_OPERATIONS:
        raise DraftMappingError(f"{location}.operacion is not a known operation")

    product = item["producto"]
    if not isinstance(product, str) or not product.strip():
        raise DraftMappingError(f"{location}.producto must be a non-blank string")

    quantity = item["cantidad"]
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        raise DraftMappingError(f"{location}.cantidad must be an integer")

    return OperationItem(
        operation=DRAFT_OPERATIONS[operation],
        product=ProductDescription(name=product),
        quantity=quantity,
        unit=CONTRACT_UNIT,
    )


def _require_keys(value: Mapping[str, Any], expected: set[str], location: str) -> None:
    keys = set(value)
    if missing := expected - keys:
        raise DraftMappingError(f"{location} is missing {sorted(missing)}")
    if unknown := keys - expected:
        raise DraftMappingError(f"{location} has unknown fields {sorted(unknown)}")
