"""Persistent product catalog of the Raspberry Pi database.

The catalog owns products, controlled categories and aliases. It does not own
stock quantities or movement history. ``load_initial_catalog`` is the seed
entrypoint. ``SqliteProductResolver`` is the ADR-0006 adapter over the same
tables.
"""

from pi.catalog.errors import (
    AliasConflictError,
    CatalogConflictError,
    CatalogError,
    DuplicateCategoryError,
    DuplicateIdentityError,
    DuplicateProductError,
    InvalidCatalogValueError,
    ProductHasStockError,
    ProvisionalProductError,
    UnknownCategoryError,
    UnknownProductError,
    UnreachableProductError,
)
from pi.catalog.model import STOCK_UNIT, Category, Product
from pi.catalog.resolver import SqliteProductResolver
from pi.catalog.seed import load_initial_catalog
from pi.catalog.snapshot import (
    CATALOG_SNAPSHOT_VERSION,
    CatalogSnapshot,
    CatalogSnapshotProduct,
    CatalogSnapshotReader,
)
from pi.catalog.store import CatalogService

__all__ = [
    "CATALOG_SNAPSHOT_VERSION",
    "STOCK_UNIT",
    "AliasConflictError",
    "CatalogConflictError",
    "CatalogError",
    "CatalogService",
    "CatalogSnapshot",
    "CatalogSnapshotProduct",
    "CatalogSnapshotReader",
    "Category",
    "DuplicateCategoryError",
    "DuplicateIdentityError",
    "DuplicateProductError",
    "InvalidCatalogValueError",
    "Product",
    "ProductHasStockError",
    "ProvisionalProductError",
    "SqliteProductResolver",
    "UnknownCategoryError",
    "UnknownProductError",
    "UnreachableProductError",
    "load_initial_catalog",
]
