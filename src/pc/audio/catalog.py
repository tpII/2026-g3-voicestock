"""Catalog attribute matching for the PC audio pipeline.

The rule is the one in ADR-0006: a candidate must carry every supplied
attribute with the same normalized value, and there is no tie-break. The
Raspberry Pi remains the component that assigns ``product_id``. This module
only decides whether the description is unique enough to send.
"""

import json
import re
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
    """Attributes copied from one catalog row.

    ``product_id`` is kept so a snapshot can be checked for duplicates. It is
    not part of the prompt and it is not sent in the operation contract.
    ``aliases`` are phrases the model may recognize. They are not identities.
    """

    name: str
    brand: str | None = None
    variant: str | None = None
    presentation: str | None = None
    aliases: tuple[str, ...] = ()
    product_id: str | None = None

    def as_prompt_row(self) -> dict[str, str | None | list[str]]:
        """Attributes and aliases the model is allowed to read."""
        return {
            "nombre": self.name,
            "marca": self.brand,
            "variante": self.variant,
            "presentacion": self.presentation,
            "alias": list(self.aliases),
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
                aliases=_aliases(item.get("aliases"), index),
                product_id=_product_id(item.get("product_id"), index),
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


SNAPSHOT_VERSION = 1
_REVISION = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class InstalledCatalog:
    """One validated snapshot and the entries the pipeline may use."""

    revision: str
    entries: tuple[CatalogEntry, ...]


class CatalogSnapshotError(ValueError):
    """The Pi snapshot cannot be used for interpretation."""


def parse_catalog_snapshot(body: object, etag: str | None) -> InstalledCatalog:
    """Validate a catalog body against its ETag. Identifiers stay out of prompts."""
    if not isinstance(body, dict):
        raise CatalogSnapshotError("catalog snapshot is not an object")
    if body.get("version") != SNAPSHOT_VERSION:
        raise CatalogSnapshotError("catalog snapshot version is not supported")
    revision = body.get("revision")
    if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
        raise CatalogSnapshotError("catalog revision is missing or malformed")
    if _etag_revision(etag) != revision:
        raise CatalogSnapshotError("catalog etag does not match the revision")
    products = body.get("products")
    if not isinstance(products, list) or not products:
        raise CatalogSnapshotError("catalog snapshot has no products")
    entries = tuple(_snapshot_entry(item, index) for index, item in enumerate(products))
    _require_identifiable(entries)
    return InstalledCatalog(revision, entries)


def _etag_revision(header: str | None) -> str | None:
    if header is None:
        return None
    text = header.strip()
    if text[:2].upper() == "W/":
        text = text[2:].strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        return None
    return text[1:-1]


def _snapshot_entry(item: object, index: int) -> CatalogEntry:
    if not isinstance(item, dict):
        raise CatalogSnapshotError(f"catalog product {index} is not an object")
    name = item.get("name")
    if not isinstance(name, str) or normalize_attribute(name) is None:
        raise CatalogSnapshotError(f"catalog product {index} needs a name")
    product_id = item.get("product_id")
    if not isinstance(product_id, str) or not product_id.strip():
        raise CatalogSnapshotError(f"catalog product {index} needs a product id")
    units = item.get("units")
    if (
        not isinstance(units, list)
        or not units
        or not all(isinstance(unit, str) and unit.strip() for unit in units)
    ):
        raise CatalogSnapshotError(f"catalog product {index} needs units")
    try:
        return CatalogEntry(
            name=name.strip(),
            brand=_optional(item.get("brand"), index, "brand"),
            variant=_optional(item.get("variant"), index, "variant"),
            presentation=_optional(item.get("presentation"), index, "presentation"),
            aliases=_snapshot_aliases(item.get("aliases"), index),
            product_id=product_id.strip(),
        )
    except ValueError as error:
        raise CatalogSnapshotError(str(error)) from error


def _snapshot_aliases(value: object, index: int) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise CatalogSnapshotError(f"catalog product {index} aliases must be a list")
    aliases: list[str] = []
    for alias in value:
        if not isinstance(alias, str) or normalize_attribute(alias) is None:
            raise CatalogSnapshotError(f"catalog product {index} has a blank alias")
        aliases.append(alias.strip())
    return tuple(aliases)


def _require_identifiable(entries: tuple[CatalogEntry, ...]) -> None:
    ids = [entry.product_id for entry in entries]
    duplicated = sorted(
        {item for item in ids if item is not None and ids.count(item) > 1}
    )
    if duplicated:
        raise CatalogSnapshotError("catalog product ids are duplicated")
    for entry in entries:
        described = ProductDescription(
            name=entry.name,
            brand=entry.brand,
            variant=entry.variant,
            presentation=entry.presentation,
        )
        if match_description(described, entries) is not ProductMatch.IDENTIFIED:
            raise CatalogSnapshotError(
                "a catalog product is not identifiable by its attributes"
            )


def _optional(value: object, index: int, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"catalog item {index} field {field} must be a string")
    return value


def prompt_rows(
    entries: tuple[CatalogEntry, ...],
) -> list[dict[str, str | None | list[str]]]:
    """Catalog rows for the model prompt, in snapshot order."""
    return [entry.as_prompt_row() for entry in entries]


def _aliases(value: object, index: int) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"catalog item {index} aliases must be a list of strings")
    return tuple(value)


def _product_id(value: object, index: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"catalog item {index} product_id must be a non-blank string")
    return value.strip()
