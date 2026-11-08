"""Product, category and alias as the catalog stores them.

Identity is the normalized tuple ``name``, ``brand``, ``variant`` and
``presentation`` from ADR-0006. Category, aliases and stock quantity are not
part of that identity. The MVP counts every product as ``unit``; the
presentation describes the package and is not a stock unit.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from pi.catalog.errors import InvalidCatalogValueError
from pi.operation_contract.products import normalize_attribute

STOCK_UNIT = "unit"


@dataclass(frozen=True)
class Category:
    """One controlled category. ``category_id`` does not identify a product."""

    category_id: str
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "category_id", _identifier(self.category_id, "category_id")
        )
        object.__setattr__(self, "name", _required_text(self.name, "category name"))

    @property
    def name_key(self) -> str:
        """Normalized name used to reject collisions such as accents or case."""
        key = normalize_attribute(self.name)
        if key is None:
            raise InvalidCatalogValueError("category name must be a non-blank string")
        return key


@dataclass(frozen=True)
class Product:
    """One commercially distinguishable product.

    ``product_id`` is opaque, stable and never reused. ``retired`` keeps the
    row for history. Aliases are alternative phrases for interpretation; they
    are not matching keys.
    """

    product_id: str
    name: str
    category_id: str
    stock_unit: str = STOCK_UNIT
    brand: str | None = None
    variant: str | None = None
    presentation: str | None = None
    retired: bool = False
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.retired) is not bool:
            raise InvalidCatalogValueError("retired must be a bool")
        object.__setattr__(
            self, "product_id", _identifier(self.product_id, "product_id")
        )
        object.__setattr__(
            self, "category_id", _identifier(self.category_id, "category_id")
        )
        object.__setattr__(self, "name", _required_text(self.name, "name"))
        object.__setattr__(self, "brand", _optional_text(self.brand, "brand"))
        object.__setattr__(self, "variant", _optional_text(self.variant, "variant"))
        object.__setattr__(
            self, "presentation", _optional_text(self.presentation, "presentation")
        )
        object.__setattr__(self, "aliases", _aliases(self.aliases))
        if self.stock_unit != STOCK_UNIT:
            raise InvalidCatalogValueError(
                f"stock_unit must be {STOCK_UNIT!r}, got {self.stock_unit!r}"
            )

    def identity_key(self) -> tuple[str, str, str, str]:
        """Normalized canonical attributes. Category and aliases are excluded."""
        return (
            _present_key(self.name),
            _present_key(self.brand),
            _present_key(self.variant),
            _present_key(self.presentation),
        )


def clean_alias(value: object) -> str:
    """Return a stored alias, or reject one that normalization would drop."""
    if not isinstance(value, str) or normalize_attribute(value) is None:
        raise InvalidCatalogValueError("alias must be a non-blank string")
    return value.strip()


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidCatalogValueError(f"{field} must be a non-blank string")
    return value.strip()


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or normalize_attribute(value) is None:
        raise InvalidCatalogValueError(f"{field} must be a non-blank string")
    return value.strip()


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidCatalogValueError(f"{field} must be a string or None")
    if normalize_attribute(value) is None:
        return None
    return value.strip()


def _aliases(values: object) -> tuple[str, ...]:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise InvalidCatalogValueError("aliases must be a sequence of strings")
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        alias = clean_alias(value)
        key = normalize_attribute(alias)
        if key in seen:
            raise InvalidCatalogValueError(f"duplicated alias {alias!r}")
        if key is None:
            raise InvalidCatalogValueError("alias must be a non-blank string")
        seen.add(key)
        cleaned.append(alias)
    return tuple(cleaned)


def _present_key(value: str | None) -> str:
    return normalize_attribute(value) or ""
