"""Single entry point from a raw ContractPayload to a validated operation.

The stages run in order: structural validation, product identification and
the semantic rules that depend on the identified product. The first failing
stage decides the rejection. No stage modifies stock or history.
"""

from dataclasses import dataclass

from pi.operation_contract.products import (
    ProductQuery,
    ProductResolver,
    ResolutionStatus,
)
from pi.operation_contract.rejection import RejectionReason, ValidationRejection
from pi.operation_contract.structural import (
    validate_structure,
    validate_structure_json,
)
from shared.operation_contract import ContractPayload, OperationItem

_RESOLUTION_REJECTIONS = {
    ResolutionStatus.INSUFFICIENT_ATTRIBUTES: (
        RejectionReason.INSUFFICIENT_PRODUCT_ATTRIBUTES,
        "the product description has no usable name",
    ),
    ResolutionStatus.UNKNOWN: (
        RejectionReason.UNKNOWN_PRODUCT,
        "no catalog product matches the description",
    ),
    ResolutionStatus.AMBIGUOUS: (
        RejectionReason.AMBIGUOUS_PRODUCT,
        "several catalog products match the description",
    ),
}


@dataclass(frozen=True)
class ValidatedOperation:
    """An operation that identifies exactly one product and obeys the rules.

    ``product_id`` is assigned by the catalog, never by the model.
    ``product_name`` is the catalog label to show the operator.
    """

    operation: str
    product_id: str
    product_name: str
    quantity: int
    unit: str


class OperationValidator:
    """Validate payloads received from the PC against one product catalog."""

    def __init__(self, resolver: ProductResolver) -> None:
        self._resolver = resolver

    def validate(self, payload: object) -> ValidatedOperation | ValidationRejection:
        """Validate an already decoded payload, such as ``ServiceResult.payload``."""
        return self._validate_structured(validate_structure(payload))

    def validate_json(
        self, raw: str | bytes
    ) -> ValidatedOperation | ValidationRejection:
        """Validate a raw JSON document."""
        return self._validate_structured(validate_structure_json(raw))

    def _validate_structured(
        self, result: ContractPayload | ValidationRejection
    ) -> ValidatedOperation | ValidationRejection:
        if isinstance(result, ValidationRejection):
            return result
        # The structural stage guarantees exactly one operation.
        return self._validate_item(result.operations[0])

    def _validate_item(
        self, item: OperationItem
    ) -> ValidatedOperation | ValidationRejection:
        product = item.product
        resolution = self._resolver.resolve(
            ProductQuery(
                name=product.name,
                brand=product.brand,
                variant=product.variant,
                presentation=product.presentation,
            )
        )
        if resolution.status in _RESOLUTION_REJECTIONS:
            reason, detail = _RESOLUTION_REJECTIONS[resolution.status]
            return ValidationRejection(reason, detail, resolution.candidate_ids)

        identified = resolution.product
        if identified is None:
            raise RuntimeError("an identified resolution must carry a product")

        if item.quantity <= 0:
            return ValidationRejection(
                RejectionReason.INVALID_QUANTITY,
                f"quantity must be positive, got {item.quantity}",
            )
        if item.unit not in identified.units:
            return ValidationRejection(
                RejectionReason.INCOMPATIBLE_UNIT,
                f"product {identified.product_id!r} is not counted in {item.unit!r}",
            )

        return ValidatedOperation(
            operation=item.operation,
            product_id=identified.product_id,
            product_name=identified.display_name,
            quantity=item.quantity,
            unit=item.unit,
        )
