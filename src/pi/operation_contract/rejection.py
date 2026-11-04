"""Typed rejection of an interpretation that cannot become an operation."""

from dataclasses import dataclass
from enum import StrEnum


class RejectionReason(StrEnum):
    """Stable reasons a caller can branch on without reading ``detail``."""

    INVALID_JSON = "invalid_json"
    INVALID_STRUCTURE = "invalid_structure"
    UNSUPPORTED_VERSION = "unsupported_version"
    UNKNOWN_OPERATION = "unknown_operation"
    UNKNOWN_UNIT = "unknown_unit"
    NO_OPERATIONS = "no_operations"
    TOO_MANY_OPERATIONS = "too_many_operations"
    INSUFFICIENT_PRODUCT_ATTRIBUTES = "insufficient_product_attributes"
    UNKNOWN_PRODUCT = "unknown_product"
    AMBIGUOUS_PRODUCT = "ambiguous_product"
    INVALID_QUANTITY = "invalid_quantity"
    INCOMPATIBLE_UNIT = "incompatible_unit"


@dataclass(frozen=True)
class ValidationRejection:
    """Why a payload was rejected. ``detail`` is diagnostic, not contractual.

    ``candidate_ids`` lists the matching products of an ``ambiguous_product``
    rejection for diagnostics. None of them is selected.
    """

    reason: RejectionReason
    detail: str
    candidate_ids: tuple[str, ...] = ()
