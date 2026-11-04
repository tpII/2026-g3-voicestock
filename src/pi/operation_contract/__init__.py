"""Raspberry Pi validation of the operation contract received from the PC.

The Raspberry Pi is the authority for this validation. ``OperationValidator``
is the single entry point: it runs the structural stage, identifies the
product through a ``ProductResolver`` (ADR-0006) and applies the semantic
rules, producing a ``ValidatedOperation`` or a ``ValidationRejection``.
"""

from pi.operation_contract.products import (
    CatalogProduct,
    InMemoryProductResolver,
    ProductQuery,
    ProductResolution,
    ProductResolver,
    ResolutionStatus,
    load_catalog,
    match_products,
    normalize_attribute,
)
from pi.operation_contract.rejection import RejectionReason, ValidationRejection
from pi.operation_contract.structural import (
    SUPPORTED_OPERATION_COUNT,
    validate_structure,
    validate_structure_json,
)
from pi.operation_contract.validator import OperationValidator, ValidatedOperation

__all__ = [
    "SUPPORTED_OPERATION_COUNT",
    "CatalogProduct",
    "InMemoryProductResolver",
    "OperationValidator",
    "ProductQuery",
    "ProductResolution",
    "ProductResolver",
    "RejectionReason",
    "ResolutionStatus",
    "ValidatedOperation",
    "ValidationRejection",
    "load_catalog",
    "match_products",
    "normalize_attribute",
    "validate_structure",
    "validate_structure_json",
]
