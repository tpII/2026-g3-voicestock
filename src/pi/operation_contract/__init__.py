"""Raspberry Pi validation of the operation contract received from the PC.

The Raspberry Pi is the authority for this validation. The structural stage
checks version and shape; product identification and semantic rules follow
in a later stage.
"""

from pi.operation_contract.rejection import RejectionReason, ValidationRejection
from pi.operation_contract.structural import (
    SUPPORTED_OPERATION_COUNT,
    validate_structure,
    validate_structure_json,
)

__all__ = [
    "SUPPORTED_OPERATION_COUNT",
    "RejectionReason",
    "ValidationRejection",
    "validate_structure",
    "validate_structure_json",
]
