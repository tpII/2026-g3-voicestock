"""SQLite persistence for the product catalog.

``CatalogService`` uses the connection it is given and never opens the
database file itself. Reads do not start a transaction, so they see the
caller's uncommitted changes. Each write joins a transaction that is already
open and does not commit it. Without one, the write opens
``pi.storage.transaction`` and commits or rolls back that unit of work.

The service does not change stock quantities or movement history. Retirement
reads ``inventory_stock.quantity`` inside the same transaction as the
retirement update.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from pi.catalog.errors import (
    AliasConflictError,
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
from pi.catalog.model import STOCK_UNIT, Category, Product, clean_alias
from pi.catalog.snapshot import (
    CatalogSnapshot,
    CatalogSnapshotProduct,
    build_snapshot,
)
from pi.operation_contract.products import (
    CatalogProduct,
    ensure_catalog_identifiable,
    normalize_attribute,
)
from pi.storage import transaction

_PRODUCT_COLUMNS = (
    "product_id",
    "name",
    "brand",
    "variant",
    "presentation",
    "category_id",
    "stock_unit",
    "retired",
)
_SELECT_PRODUCTS = (
    f"SELECT {', '.join(_PRODUCT_COLUMNS)} FROM catalog_products WHERE name IS NOT NULL"
)


class CatalogService:
    """Reads and the few writes of the persistent product catalog.

    Construction does not migrate the database and does not load the seed.
    The caller opens the connection, applies migrations and decides when a
    unit of work commits. The connection is used by one thread.
    """

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get_category(self, category_id: str) -> Category:
        """Return one category, or raise ``UnknownCategoryError``."""
        row = self._connection.execute(
            "SELECT category_id, name FROM catalog_categories WHERE category_id = ?",
            (category_id,),
        ).fetchone()
        if row is None:
            raise UnknownCategoryError(category_id)
        return Category(category_id=row[0], name=row[1])

    def list_categories(self) -> tuple[Category, ...]:
        """Return every category, ordered by ``category_id``."""
        rows = self._connection.execute(
            "SELECT category_id, name FROM catalog_categories ORDER BY category_id"
        ).fetchall()
        return tuple(Category(category_id=row[0], name=row[1]) for row in rows)

    def get_product(self, product_id: str) -> Product:
        """Return one complete product, including a retired one.

        A missing id and a provisional legacy row both raise
        ``UnknownProductError``. The provisional flag distinguishes them.
        """
        row = self._connection.execute(
            f"SELECT {', '.join(_PRODUCT_COLUMNS)} FROM catalog_products "
            "WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        if row is None:
            raise UnknownProductError(product_id)
        if row[1] is None:
            raise UnknownProductError(product_id, provisional=True)
        aliases = self._aliases_for((product_id,)).get(product_id, ())
        return _product_from_row(row, aliases)

    def list_products(
        self,
        *,
        include_retired: bool = False,
        category_id: str | None = None,
    ) -> tuple[Product, ...]:
        """Return complete products, ordered by ``product_id``.

        Retired products are excluded unless ``include_retired`` is true.
        Provisional rows are never returned. An unknown ``category_id``
        raises ``UnknownCategoryError`` instead of looking like an empty
        category.
        """
        if category_id is not None:
            self.get_category(category_id)
        rows = self._connection.execute(
            _SELECT_PRODUCTS + " AND (? OR retired = 0) "
            "AND (? IS NULL OR category_id = ?) ORDER BY product_id",
            (include_retired, category_id, category_id),
        ).fetchall()
        aliases = self._aliases_for(tuple(row[0] for row in rows))
        return tuple(_product_from_row(row, aliases.get(row[0], ())) for row in rows)

    def list_aliases(self, product_id: str) -> tuple[str, ...]:
        """Return the aliases of one complete product, in stable order."""
        self.get_product(product_id)
        return self._aliases_for((product_id,)).get(product_id, ())

    def list_active_product_ids(self) -> tuple[str, ...]:
        """Return the ids of complete, non-retired products, in id order.

        This is the enumeration inventory initialization uses. It does not
        include provisional legacy rows.
        """
        rows = self._connection.execute(
            "SELECT product_id FROM catalog_products "
            "WHERE name IS NOT NULL AND retired = 0 ORDER BY product_id"
        ).fetchall()
        return tuple(product_id for (product_id,) in rows)

    def list_provisional_product_ids(self) -> tuple[str, ...]:
        """Return legacy rows that still have no commercial identity."""
        rows = self._connection.execute(
            "SELECT product_id FROM catalog_products "
            "WHERE name IS NULL ORDER BY product_id"
        ).fetchall()
        return tuple(product_id for (product_id,) in rows)

    def read_active_catalog(self) -> tuple[CatalogProduct, ...]:
        """Project active products to the validator's ``CatalogProduct``.

        ``units`` is the stock unit and nothing else. Aliases are omitted on
        purpose: resolution must not match them.
        """
        return tuple(
            CatalogProduct(
                product_id=product.product_id,
                name=product.name,
                brand=product.brand,
                variant=product.variant,
                presentation=product.presentation,
                units=(product.stock_unit,),
            )
            for product in self.list_products()
        )

    def read_snapshot(self) -> CatalogSnapshot:
        """Return the versioned snapshot of the active catalog.

        Retired products, provisional rows, stock and movement history are
        excluded. Category is excluded because it does not affect
        interpretation.
        """
        products = tuple(
            CatalogSnapshotProduct(
                product_id=product.product_id,
                name=product.name,
                brand=product.brand,
                variant=product.variant,
                presentation=product.presentation,
                units=(product.stock_unit,),
                aliases=product.aliases,
            )
            for product in self.list_products()
        )
        return build_snapshot(products)

    def add_category(self, category: Category) -> None:
        """Insert one category. A repeated id or normalized name is rejected."""
        with self._unit():
            if self._category_id_exists(category.category_id):
                raise DuplicateCategoryError(
                    f"category {category.category_id!r} already exists"
                )
            owner = self._category_name_owner(category.name_key)
            if owner is not None:
                raise DuplicateCategoryError(
                    f"category name {category.name!r} matches {owner!r}"
                )
            self._connection.execute(
                "INSERT INTO catalog_categories (category_id, name, name_key) "
                "VALUES (?, ?, ?)",
                (category.category_id, category.name, category.name_key),
            )

    def add_product(self, product: Product) -> None:
        """Insert one active product and its aliases.

        The id is never reused, including when a provisional row already
        holds it. Canonical attributes cannot be changed through this method.
        The active catalog must still satisfy ADR-0006 after the insert.
        """
        if product.retired:
            raise InvalidCatalogValueError(
                "new products are active; retire them with retire_product"
            )
        with self._unit():
            self._require_new_product(product)
            self._insert_product(product)
            self._require_identifiable()
            for alias in product.aliases:
                self._insert_alias(product.product_id, alias)

    def add_alias(self, product_id: str, alias: str) -> None:
        """Associate one alias with a product.

        The same normalized alias on the same product is kept once, without
        rewriting the stored text. The same alias on two active products is
        rejected. A retired product may share an alias with an active one;
        its aliases stay out of the active snapshot.
        """
        text = clean_alias(alias)
        with self._unit():
            self.get_product(product_id)
            self._insert_alias(product_id, text)

    def retire_product(self, product_id: str) -> Product:
        """Retire a product when it has no stock or its quantity is zero.

        The stock check and the flag update are one unit of work. A positive
        quantity rejects the retirement and leaves the row active. An already
        retired product with no positive stock is returned unchanged. The
        product id, its stock row and its movement history stay in place.
        """
        with self._unit():
            product = self.get_product(product_id)
            quantity = self._stock_quantity(product_id)
            if quantity is not None and quantity > 0:
                raise ProductHasStockError(product_id, quantity)
            if not product.retired:
                self._connection.execute(
                    "UPDATE catalog_products SET retired = 1 WHERE product_id = ?",
                    (product_id,),
                )
            return self.get_product(product_id)

    @contextmanager
    def _unit(self) -> Iterator[None]:
        if self._connection.in_transaction:
            yield
            return
        with transaction(self._connection):
            yield

    def _require_new_product(self, product: Product) -> None:
        if not self._category_id_exists(product.category_id):
            raise UnknownCategoryError(product.category_id)
        row = self._connection.execute(
            "SELECT name FROM catalog_products WHERE product_id = ?",
            (product.product_id,),
        ).fetchone()
        if row is not None:
            if row[0] is None:
                raise ProvisionalProductError(product.product_id)
            raise DuplicateProductError(product.product_id)
        owner = self._identity_owner(product)
        if owner is not None:
            raise DuplicateIdentityError(product.product_id, owner)

    def _insert_product(self, product: Product) -> None:
        name_key, brand_key, variant_key, presentation_key = _stored_keys(product)
        try:
            self._connection.execute(
                "INSERT INTO catalog_products ("
                "product_id, stock_unit, retired, name, brand, variant, "
                "presentation, category_id, name_key, brand_key, variant_key, "
                "presentation_key) VALUES (?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    product.product_id,
                    STOCK_UNIT,
                    product.name,
                    product.brand,
                    product.variant,
                    product.presentation,
                    product.category_id,
                    name_key,
                    brand_key,
                    variant_key,
                    presentation_key,
                ),
            )
        except sqlite3.IntegrityError as error:
            raise _integrity(product.product_id, error) from error

    def _insert_alias(self, product_id: str, alias: str) -> None:
        key = normalize_attribute(alias)
        if key is None:
            raise InvalidCatalogValueError("alias must be a non-blank string")
        product = self.get_product(product_id)
        rows = self._connection.execute(
            "SELECT alias.product_id, product.retired "
            "FROM catalog_aliases AS alias "
            "JOIN catalog_products AS product "
            "ON product.product_id = alias.product_id "
            "WHERE alias.alias_key = ?",
            (key,),
        ).fetchall()
        for other_id, other_retired in rows:
            if other_id == product_id:
                return
            if not product.retired and not other_retired:
                raise AliasConflictError(
                    f"alias {alias!r} belongs to active product {other_id!r}"
                )
        try:
            self._connection.execute(
                "INSERT INTO catalog_aliases (product_id, alias, alias_key) "
                "VALUES (?, ?, ?)",
                (product_id, alias, key),
            )
        except sqlite3.IntegrityError as error:
            raise AliasConflictError(str(error)) from error

    def _require_identifiable(self) -> None:
        try:
            ensure_catalog_identifiable(self.read_active_catalog())
        except ValueError as error:
            raise UnreachableProductError(str(error)) from error

    def _category_id_exists(self, category_id: str) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM catalog_categories WHERE category_id = ?",
            (category_id,),
        ).fetchone()
        return row is not None

    def _category_name_owner(self, name_key: str) -> str | None:
        row = self._connection.execute(
            "SELECT category_id FROM catalog_categories WHERE name_key = ?",
            (name_key,),
        ).fetchone()
        return None if row is None else row[0]

    def _identity_owner(self, product: Product) -> str | None:
        name_key, brand_key, variant_key, presentation_key = _stored_keys(product)
        row = self._connection.execute(
            "SELECT product_id FROM catalog_products "
            "WHERE name_key = ? "
            "AND ifnull(brand_key, '') = ifnull(?, '') "
            "AND ifnull(variant_key, '') = ifnull(?, '') "
            "AND ifnull(presentation_key, '') = ifnull(?, '')",
            (name_key, brand_key, variant_key, presentation_key),
        ).fetchone()
        return None if row is None else row[0]

    def _stock_quantity(self, product_id: str) -> int | None:
        row = self._connection.execute(
            "SELECT quantity FROM inventory_stock WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        return None if row is None else row[0]

    def _aliases_for(self, product_ids: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
        if not product_ids:
            return {}
        placeholders = ", ".join("?" for _ in product_ids)
        rows = self._connection.execute(
            "SELECT product_id, alias FROM catalog_aliases "
            f"WHERE product_id IN ({placeholders}) "
            "ORDER BY product_id, alias_key, alias",
            product_ids,
        ).fetchall()
        grouped: dict[str, list[str]] = {product_id: [] for product_id in product_ids}
        for product_id, alias in rows:
            grouped[product_id].append(alias)
        return {product_id: tuple(aliases) for product_id, aliases in grouped.items()}


def _product_from_row(row: tuple, aliases: tuple[str, ...]) -> Product:
    (
        product_id,
        name,
        brand,
        variant,
        presentation,
        category_id,
        stock_unit,
        retired,
    ) = row
    return Product(
        product_id=product_id,
        name=name,
        brand=brand,
        variant=variant,
        presentation=presentation,
        category_id=category_id,
        stock_unit=stock_unit,
        retired=bool(retired),
        aliases=aliases,
    )


def _stored_keys(
    product: Product,
) -> tuple[str, str | None, str | None, str | None]:
    return (
        normalize_attribute(product.name) or "",
        normalize_attribute(product.brand),
        normalize_attribute(product.variant),
        normalize_attribute(product.presentation),
    )


def _integrity(product_id: str, error: sqlite3.IntegrityError) -> CatalogError:
    message = str(error).lower()
    if "canonical_identity" in message:
        return DuplicateIdentityError(product_id, "another product")
    if "alias belongs" in message:
        return AliasConflictError(str(error))
    if "foreign key" in message:
        return UnknownCategoryError(product_id)
    if "incomplete" in message or "counted in unit" in message:
        return InvalidCatalogValueError(str(error))
    if "product_id" in message:
        return DuplicateProductError(product_id)
    raise error
