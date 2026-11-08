# Product catalog

## Purpose

`pi.catalog` is the product catalog of the Raspberry Pi database. It owns
products, controlled categories and aliases. It does not own stock quantities,
movement history, prices, suppliers or barcodes.

The same SQLite file holds the catalog, the stock and the history. Only the
Raspberry Pi process opens it. The PC and the browser never open the file.
Why there is one file is recorded in
[ADR-0014](../decisions/0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md).
How a product is identified is recorded in
[ADR-0006](../decisions/0006-identify-products-by-unique-attribute-match.md)
and extended by
[ADR-0015](../decisions/0015-persist-the-product-catalog-in-the-pi-database.md).

```text
seed, maintenance ──► CatalogService ──► catalog_products
                                        catalog_categories
                                        catalog_aliases
OperationValidator ──► SqliteProductResolver ──► active products only
GET /api/v1/catalog ──► read_snapshot()
inventory init ──► list_active_product_ids()
                   then pi.inventory.create_stock_record
```

## Domain

| Type | Fields | Role |
| --- | --- | --- |
| `Product` | `product_id`, `name`, `brand`, `variant`, `presentation`, `category_id`, `stock_unit`, `retired`, `aliases` | One commercially distinguishable product |
| `Category` | `category_id`, `name` | Controlled classification. Not an identity attribute |
| alias | text stored on one product | Phrase the interpreter may see. Not a matching key |

`product_id` is the only persistent identifier. It is opaque, unique, stable
and never reused, including after retirement. There is no SKU.

The canonical identity is `name`, `brand`, `variant` and `presentation`.
Normalization is `pi.operation_contract.normalize_attribute`: Unicode NFKD,
case folding, punctuation turned into spaces, collapsed whitespace. Empty
after normalization means absent. No synonyms, no edit distance.

A valid active catalog satisfies `ensure_catalog_identifiable`: every active
product is found by a query that carries all of its own canonical attributes.
A generic product next to a more specific one with the same attributes is
rejected. Two products with the same normalized identity are rejected even if
one is retired. Category, aliases and stock do not take part in that check.

Every product in this MVP has `stock_unit == "unit"`. The presentation
describes the package (`1 kg`, `2.25 L`) and is not the unit used to count
stock. The validator projection is `CatalogProduct.units = (stock_unit,)`.

## Categories and aliases

Categories live in `catalog_categories`. `category_id` is stable. Names are
unique after normalization, so `Lácteos` and `Lacteos` cannot both exist.
Each complete product references exactly one category. The reference is a
foreign key. Listing by category is `list_products(category_id=...)`.

Aliases live in `catalog_aliases`, one row per normalized phrase. A blank
alias is rejected. The same normalized alias on the same product is stored
once and the original text is not rewritten. The same normalized alias cannot
belong to two active products. That holds for an insert, for a change of the
alias text or its normalized key, for a change of the owning product, and for
a return from retired to active. A retired product may keep its aliases; they
are readable on the product and are omitted from the active snapshot. There
is no public API to edit an alias.

`SqliteProductResolver` does not read aliases. A spoken alias becomes a
canonical attribute only if the interpreter on the PC does that translation.
The Raspberry Pi still matches the canonical attributes.

## Retirement

Products are not deleted. `retire_product(product_id)` sets `retired` when
the product has no `inventory_stock` row or that row has quantity zero. A
positive quantity raises `ProductHasStockError` and changes nothing. The
check and the update run in one `pi.storage.transaction`. The schema rejects
the same transition when a writer sets `retired = 1` directly: a trigger
aborts the update while `inventory_stock.quantity > 0`. Zero stock and a
missing stock row stay legal. The stock row is not deleted and its quantity
is not changed.

Retirement keeps the id, the identity, the stock row and the movement
history. A retired product remains available from `get_product` and from
`list_products(include_retired=True)`. It is excluded from
`list_products()`, `list_active_product_ids()`, `read_active_catalog()`,
`read_snapshot()` and from `SqliteProductResolver`. Inventory already rejects
a delta or a new stock row for a retired product.

Canonical attributes are not updated by the public API. A capitalization or
punctuation correction is not offered yet. Replacing a presentation is a new
product id. The API refuses to insert an already retired product; retirement
is only `retire_product`.

## Persistence

Migration 4, `extend_catalog_products`, adds the identity columns, the
category foreign key and `catalog_aliases`. Migrations 1 to 3 are unchanged.
Their SQL is not edited, and the SQL of migration 4 is not edited either:
that version may already be recorded in a development database.

Migration 5, `protect_catalog_retirement_and_aliases`, adds three triggers
and does not rewrite rows:

- `catalog_products_reject_retirement_with_stock` blocks `retired` going
  from 0 to 1 while stock quantity is positive.
- `catalog_aliases_reject_shared_active_alias_on_update` blocks an update of
  `alias`, `alias_key` or `product_id` that would leave two active products
  with the same normalized alias.
- `catalog_products_reject_activation_with_shared_alias` blocks `retired`
  going from 1 to 0 when that product would then share an alias with another
  active product. The public API does not reactivate products; the trigger
  covers a direct SQL update.

