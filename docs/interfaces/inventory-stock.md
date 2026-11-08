# Inventory stock interface

## Purpose

`pi.inventory` keeps the current stock of every catalog product in the
Raspberry Pi database and is the only way the rest of the Pi reads or changes
it. It answers "how many units of this product are there now?" and applies a
signed change that someone else already decided on.

It does not map an operation to a delta, confirm or cancel operations,
record movements or expose HTTP. Those belong to OperationConfirmationExecution,
InventoryMovementHistory and InventoryWebApp.
Why catalog, stock and history share one SQLite file is recorded in
[ADR-0014](../decisions/0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md).

```text
OperationConfirmationExecution ─┐
InventoryWebApp ────────────────┼─► StockReader / StockWriter ─► inventory_stock
tests, seed ────────────────────┘        (InventoryService)        catalog_products
```

| Planned consumer | Uses |
|---|---|
| OperationConfirmationExecution | `get_stock` to evaluate, `apply_delta` to execute a confirmed operation |
| InventoryWebApp | `get_stock` and `list_stock` to show inventory |
| Initial stock load (`load_initial_stock`) | `create_stock_record`, `get_stock` and the movement recorder |

## Model

A **stock record** is the current quantity of one catalog product.

| Field | Meaning |
|---|---|
| `product_id` | Stable catalog key ([ADR-0006](../decisions/0006-identify-products-by-unique-attribute-match.md)); one record per product at most |
| `quantity` | Exact integer, zero or more |
| `unit` | The product's stock unit in the catalog; no other unit can be stored |

Invariants, enforced by the schema for every writer:

- a record references an existing catalog product, in that product's stock
  unit;
- a product has at most one record;
- the quantity is an integer (no `float`, no rounding) and never negative;
- a record never moves to another product or unit and is never deleted;
- a retired product keeps its record, gets no new one, and cannot be
  deleted while it has stock.

**A missing record is not zero.** It means the product's stock was never
initialized. Records are created explicitly with their initial quantity, never
by default, so a seed can create the missing ones without resetting the
others. Every active product must end up with a record;
`find_active_products_without_stock` lists the ones that break this.

## Reading stock

```python
from pi.inventory import InventoryService, StockStatus

service = InventoryService(connection)
lookup = service.get_stock("coca-cola-zero-2l")
if lookup.status is StockStatus.FOUND:
    print(lookup.level.quantity, lookup.level.unit)
```

| Call | Returns |
|---|---|
| `get_stock(product_id)` | `StockLookup` with status `found` and a `StockLevel`, `unknown_product`, or `not_initialized` |
| `list_stock(include_retired=False)` | Records of active products, ordered by `product_id`; `include_retired=True` adds retired ones |

`StockLevel` has `product_id`, `quantity`, `unit` and `retired`. Each read is
one query on the caller's connection and never opens or commits a transaction,
so inside the caller's unit of work it sees that unit's uncommitted changes.

## Changing stock

```python
level = service.apply_delta("coca-cola-zero-2l", -2, "unit")
```

`apply_delta(product_id, delta, unit)` adds `delta` to the stock of an active
product and returns the new `StockLevel`. It runs as one conditional `UPDATE`
that only applies when the product is active, `unit` is its stock unit and the
result is not negative. No read-compute-write happens, so concurrent changes
can neither lose an update nor go below zero.

When the change does not apply, nothing changes and the error says why. All
errors derive from `StockRecordError`.

| Error | When |
|---|---|
| `InvalidDeltaError` | `delta` is zero or not an `int` (floats, `Decimal`, strings and booleans are rejected, not converted) |
| `UnknownProductError` | the product is not in the catalog |
| `StockNotInitializedError` | the product has no record; none is created |
| `RetiredProductError` | the product is retired |
| `IncompatibleUnitError` | `unit` is not the product's stock unit; nothing is converted |
| `InsufficientStockError` | the result would be negative; carries `available` and `delta` |

Creating a record (`create_stock_record(connection, product_id, quantity)`)
raises `UnknownProductError`, `RetiredProductError`, `StockRecordExistsError`
or `InvalidQuantityError`.

## Units of work

The connection belongs to the caller and is used by one thread.

- **Inside the caller's transaction.** When a transaction is already open on
  the connection, `apply_delta` joins it and does not commit. The caller opens
  it with `pi.storage.transaction`, applies the delta, records the movement
  with the same connection and lets the transaction commit or roll back both.
  A rejection inside it changes nothing and leaves the decision to the caller.
- **On its own.** Without an open transaction, `apply_delta` runs and commits
  its own transaction before returning.

The inventory layer never owns the confirmation transaction: it does not
decide when stock and history are committed together.

```python
from pi.storage import transaction

with transaction(connection):
    level = service.apply_delta(product_id, delta, unit)
    recorder.record(...)  # same connection, same unit of work
```

## Database file and initial stock

The owner process opens the file with `pi.storage.open_database`, which checks
the path, connects and applies the migrations. The default location is
`~/.local/share/voicestock/voicestock.sqlite3`; `VOICESTOCK_DATABASE`
overrides it. Temporary and in-memory paths are rejected
([ADR-0014](../decisions/0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md)).

### Preparing the database

`voicestock-pi-database init` prepares the database on the Raspberry Pi. It
opens the file on its persistent path, applies the migrations, loads the closed
catalog (`pi.catalog.load_initial_catalog`) and then the initial stock
(`pi.inventory.load_initial_stock`). `voicestock-pi-database status` reports
the schema version, active products, stock records and units, movements and
active products without stock, without changing anything. Both accept
`--database PATH`. Stop `voicestock-pi` before `init`.

```bash
voicestock-pi-database init
voicestock-pi-database status
```

### Initial stock

`pi.inventory.INITIAL_STOCK` gives one exact quantity to each of the 91
products of the closed catalog. A test checks that its keys are exactly the
catalog seed. Fast movers get more units and bulky or expensive products
fewer; `yogur-serenisima-natural-120` starts at zero and a few products start
at two to five units, so a removal can be rejected for lack of stock during a
demonstration.

`load_initial_stock(connection)`:

- refuses to write anything when the table and the active catalog name
  different products (`InitialStockMismatchError`, with `missing` and
  `unknown`) or a quantity is not an exact non-negative integer;
- creates a record only for active products whose stock is `not_initialized`,
  so running it again never resets a quantity that operations already
  changed; retired products are left out;
- records one `initialization` movement for each record created with a
  positive quantity, with causation key `initial-stock:<product_id>`, so the
  history shows where the first units came from;
- runs everything in one unit of work: it joins the caller's transaction or
  opens its own, and a failure leaves neither stock nor movements behind;
- returns `InitialStockResult(created, skipped)`.

There is no reset. Records are never deleted and the history is append-only,
so starting over means deleting the database file on a development machine,
explicitly and with `voicestock-pi` stopped. Never do it on the Raspberry Pi
that holds real stock.

## Rules for maintainers

- SQLite is the only source of truth. Do not keep a cache of stock in memory
  that can diverge from the database; read it again instead.
- Change quantities only with `apply_delta` or an equally conditional
  `UPDATE`, never by reading a value and writing a computed one.
- Do not open the database file from another process or from the PC.
- Do not edit a migration after it reaches `develop`; add a new one.
- Keep `pi.inventory` free of HTTP, the operation cycle and the interpretation
  contract; an architecture test enforces it.
