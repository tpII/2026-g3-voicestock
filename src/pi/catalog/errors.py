"""Failures of the persistent product catalog.

Callers branch on these types. A catalog write does not report a broken
invariant as a bare ``sqlite3.IntegrityError``.
"""


class CatalogError(Exception):
    """A catalog read or write could not be completed."""


class InvalidCatalogValueError(CatalogError, ValueError):
    """An identifier, name, alias or stock unit is missing or not allowed."""


class UnknownProductError(CatalogError):
    """No complete catalog product has this id.

    ``provisional`` is true when the id belongs to a legacy row that has no
    commercial identity. That row is left untouched.
    """

    def __init__(self, product_id: str, *, provisional: bool = False) -> None:
        self.product_id = product_id
        self.provisional = provisional
        if provisional:
            message = (
                f"product {product_id!r} is a provisional catalog row "
                "without commercial identity"
            )
        else:
            message = f"product {product_id!r} is not in the catalog"
        super().__init__(message)


class UnknownCategoryError(CatalogError):
    """No category has this id."""

    def __init__(self, category_id: str) -> None:
        self.category_id = category_id
        super().__init__(f"category {category_id!r} is not in the catalog")


class DuplicateCategoryError(CatalogError):
    """The category id or its normalized name is already stored."""


class DuplicateProductError(CatalogError):
    """A catalog row already uses this product id."""

    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        super().__init__(f"product {product_id!r} already exists")


class DuplicateIdentityError(CatalogError):
    """Another product has the same normalized canonical attributes."""

    def __init__(self, product_id: str, other_product_id: str) -> None:
        self.product_id = product_id
        self.other_product_id = other_product_id
        super().__init__(
            f"product {product_id!r} has the same identity as {other_product_id!r}"
        )


class UnreachableProductError(CatalogError):
    """An active product cannot be identified by its own attributes."""


class AliasConflictError(CatalogError):
    """The alias is already used by another active product."""


class ProductHasStockError(CatalogError):
    """Retirement was rejected because the stock quantity is positive."""

    def __init__(self, product_id: str, quantity: int) -> None:
        self.product_id = product_id
        self.quantity = quantity
        super().__init__(
            f"product {product_id!r} has stock {quantity} and cannot be retired"
        )


class ProvisionalProductError(CatalogError):
    """A legacy row exists for this id and was not completed or overwritten."""

    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        super().__init__(
            f"product {product_id!r} is a provisional catalog row "
            "and was not overwritten"
        )


class CatalogConflictError(CatalogError):
    """An existing row does not match the authoritative seed."""
