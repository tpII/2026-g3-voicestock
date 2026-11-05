# Inventory movement history interface

## Purpose

`pi.movement_history` keeps a durable, append-only record of every stock
change on the Raspberry Pi, so the inventory is a history that can be
reconstructed and not only a current balance. Each movement answers what
changed, by how much, when, on which product and why.

It lives in the same SQLite file as the catalog and the stock
([ADR-0014](../decisions/0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md)).
It does not change stock ([inventory stock](inventory-stock.md)), decide a
delta, confirm or cancel operations (OperationConfirmationExecution) or show
anything (InventoryWebApp).

```text
OperationConfirmationExecution ── record ─────────┐
manual adjustments, seed ──────── record ─────────┼─► inventory_movements
InventoryWebApp, E2E validation ─ find_movements ─┘   (append-only)
```

## Movement

| Field | Meaning |
|---|---|
| `movement_id` | Unique text id (UUID4), assigned when recording |
| `sequence` | Integer assigned by the database; the **total order** of the history |
| `product_id`, `unit` | Catalog product and its stock unit |
| `delta` | Exact, non-zero, signed integer |
| `quantity_before`, `quantity_after` | Balance around the change; `after = before + delta`, both zero or more |
| `origin` | `voice_operation`, `manual_adjustment` or `initialization` |
| `operation_id` | Id of the pending voice operation; required for voice, absent otherwise |
| `causation_key` | Idempotency key of the cause, see below |
| `recorded_at` | UTC time from the Pi clock, microsecond precision |
| `cause` | Non-empty JSON snapshot of why it happened, frozen when recorded |

The cause needs `recognized_text` for a voice movement and `reason` for the
other origins; other plain JSON keys may be added. With the balance and the
cause, a movement explains itself without reading the current stock or the
pending operation, which no longer exists after confirmation.

**Order.** The Raspberry Pi 3 has no real-time clock: until it reaches
network time, `recorded_at` can be wrong or go backwards. The order of the
history is therefore always `sequence`, never `recorded_at`.

**Append-only.** The database rejects every update and delete of a movement.
A wrong movement is corrected with a new movement, never by editing history.

### Associations and idempotency

| Origin | `operation_id` | `causation_key` |
|---|---|---|
| `voice_operation` | `PendingOperation.operation_id` | Always equal to `operation_id` |
| `manual_adjustment` | Absent | Optional key chosen by the caller |
| `initialization` | Absent | Optional key chosen by the caller |

`(origin, causation_key)` is unique, so one voice operation can never produce
two movements, and a manual or initialization cause with a key is recorded
once. Movements without a key are never deduplicated. No `operation_id` is
invented for movements that do not come from voice.

The product must exist in the catalog and the unit must be its stock unit.
While a product has movements, it cannot be deleted and its stock unit cannot
change.

## Recording

`SQLiteMovementRecorder(connection)` implements `MovementRecorder`.

`record(...)` takes `product_id`, `delta`, `unit`, `quantity_before`,
`quantity_after`, `origin`, `cause` and, when they apply, `operation_id` and
`causation_key`. It assigns `movement_id` and `recorded_at` and returns
`RecordResult(movement, created)`.

- It must run **inside a transaction already open on the caller's
  connection** (`NoUnitOfWorkError` otherwise) and never commits. The movement
  is committed or rolled back with the stock change it describes.
- Replaying a cause with the same product, delta, unit and operation returns
  the existing movement with `created=False`. The balance and cause may
  differ, because stock moved since. Reusing the key for a different change
  raises `CausationConflictError`.
- An incomplete or inconsistent movement, or a database integrity failure,
  raises `InvalidMovementError` and stores nothing.

A confirmed change follows this order, in one unit of work:

```python
from pi.inventory import InventoryService
from pi.movement_history import SQLiteMovementRecorder
from pi.storage import transaction

stock = InventoryService(connection)
recorder = SQLiteMovementRecorder(connection)

with transaction(connection):
    if recorder.find_by_causation("voice_operation", operation_id) is None:
        level = stock.apply_delta(product_id, delta, unit)
        recorder.record(
            product_id=product_id,
            delta=delta,
            unit=unit,
            quantity_before=level.quantity - delta,
            quantity_after=level.quantity,
            origin="voice_operation",
            operation_id=operation_id,
            cause={"recognized_text": recognized_text},
        )
```

Checking the cause first is what makes a repeated confirmation change stock
once: `record` deduplicates the movement, but only the caller can skip the
delta.

## Querying

`SQLiteMovementHistory(connection)` implements `MovementHistoryReader`.
`find_movements(MovementQuery(...))` returns a `MovementPage` with
`movements` and `next_cursor`.

| `MovementQuery` field | Meaning |
|---|---|
| `product_id`, `operation_id`, `origin` | Exact match. Movements without an operation never match `operation_id`; select them by `origin` |
| `recorded_from`, `recorded_to` | Half-open interval `[recorded_from, recorded_to)` on `recorded_at`; timezone-aware datetimes, any zone; `from` must be before `to` |
| `newest_first` | `False` (default): ascending `sequence`; `True`: descending |
| `limit` | 1 to 200, default 50 |
| `cursor` | `next_cursor` of the previous page; opaque |

- Filters combine with AND, and results are always ordered by `sequence`.
  The same query over the same history returns the same page.
- Pagination never uses an offset: movements appended while a client pages
  do not shift or repeat pages. `next_cursor` is `None` on the last page.
- The time interval filters by the Pi's clock; within it, order is still
  `sequence`.
- An invalid filter, limit or cursor raises `InvalidMovementQueryError`
  (not a `sqlite3.Error`) before any read. No match is an empty page.
- Queries read only the history: they never compute or correct stock, and
  they do not open or commit a transaction.

```python
from pi.movement_history import MovementQuery, SQLiteMovementHistory

history = SQLiteMovementHistory(connection)
page = history.find_movements(MovementQuery(product_id="coca-cola-zero-2l"))
while page.next_cursor:
    page = history.find_movements(
        MovementQuery(product_id="coca-cola-zero-2l", cursor=page.next_cursor)
    )
```

## Limits

- **Inventory.** Stock changes only through `pi.inventory`. Recording a
  movement never changes stock, and queries never derive stock from the
  history.
- **Confirmation.** OperationConfirmationExecution maps an operation to a
  delta, opens the unit of work, applies it and records the movement. The
  history neither confirms nor clears the pending operation.
- **Web.** InventoryWebApp reads through `MovementHistoryReader` and never
  queries the tables directly. Screens, filters and HTTP endpoints are its
  own.
- An architecture test keeps `pi.movement_history` free of HTTP, the
  operation cycle and the interpretation contract.