A fresh database applies versions 1 through 5. A database at version 3
applies 4 and then 5. A database that already applied version 4 applies only
5, so it does not miss the new triggers. Existing stock, movement history
and product rows are left in place. A row that was already retired with
positive stock, which the old schema allowed only through direct SQL, is not
rewritten; later retirement and activation updates are rejected.

Rows created before this migration may contain only `product_id`,
`stock_unit` and `retired`. The migration leaves them in place and does not
invent a name or a category. `name` stays `NULL`. Those provisional rows are
not products of this API: `get_product` raises `UnknownProductError` with
`provisional=True`, and `list_provisional_product_ids()` lists them. The seed
refuses to overwrite one. Complete them by an explicit later decision, not by
guessing commercial attributes.

`CatalogService` is the supported writer. The schema also rejects a complete
row without a category, a stock unit other than `unit` on a complete row, and
a duplicated normalized identity. The reachable-product rule is enforced by
the service on every insert, inside the write transaction.

## Transactions

The caller owns the connection and uses it from one thread.

| Call | Transaction |
| --- | --- |
| `get_product`, `get_category`, `list_products`, `list_categories`, `list_aliases`, `list_active_product_ids`, `list_provisional_product_ids`, `read_active_catalog`, `read_snapshot` | None. They see the caller's open transaction and do not commit it. |
| `add_category`, `add_product`, `add_alias`, `retire_product` | Join the caller's transaction and do not commit it. Without one, they open `pi.storage.transaction` and commit or roll it back. |
| `load_initial_catalog` | One transaction for the whole seed. It joins a transaction the caller already opened and does not commit that transaction. |

## Seed

`load_initial_catalog(connection)` loads the closed supermarket catalog:
91 products, 8 categories (`almacen`, `bebidas`, `congelados`, `conservas`,
`higiene`, `lacteos`, `limpieza`, `snacks`) and 21 aliases. Product ids are
fixed strings in `pi.catalog.seed.SEED_PRODUCTS`. The original 26 ids and
their canonical attributes are unchanged. New ids were added beside them.
One existing product, `leche-serenisima-descremada-1000`, gained the alias
`Leche Serenísima descremada`; that is an added phrase, not a new identity.

Running the seed again does not create new ids, does not reset `retired`,
and does not write `inventory_stock` or `inventory_movements`. On a database
that already has the original 26 products, a later run inserts only the
missing categories, products and aliases. Stock quantities and movement
history already stored for those ids stay as they are.

The same product type is split by brand, variant and presentation. An
incomplete query is ambiguous on purpose. `Arroz` at `1 kg` matches Gallo,
Marolio and Dos Hermanos. `Arroz` Gallo matches `500 g` and `1 kg`.
`Gaseosa` Coca-Cola at `1.5 L` matches Original and Zero. `Gaseosa`
Coca-Cola Zero matches `1.5 L` and `2.25 L`. `ProductQuery(name="Gaseosa",
brand="Coca-Cola")` is ambiguous. A query that carries every canonical
attribute of a product identifies that product and no other. Aliases such as
`Coca Zero de litro y medio` and `Arroz Gallo de medio kilo` are stored for
the interpreter and are not used by `SqliteProductResolver`.

If an existing category, product or alias disagrees with the seed, the call
raises `CatalogConflictError` and rolls back everything that call inserted.
It does not overwrite the conflicting row.

The function does not open the database and does not apply migrations. The
caller does both. Do not run it while `voicestock-pi` has the file open.
Application startup does not call it.

```python
from pi.catalog import load_initial_catalog
from pi.storage import open_database

connection = open_database("/path/to/voicestock.sqlite3")
try:
    load_initial_catalog(connection)
finally:
    connection.close()
```

`open_database` rejects an in-memory path and a path under a temporary
directory. Tests use `pi.storage.connect` on a temporary file and
`apply_migrations` instead.

## Resolution

```python
from pi.catalog import SqliteProductResolver
from pi.operation_contract import OperationValidator, ProductQuery

validator = OperationValidator(SqliteProductResolver(connection))
resolution = SqliteProductResolver(connection).resolve(
    ProductQuery("Gaseosa", brand="Coca-Cola", variant="Zero")
)
```

The result is the existing `ProductResolution`: `identified`, `unknown`,
`ambiguous` or `insufficient_attributes`. Matching is
`pi.operation_contract.match_products`. Only active, complete products are
candidates. The resolver does not create products and does not change stock.
`OperationValidator` still decides whether the operation is acceptable.

`InMemoryProductResolver` remains the implementation used by `voicestock-pi`
today. Both implementations share `ensure_catalog_identifiable` and
`match_products`.

## Snapshot

`CatalogService.read_snapshot()` returns `CatalogSnapshot`:

| Field | Meaning |
| --- | --- |
| `version` | Snapshot schema. Currently `1`. Not the migration version. |
| `revision` | SHA-256 hex of the canonical JSON array of active products. |
| `products` | Active products ordered by `product_id`. |

