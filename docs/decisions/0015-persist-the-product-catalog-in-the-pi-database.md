# ADR-0015: Persist product identity, categories and aliases in the Pi database

## Status

Accepted — 8 November 2026. Implemented in `pi.catalog` on top of the
database from
[ADR-0014](0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md).
Product identity remains
[ADR-0006](0006-identify-products-by-unique-attribute-match.md).

## Context

Stock and movement history already reference `catalog_products` through
`product_id` and `stock_unit`. That table was only the key, the unit and a
retirement flag, because the catalog feature had not started. The voice
validator still loads a JSON file into `InMemoryProductResolver`.

The catalog now has to be persistent, closed and safe to seed before another
change initializes stock. It also has to keep every database that already
passed migrations 1 to 3, including rows that have no commercial name.

## Decision

### One table, extended

`catalog_products` stays the product table. Migration 4 adds `name`, `brand`,
`variant`, `presentation`, `category_id` and the normalized keys used to
enforce identity. Migrations 1 to 3 are not edited. Categories and aliases
are new tables in the same file. There is no second database and no ORM.

A row whose `name` is still `NULL` is provisional. The migration does not
invent attributes for it and does not delete it. The catalog API does not
treat it as a product. `list_provisional_product_ids()` exposes it so it can
be reconciled explicitly.

### Identity

`product_id` is the only identifier. It is opaque, stable and never reused.
The canonical attributes remain `name`, `brand`, `variant` and
`presentation`, normalized by the existing `normalize_attribute`. Category
and aliases are not part of that identity.

Two complete products cannot share a normalized identity, whether or not they
are retired. Every active product must be identifiable by a query that
carries all of its own canonical attributes. The check is
`ensure_catalog_identifiable`, the same function `InMemoryProductResolver`
uses. The service runs it inside the insert transaction, so a rejected
product is not committed.

The public API does not update canonical attributes. A different package is a
new product. In-place corrections are left for a later, explicit operation.

### Categories and aliases

A category has a stable id and a name that is unique after normalization.
Each complete product has one category, enforced by a foreign key.

Aliases are stored as rows. They give the interpreter extra phrases. They are
excluded from `SqliteProductResolver` and from ADR-0006 matching. The same
normalized alias cannot be shared by two active products. Retired aliases
stay on the product and stay out of the active snapshot.

### Units and retirement

Seeded products are counted as `unit`. Presentation is the package, not the
stock unit. `CatalogProduct.units` stays a tuple of that stock unit.

Retirement is logical. It is allowed only when stock is absent or zero, and
the check shares the write transaction with the flag update. Stock rows and
movement rows are kept. Inventory continues to reject changes to a retired
product. Migration 5 repeats that rule in the schema, so a direct
`UPDATE retired = 1` fails while `inventory_stock.quantity > 0`. The same
migration rejects an alias update, an alias ownership change, and a return
to active that would give two active products the same normalized alias.
There is still no public editor for aliases and no reactivation.

### Seed and snapshot

`load_initial_catalog` inserts a fixed set of 91 products, 8 categories and
21 aliases. Ids are constants. The original 26 ids and their canonical
attributes stay as first published on this branch; the later products were
added beside them. A second run does not mint ids, does not clear `retired`,
and does not write stock or history. A database that already holds the
original seed receives only the missing categories, products and aliases. A
conflicting existing row aborts the seed.

The set is large enough to exercise brand, variant, presentation and
legitimate ambiguity. `Gaseosa` plus `Coca-Cola`, without variant or
presentation, matches more than one product. A query with every canonical
attribute of a product identifies that product. Aliases stay out of matching.

Migration 4 is left as published. Databases that already applied it receive
migration 5 and do not need a reset. Migrations 1 to 3 stay untouched.

The snapshot revision is the SHA-256 of the canonical JSON of active
products, aliases included and category excluded. It is not the migration
version. `GET /api/v1/catalog` returns it from the existing FastAPI app when
a catalog port is supplied.

### Runtime

`voicestock-pi` keeps validating with the JSON catalog from `--catalog`.
`SqliteProductResolver` implements the same port and can replace the
in-memory resolver when the process opens this database as its only catalog.
Doing that in this change would leave the voice workflow with two catalog
sources. The PC is not changed and does not read the snapshot yet.

## Alternatives considered

- **Fill provisional rows with placeholder names.** It would publish products
  nobody defined and could collide with the seed. Left as `NULL` instead.
- **Delete provisional rows.** Stock or history may already reference them.
- **A product administration API.** The MVP needs a seed, reads and
  retirement, not unrestricted edits.
- **Match aliases in the resolver.** ADR-0006 forbids a second matching
  algorithm. Aliases stay on the interpretation side of the boundary.
- **Put the category in the snapshot revision.** Changing category would look
  like a new product to the interpreter. Category is classification only.
- **Open the database inside `voicestock-pi` now.** The process would validate
  against SQLite while `--catalog` and the PC prompt still describe the JSON
  file. Deferred until one source replaces the other.

## Consequences

- Inventory initialization can list active ids without reading the catalog
  schema. It must ignore provisional rows or it will try to stock a product
  that has no commercial identity. `find_active_products_without_stock` still
  returns those rows; that behavior is unchanged on purpose.
- A catalog write cannot commit an active catalog that hides a product.
- Retirement cannot pass a positive stock quantity by checking and updating
  in two transactions, or by writing `retired` outside `CatalogService`.
- Inventory initialization must enumerate `list_active_product_ids()` after
  the expanded seed and must supply a quantity only for ids that are still
  `not_initialized`. Previously stored quantities stay.
- The HTTP catalog route answers `503` until the runtime passes a port.
- The PC prompt can drift from the database until a later change delivers
  the snapshot to the interpreter.
