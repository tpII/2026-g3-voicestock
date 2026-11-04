"""Product identification port and its in-memory implementation (ADR-0006).

The catalog is the only authority on product identity. A query made of the
attributes in the ContractPayload resolves to exactly one product, or is
rejected as unknown, ambiguous or insufficient. Normalization and matching are
implemented once here so every catalog source behaves the same.
"""

import json
import unicodedata
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

ATTRIBUTES = ("name", "brand", "variant", "presentation")


def normalize_attribute(value: str | None) -> str | None:
    """Apply the fixed normalization of ADR-0006.

    Accents and case are ignored, every non-alphanumeric character becomes a
    space and runs of spaces collapse. A value that is empty afterwards is
    absent. No synonyms, stemming or fuzzy matching are applied.
    """
    if value is None:
        return None
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    spaced = "".join(
        char if char.isalnum() else " " for char in without_marks.casefold()
    )
    return " ".join(spaced.split()) or None


@dataclass(frozen=True)
class ProductQuery:
    """Attributes describing one product, as received in the contract."""

    name: str | None
    brand: str | None = None
    variant: str | None = None
    presentation: str | None = None


@dataclass(frozen=True)
class CatalogProduct:
    """One catalog entry. ``product_id`` is opaque and owned by the catalog.

    ``units`` lists the units in which the product can be counted.
    """

    product_id: str
    name: str
    brand: str | None = None
    variant: str | None = None
    presentation: str | None = None
    units: tuple[str, ...] = ("unit",)

    def __post_init__(self) -> None:
        if not isinstance(self.product_id, str) or not self.product_id.strip():
            raise ValueError("product_id must be a non-blank string")
        if normalize_attribute(self.name) is None:
            raise ValueError(f"product {self.product_id!r} needs a non-blank name")
        if not self.units:
            raise ValueError(f"product {self.product_id!r} needs at least one unit")

    @property
    def display_name(self) -> str:
        """Label built from the catalog attributes, not from the model."""
        parts = (self.name, self.brand, self.variant, self.presentation)
        return " ".join(part for part in parts if part)


class ResolutionStatus(StrEnum):
    """Outcome of resolving one product query."""

    IDENTIFIED = "identified"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_ATTRIBUTES = "insufficient_attributes"


@dataclass(frozen=True)
class ProductResolution:
    """Result of a resolution. Only ``identified`` carries a product."""

    status: ResolutionStatus
    product: CatalogProduct | None = None
    candidate_ids: tuple[str, ...] = field(default=())


@runtime_checkable
class ProductResolver(Protocol):
    """Port every catalog source implements, independent of storage."""

    def resolve(self, query: ProductQuery) -> ProductResolution:
        """Resolve the query following the matching rule of ADR-0006."""


def match_products(
    query: ProductQuery, products: Iterable[CatalogProduct]
) -> ProductResolution:
    """Apply the matching rule of ADR-0006 to a list of catalog products.

    A product is a candidate when it has every attribute present in the query
    with the same normalized value. There is no tie-breaking.
    """
    wanted = _normalized_attributes(query)
    if "name" not in wanted:
        return ProductResolution(ResolutionStatus.INSUFFICIENT_ATTRIBUTES)

    candidates = [
        product
        for product in products
        if all(
            normalize_attribute(getattr(product, attribute)) == value
            for attribute, value in wanted.items()
        )
    ]
    if not candidates:
        return ProductResolution(ResolutionStatus.UNKNOWN)
    if len(candidates) > 1:
        return ProductResolution(
            ResolutionStatus.AMBIGUOUS,
            candidate_ids=tuple(product.product_id for product in candidates),
        )
    return ProductResolution(ResolutionStatus.IDENTIFIED, product=candidates[0])


class InMemoryProductResolver:
    """Resolver over a fixed list of products, used until ProductCatalog exists.

    Construction fails when the catalog breaks the invariant of ADR-0006: every
    product must be identifiable by querying with all of its own attributes.
    """

    def __init__(self, products: Sequence[CatalogProduct]) -> None:
        self._products = tuple(products)
        _check_catalog(self._products)

    def resolve(self, query: ProductQuery) -> ProductResolution:
        return match_products(query, self._products)


def load_catalog(path: Path) -> list[CatalogProduct]:
    """Read catalog products from a JSON list of objects."""
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("catalog file must contain a JSON list")
    return [
        CatalogProduct(
            **{
                **entry,
                "units": tuple(entry.get("units", ("unit",))),
            }
        )
        for entry in entries
    ]


def _normalized_attributes(source: ProductQuery | CatalogProduct) -> dict[str, str]:
    values = {
        attribute: normalize_attribute(getattr(source, attribute))
        for attribute in ATTRIBUTES
    }
    return {attribute: value for attribute, value in values.items() if value}


def _check_catalog(products: tuple[CatalogProduct, ...]) -> None:
    ids = [product.product_id for product in products]
    if duplicated := sorted({item for item in ids if ids.count(item) > 1}):
        raise ValueError(f"duplicated product ids: {duplicated}")

    unreachable = [
        product.product_id
        for product in products
        if match_products(ProductQuery(**_normalized_attributes(product)), products)
        != ProductResolution(ResolutionStatus.IDENTIFIED, product=product)
    ]
    if unreachable:
        raise ValueError(
            f"products not identifiable by their own attributes: {unreachable}"
        )
