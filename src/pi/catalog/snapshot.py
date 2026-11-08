"""Versioned snapshot of the active catalog used for interpretation.

The revision is a hash of that content. It changes when an active product,
a canonical attribute or an alias changes, and it stays the same when the
content does not. It is not the database migration version.

Product ids travel with the snapshot so the Raspberry Pi can diagnose a
later resolution. They are not an identity the language model may assign.
"""

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from pi.operation_contract.products import normalize_attribute

CATALOG_SNAPSHOT_VERSION = 1


@dataclass(frozen=True)
class CatalogSnapshotProduct:
    """One active product as interpretation context, without stock."""

    product_id: str
    name: str
    brand: str | None
    variant: str | None
    presentation: str | None
    units: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class CatalogSnapshot:
    """Closed active catalog at one deterministic revision."""

    version: int
    revision: str
    products: tuple[CatalogSnapshotProduct, ...]

    def as_dict(self) -> dict[str, object]:
        """JSON-ready mapping. Key order is not significant; the hash is."""
        return {
            "version": self.version,
            "revision": self.revision,
            "products": [_product_payload(product) for product in self.products],
        }


@runtime_checkable
class CatalogSnapshotReader(Protocol):
    """Read-only port the HTTP adapter calls. It does not open the file."""

    def read_snapshot(self) -> CatalogSnapshot:
        """Return the current active catalog snapshot."""


def build_snapshot(products: Sequence[CatalogSnapshotProduct]) -> CatalogSnapshot:
    """Build a snapshot whose revision depends only on the effective content."""
    ordered = tuple(
        sorted(
            (_ordered_product(product) for product in products),
            key=lambda product: product.product_id,
        )
    )
    return CatalogSnapshot(
        version=CATALOG_SNAPSHOT_VERSION,
        revision=catalog_revision(ordered),
        products=ordered,
    )


def catalog_revision(products: Sequence[CatalogSnapshotProduct]) -> str:
    """Return the SHA-256 hex digest of the canonical product array."""
    payload = [_product_payload(product) for product in products]
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _ordered_product(product: CatalogSnapshotProduct) -> CatalogSnapshotProduct:
    aliases = tuple(
        sorted(
            product.aliases,
            key=lambda alias: (normalize_attribute(alias) or "", alias),
        )
    )
    return CatalogSnapshotProduct(
        product_id=product.product_id,
        name=product.name,
        brand=product.brand,
        variant=product.variant,
        presentation=product.presentation,
        units=tuple(product.units),
        aliases=aliases,
    )


def _product_payload(product: CatalogSnapshotProduct) -> dict[str, object]:
    return {
        "aliases": list(product.aliases),
        "brand": product.brand,
        "name": product.name,
        "presentation": product.presentation,
        "product_id": product.product_id,
        "units": list(product.units),
        "variant": product.variant,
    }
