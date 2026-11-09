# TC-PER-001 — Stock and history persist across process and device restarts

- Status: DESIGNED
- Executions: [EX-TC-PER-001-20261108-01](../executions/EX-TC-PER-001-20261108-01.md) (**PASSED**; review NOT_REVIEWED)
- Procedure version: 1

## Objective

Show that the stock quantities and the movement history stored in the
Raspberry Pi database are the same after the owner process stops and starts
again, and after the Raspberry Pi reboots: every stock record, every
movement with its id, origin, delta and unit, UTC time, order, causation and
cause snapshot, and the answers of the history queries.

## Test level and type

Level: software component on the Raspberry Pi, on the real persistent path.

Type: functional. One process restart and one device reboot.

## Requirements and ClickUp traceability

- ClickUp: [InventoryPersistence-06](https://app.clickup.com/t/1dfdcycvurr)
  and [InventoryMovementHistory-05](https://app.clickup.com/t/1dfdcycvuu1).
- Requirement: RNF03. Stock read after a restart matches the last committed
  changes; history keeps identity, order, origin, causation and snapshot,
  and a replayed voice causation creates no duplicate.

## Source modules and documentation

- `pi.storage`, `pi.inventory`, `pi.movement_history`, `pi.catalog`.
- `scripts/integration/validate_persistence.py`.
- [Inventory stock](../../../interfaces/inventory-stock.md),
  [movement history](../../../interfaces/inventory-movement-history.md),
  [ADR-0014](../../../decisions/0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md).

## Preconditions and dependencies

- The repository revision under test is checked out on the Pi and its
  virtual environment imports it.
- `voicestock-pi` is not running: it does not own the database yet, and no
  other process may write the file during the case.
- The operator can reach the Pi again after a reboot (Tailscale over
  Ethernet, or a local console).

## Required hardware and software

- Raspberry Pi 3 of the project, booting from its USB drive.
- Project Python environment. `sudo` only for the reboot.

## Preparation

Two databases on the persistent data directory
`~/.local/share/voicestock/`:

- `<validation-db>`: a dedicated file that receives known writes. The
  history is append-only, so validation movements are never written into
  the real database.
- `<real-db>`: `voicestock.sqlite3`, initialized with
  `voicestock-pi-database init`. Only read.

## Execution

From the repository root, with `PYTHONPATH=src` and the project Python:

1. `validate_persistence.py prepare --database <validation-db> --state
   <validation-state>` writes catalog and initial stock, two voice
   operations (+5 and −3 on `gaseosa-coca-cola-zero-2250`) and one manual
   adjustment (−2 on `arroz-gallo-1000`), each with `apply_delta` and the
   movement in one transaction, and saves the observed state.
2. `validate_persistence.py record --database <real-db> --state
   <real-state>` saves the state of the real database without writing.
3. Process restart: run `check` on both databases from new processes.
4. Device restart: `sudo systemctl reboot`. When the Pi is back, record the
   new boot time and run `check` on both databases again.

`check` compares every stock record and every movement field by field, the
query results by origin, product, operation, the UTC interval between the
first and last movement, and the cursor pages of seven, then replays each
voice causation and verifies that no movement is created.

## Observations and evidence

- Boot time before and after the reboot (`uptime -s`).
- SHA-256 of both state files and of both database files.
- Output of each `check`: counts and PASS or FAIL with the differing keys.

## Pass criteria

1. Every `check` prints PASS.
2. The boot time changed between step 3 and step 4.
3. The real database was not written by the case (same SHA-256 before and
   after, apart from a reboot).
