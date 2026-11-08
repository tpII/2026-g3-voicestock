# ADR-0014: Keep catalog, stock and history in one SQLite database on the Pi

## Status

Accepted — 4 November 2026. Implemented by InventoryPersistence-01..03
(#38, #40, #41) and InventoryMovementHistory-01 (#43). Product catalog
identity and lifecycle extend this database in
[ADR-0015](0015-persist-the-product-catalog-in-the-pi-database.md).

## Context

The November MVP adds three persistent concepts on the Raspberry Pi: the
closed product catalog (ProductCatalog), the current stock
(InventoryPersistence) and the movement history (InventoryMovementHistory).
A confirmed voice operation must change stock and record its movement
together: a change without a movement, or a movement without a change,
breaks the trace.

The constraints are:

- one Raspberry Pi 3 with a USB drive, no database server and no network
  dependency in operation mode;
- the operation workflow and the web page run in one process,
  `voicestock-pi` ([ADR-0008](0008-use-a-single-raspberry-pi-operation-workflow.md),
  [ADR-0009](0009-use-in-process-fastapi-and-static-web-ui.md));
- the PC and the browser are remote consumers and must not depend on the
  storage format;
- `/tmp` on the Pi is `tmpfs`, and the Pi has no real-time clock, so its time
  can be wrong until it reaches network time;
- ProductCatalog had not started when stock was built, but stock needs a
  product to reference.

## Decision

### One file, one owner

Catalog, stock and history live in **one SQLite file** on the Raspberry Pi:
`$VOICESTOCK_DATABASE` when set, otherwise
`$XDG_DATA_HOME/voicestock/voicestock.sqlite3` or
`~/.local/share/voicestock/voicestock.sqlite3`. Paths in memory or under
`/tmp`, `/var/tmp`, `/dev/shm`, `/run` or the system temporary directory are
rejected, also when a symbolic link leads there.

Only `voicestock-pi` opens the file. The PC, the browser and any other
consumer reach the data through that process and never open the file.

### One migration order

`pi.storage.MIGRATIONS` is the only schema history. Each migration is applied
once, recorded in `schema_migrations` with its version and name, and never
edited after it reaches `develop`: a schema change is a new migration at the
end. Applying migrations is repeatable and atomic, and a database whose
history does not match the code is refused.

| Version | Name | Feature |
|---|---|---|
| 1 | `create_catalog_products` | Minimal catalog for stock to reference |
| 2 | `create_inventory_stock` | InventoryPersistence |
| 3 | `create_inventory_movements` | InventoryMovementHistory |

Migration 1 holds only what stock needs: the stable `product_id`, the stock
unit and a `retired` flag. ProductCatalog-02 adds the identity attributes
with new migrations on the same table instead of creating another database.

### Connections and units of work

Connections enforce foreign keys and use the write-ahead log with
`synchronous = FULL`. They run in autocommit mode: a change that spans stock
and history runs inside one `pi.storage.transaction`, opened by the caller,
and the modules that join it never commit. The transaction takes the write
lock when it starts, so two writers never interleave.

### Integrity in the schema

The invariants hold for every writer, not only for the Python services:
foreign keys to the catalog, exact non-negative integer quantities, the unit
tied to the product's stock unit, records that are never deleted and an
append-only history.

## Alternatives considered

- **One file per concept.** SQLite cannot commit one transaction across
  files without attaching them, and a stock change and its movement would
  then commit separately.
- **A database server (PostgreSQL, MariaDB) on the Pi.** It adds a service
  to install and supervise on 1 GB of RAM for a single writer process.
- **Keep stock in memory or in a JSON file.** It does not survive restarts
  reliably and gives no atomic update.
- **Wait for ProductCatalog before building stock.** It would block two
  features; the minimal table lets ProductCatalog extend it later.

## Consequences

- A stock change and its movement are committed or rolled back together.
- Concurrency is limited to one writer at a time, which fits one operator
  and one process.
- ProductCatalog must add migrations after the existing ones; it cannot
  change migrations 1 to 3.
- Nobody may copy the file while `voicestock-pi` writes it; a backup uses
  SQLite's backup API or stops the process first.
- Time stored in the history comes from the Pi clock; the order of the
  history comes from a sequence instead.