Each product carries `product_id`, `name`, `brand`, `variant`,
`presentation`, `units` and `aliases`. It does not carry category, quantity,
stock, history, price or supplier data. `product_id` is there for the
Raspberry Pi to diagnose a later resolution. The language model must not
assign it. The PC still produces canonical attributes, and the Pi resolves
them.

The same effective content always produces the same revision. Adding or
retiring a product, changing a canonical attribute, or adding or removing an
alias changes the revision. Changing only the category does not. Retired
products are absent.

`GET /api/v1/catalog` on the existing FastAPI app returns that snapshot with
`Cache-Control: no-store`. Without a catalog port the route returns `503` and
`catalog_not_ready`. The handler is async so the read stays on the server
thread that owns the SQLite connection.

`voicestock-pi` does not open the database and does not pass a catalog port,
so that route answers `503` in the current process. The voice workflow keeps
validating with the JSON file from `--catalog`. Replacing that file with
`SqliteProductResolver` is a separate wiring step: it has to happen together
with the process becoming the single owner of the database, without a second
catalog source beside it.

## Inventory initialization

Another change creates the initial stock. This catalog does not insert into
`inventory_stock` and does not reset quantities. After migrations and the
seed, the stock loader can do the following. It must use the same connection
and must not run while another process owns the file.

```python
from pi.catalog import CatalogService, load_initial_catalog
from pi.inventory import InventoryService, StockStatus, create_stock_record
from pi.storage import open_database, transaction

connection = open_database("/path/to/voicestock.sqlite3")
try:
    load_initial_catalog(connection)
    # One entry for every active id that does not have stock yet.
    # Ids that already have a record are skipped; do not reset them.
    quantities = {"gaseosa-coca-cola-zero-2250": 12}
    catalog = CatalogService(connection)
    with transaction(connection):
        for product_id in catalog.list_active_product_ids():
            lookup = InventoryService(connection).get_stock(product_id)
            if lookup.status is not StockStatus.NOT_INITIALIZED:
                continue
            create_stock_record(connection, product_id, quantities[product_id])
finally:
    connection.close()
```

`list_active_product_ids()` is the list of complete, non-retired products,
ordered by id. After this seed it contains the expanded set, not the
original 26. A quantity map written for the old seed must gain an entry for
each new active id. An id that already has stock is left untouched: the loop
skips it because `get_stock` is not `not_initialized`. Do not reload the
catalog by writing those quantities again.

`find_active_products_without_stock(connection)` is the
inventory helper and has a wider meaning: it also returns provisional legacy
rows that are not retired and have no stock record. On a database that only
contains this seed, the two lists match. On a database upgraded from
migration 3, use the catalog ids as the allow-list and do not invent a
quantity for a provisional id.

Running the block again does not change a quantity that already exists,
because `create_stock_record` is called only when `get_stock` reports
`not_initialized`. `StockRecordExistsError` is the guard if a record appears
inside the same transaction. Do not `UPDATE inventory_stock` to "reload" the
seed.

`create_stock_record`, `find_active_products_without_stock`,
`InventoryService.get_stock`, `list_stock` and `apply_delta` are unchanged.
The catalog does not call them except for the quantity read inside
`retire_product`.

## Errors

All catalog failures derive from `CatalogError`.

| Error | When |
| --- | --- |
| `InvalidCatalogValueError` | Blank id or name, alias that normalizes away, stock unit other than `unit`, or an insert that is already retired |
| `UnknownProductError` | The id is missing. `provisional` is true when a legacy row has the id and no name |
| `UnknownCategoryError` | The category id does not exist |
| `DuplicateCategoryError` | The category id or the normalized name already exists |
| `DuplicateProductError` | The product id already belongs to a complete product |
| `ProvisionalProductError` | A write would have overwritten a legacy row |
| `DuplicateIdentityError` | Another product has the same normalized canonical attributes |
| `UnreachableProductError` | The active catalog would hide a product behind a more specific one |
| `AliasConflictError` | An active product already owns that normalized alias |
| `ProductHasStockError` | Retirement found a positive quantity. Carries `product_id` and `quantity` |
| `CatalogConflictError` | The seed found an existing row that does not match |

## Known limits

- `voicestock-pi` still validates operations with the JSON catalog. The
  SQLite resolver and the HTTP snapshot are ready and are not connected to
  that process.
- The PC does not download the snapshot and does not change its prompt.
- There is no API to correct a canonical attribute in place.
- A retired product is not reactivated.
- Stock is counted only in `unit`. There is no conversion and no fractional
  quantity.
- Provisional rows from migration 3 stay unresolved until a person decides
  their commercial identity.
- Aliases are not matching keys. An underspecified command can still be
  `ambiguous`; that is a query, not a broken catalog. The seed keeps several
  of those groups on purpose.
- There is no public alias editor and no reactivation. Direct SQL that would
  create either invalid state is rejected by migration 5.
- A product retired with positive stock before migration 5 is left as stored.
  The migration does not zero that quantity and does not clear `retired`.
