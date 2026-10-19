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


@dataclass(frozen=True)
class ValidationRejection:
    """Why a payload was rejected. ``detail`` is diagnostic, not contractual."""

    reason: RejectionReason
    detail: str
