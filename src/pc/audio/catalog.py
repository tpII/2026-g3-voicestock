"""Catalog attribute matching for the PC audio pipeline.

The rule is the one in ADR-0006: a candidate must carry every supplied
attribute with the same normalized value, and there is no tie-break. The
Raspberry Pi remains the component that assigns ``product_id``. This module
only decides whether the description is unique enough to send.
"""

import json
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from shared.operation_contract import ProductDescription

ATTRIBUTES = ("name", "brand", "variant", "presentation")


class ProductMatch(StrEnum):
    """Whether a description selects one catalog row."""

    IDENTIFIED = "identified"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT = "insufficient"


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Attributes copied from one catalog row. No identifier is exposed."""

    name: str
    brand: str | None = None
    variant: str | None = None
    presentation: str | None = None

    def as_prompt_row(self) -> dict[str, str | None]:
        """Attributes the model is allowed to copy."""
        return {
            "nombre": self.name,
            "marca": self.brand,
            "variante": self.variant,
            "presentacion": self.presentation,
        }


def load_catalog_entries(path: Path) -> tuple[CatalogEntry, ...]:
    """Read catalog attributes from a JSON list. Identifiers are ignored."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"catalog file cannot be read: {path}") from error
    if not isinstance(raw, list) or not raw:
        raise ValueError("catalog file must contain a non-empty JSON list")
    entries: list[CatalogEntry] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"catalog item {index} must be an object")
        name = item.get("name")
        if not isinstance(name, str) or normalize_attribute(name) is None:
            raise ValueError(f"catalog item {index} needs a non-blank name")
        entries.append(
            CatalogEntry(
                name=name,
                brand=_optional(item.get("brand"), index, "brand"),
                variant=_optional(item.get("variant"), index, "variant"),
                presentation=_optional(item.get("presentation"), index, "presentation"),
            )
        )
    return tuple(entries)


def match_description(
    description: ProductDescription, entries: tuple[CatalogEntry, ...]
) -> ProductMatch:
    """Match ``description`` against ``entries`` without choosing a tie."""
    wanted = {
        attribute: normalize_attribute(getattr(description, attribute))
        for attribute in ATTRIBUTES
    }
    wanted = {key: value for key, value in wanted.items() if value is not None}
    if "name" not in wanted:
        return ProductMatch.INSUFFICIENT
    matches = [
        entry
        for entry in entries
        if all(
            normalize_attribute(getattr(entry, attribute)) == value
            for attribute, value in wanted.items()
        )
    ]
    if not matches:
        return ProductMatch.UNKNOWN
    if len(matches) > 1:
        return ProductMatch.AMBIGUOUS
    return ProductMatch.IDENTIFIED


def normalize_attribute(value: str | None) -> str | None:
    """Apply the ADR-0006 normalization used by the Raspberry Pi."""
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


def _optional(value: object, index: int, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"catalog item {index} field {field} must be a string")
    return value


def prompt_rows(entries: tuple[CatalogEntry, ...]) -> list[dict[str, str | None]]:
    """Catalog rows for the model prompt, in file order."""
    return [entry.as_prompt_row() for entry in entries]
