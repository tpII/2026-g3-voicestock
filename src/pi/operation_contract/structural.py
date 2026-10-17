"""Structural validation of a ContractPayload received from the PC.

This stage only checks that the payload is a supported version of the contract
and has the expected shape. It does not look up products, check quantities or
modify inventory: passing it does not make the operation acceptable.
"""

import json

from pydantic import ValidationError

from pi.operation_contract.rejection import RejectionReason, ValidationRejection
from shared.operation_contract import CONTRACT_VERSION, ContractPayload

# Contract version 1 carries a list, but a pending operation holds exactly one
# operation for now. Accepting more must wait until the flow supports it.
SUPPORTED_OPERATION_COUNT = 1

_VOCABULARY_FIELDS = {
    "operation": RejectionReason.UNKNOWN_OPERATION,
    "unit": RejectionReason.UNKNOWN_UNIT,
}


def validate_structure_json(raw: str | bytes) -> ContractPayload | ValidationRejection:
    """Decode a raw JSON document and validate its structure."""
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return ValidationRejection(
            RejectionReason.INVALID_JSON, "payload is not valid UTF-8 JSON"
        )
    return validate_structure(data)


def validate_structure(data: object) -> ContractPayload | ValidationRejection:
    """Validate an already decoded JSON value against the supported contract.

    The version is checked before the fields, so a payload written for another
    version is reported as ``unsupported_version`` rather than as a list of
    field errors.
    """
    if not isinstance(data, dict):
        return ValidationRejection(
            RejectionReason.INVALID_STRUCTURE, "payload must be a JSON object"
        )

    if "contract_version" not in data:
        return ValidationRejection(
            RejectionReason.INVALID_STRUCTURE, "contract_version is required"
        )

    version = data["contract_version"]
    if version != CONTRACT_VERSION:
        return ValidationRejection(
            RejectionReason.UNSUPPORTED_VERSION,
            f"contract version {version!r} is not supported; "
            f"expected {CONTRACT_VERSION!r}",
        )

    try:
        payload = ContractPayload.model_validate(data)
    except ValidationError as error:
        return _rejection_from(error)

    if not payload.operations:
        return ValidationRejection(
            RejectionReason.NO_OPERATIONS, "payload contains no operations"
        )
    if len(payload.operations) > SUPPORTED_OPERATION_COUNT:
        return ValidationRejection(
            RejectionReason.TOO_MANY_OPERATIONS,
            f"payload contains {len(payload.operations)} operations; "
            f"at most {SUPPORTED_OPERATION_COUNT} is supported",
        )

    return payload


def _rejection_from(error: ValidationError) -> ValidationRejection:
    """Map schema errors to one reason.

    A value outside the operation or unit vocabulary gets its own reason only
    when it is the sole kind of problem; any other error makes the payload
    ``invalid_structure``.
    """
    issues = error.errors(include_url=False)
    detail = "; ".join(_describe(issue) for issue in issues)

    vocabulary_reasons = [_vocabulary_reason(issue) for issue in issues]
    if all(vocabulary_reasons):
        return ValidationRejection(vocabulary_reasons[0], detail)
    return ValidationRejection(RejectionReason.INVALID_STRUCTURE, detail)


def _vocabulary_reason(issue: dict) -> RejectionReason | None:
    location = issue["loc"]
    if (
        issue["type"] == "literal_error"
        and isinstance(issue["input"], str)
        and location
        and location[-1] in _VOCABULARY_FIELDS
    ):
        return _VOCABULARY_FIELDS[location[-1]]
    return None


def _describe(issue: dict) -> str:
    location = ".".join(str(part) for part in issue["loc"]) or "payload"
    return f"{location}: {issue['msg']}"
