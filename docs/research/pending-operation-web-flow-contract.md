# Pending operation web flow contract

Integration record for task **PendingOperationWeb-02**: the application
boundary that the future web adapter will call, and that `PendingOperationFlow`
will own.

**Status:** contract recorded. `PendingOperationFlow` is not implemented.
This document is the hand-off for that feature. It is not the design of the
FSM. When Flow exists, this note can be replaced or absorbed by the interface
document and by Flow's own design. Until then, it is the source of truth for
the boundary below.

The HTTP stack and the single-process topology are already decided in
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md) and
[the web stack research](pending-operation-web-stack.md). This task does not
add FastAPI, routes, or HTTP status codes.

## Ownership

`PendingOperationFlow` will be the owner of `PendingOperation` and of the FSM,
including the transition into `WAIT_CONFIRMATION` and any later transition
out of it. Those states are not defined here.

The web adapter, when it exists, calls application ports. It does not own the
pending operation, does not clear it, and does not modify the FSM.

```text
pi.web                             HTTP adapter
    |
    v
PendingOperationQueryPort
PendingOperationResolutionPort
    |
    v
PendingOperationGateway            policy implemented now
    |
    +--> OperationExecutor         provisional now, inventory later
    |
    v
PendingOperationSlot               implemented by PendingOperationFlow
    |
    v
FSM / PendingOperation             future owner
```

Flow should compose `PendingOperationGateway` and pass its slot and the
executor in. It should not reimplement confirm and cancel in the HTTP layer,
and it should not keep a second copy of the resolution rules.

`pi.web` already accepts the two ports and stores them. No route calls them
yet. The current page is a placeholder. The API is `PendingOperationWeb-04`.

The code lives in `pi.pending_operation`, because both the future UI and the
orchestrator run on the Raspberry Pi. It is not in `shared`: the PC does not
exchange this contract.

## Query

`PendingOperationQueryPort.get_current()` returns a `PendingOperationView`,
or `None` when nothing is pending.

`PendingOperationView` is a read snapshot. Callers outside the owner,
including the future page, must not receive the domain object Flow will
define. The gateway copies the public fields, so an internal subclass cannot
leak extra attributes through the port.

| Field | Role |
| --- | --- |
| `operation_id` | Identity of this pending operation. Non-blank string. Required on every confirm and cancel. |
| `recognized_text` | Text that produced the operation. Display only for this contract. |
| `product` | Product label to show. Not a product-catalog key defined here. |
| `operation` | Opaque label of the requested inventory action. Not an FSM state. The allowed vocabulary belongs to the future inventory contract. |
| `quantity` | Integer amount to show. |
| `unit` | Unit label to show. |
| `confirmation_message` | Message the operator confirms. |

## Resolution

`PendingOperationResolutionPort` has two methods. There is no
`resolve(operation_id, action)` and no `confirm_current()`.

```text
confirm(operation_id) -> ResolutionResult
cancel(operation_id) -> ResolutionResult
```

A missing or blank `operation_id` raises `ValueError`. It is not a resolution
status.

`ResolutionResult` carries:

| Field | When it is set |
| --- | --- |
| `status` | Always. |
| `operation_id` | The operation the result is about. Empty for `no_pending`. For `stale_operation` and `execution_failed`, this is the requested id, not the id that remains current. |
| `resolved_action` | `confirm` or `cancel` when that action stands for the id: just applied, already applied, or the action that won a conflict. Empty when nothing was resolved. |

Statuses:

| Status | Meaning |
| --- | --- |
| `success` | The requested action was applied to that id. |
| `no_pending` | Nothing is pending, and this id is not the remembered resolution. |
| `stale_operation` | Another operation is current. The request names the stale id. The current operation stays as it is. |
| `already_resolved` | This id was already resolved with the same action. The executor is not called again. |
| `conflict` | This id was already resolved with the opposite action. The new action is not applied. `resolved_action` is the action that already won. |
| `execution_failed` | Confirm ran the executor and it failed. The pending operation stays. |

Mapping these statuses to HTTP belongs to `PendingOperationWeb-04`.

## Confirm and cancel

Confirm is not "delete the pending operation".

```text
confirm(operation_id)
        |
        v
still the current id?
        |
        v
executor.execute(snapshot)
        |
        v
success?
   |            |
  yes           no
   |            |
   v            v
clear pending   keep pending
remember         do not remember
```

The slot is cleared only after a successful execution. A failed result or an
exception from the executor becomes `execution_failed` and leaves the pending
operation in place, so the operator can retry. The failure path must not be
"clear, then execute".

Cancel does not call the executor and does not modify inventory.

```text
cancel(operation_id)
        |
        v
still the current id?
        |
        v
clear pending
remember cancel
```

Which FSM state follows a cancel or a successful confirm is Flow's decision.
This contract only requires that the slot no longer exposes that operation
after a successful resolution, and that a failed confirm still exposes it.

## Stale ids

```text
UI shows operation AAA
the current operation becomes BBB
UI sends confirm(AAA)
        |
        v
stale_operation
BBB stays pending
the executor is not called
```

The same check applies to cancel.

## Retries and conflicts

The gateway keeps one in-process record, `last_resolution`, with the
`operation_id` and the action of the immediately previous successful
resolution. It is checked before the slot.

```text
confirm(AAA) -> success
the response is lost
confirm(AAA) -> already_resolved
the executor does not run again
```

```text
AAA was confirmed
cancel(AAA) -> conflict
```

The opposite order also returns `conflict`. A conflict does not undo the
action that won and does not execute inventory work.

Only that one previous resolution is remembered. After a later operation is
resolved, the older id is forgotten. Repeating it then follows the normal
empty-slot rule (`no_pending` if nothing is pending).

This memory is not:

- a durable history;
- durable idempotency;
- persistence;
- `OperationHistory`.

It lives on the gateway instance. A new process, or a new gateway, does not
have it. That is acceptable for this increment. With the provisional executor
nothing was written to inventory, so losing the record does not repeat a real
stock change. When the real executor exists, a retry after a restart is not
covered by this record. Durable idempotency has to be decided with that
executor, not added here.

Flow must not reuse an `operation_id` while it is still the remembered one.
A reused id would be treated as already resolved and would not execute.

## Concurrency

FastAPI may deliver overlapping requests later. The same rule has to hold for
any other adapter. The lock is therefore on the gateway, not in a route.

There is one lock, not a lock per operation. VoiceStock has a single pending
operation, so one lock is enough.

The critical section is the whole resolution:

```text
remembered id?
        |
        v
current pending operation
        |
        v
operation_id still matches?
        |
        v
execute (confirm only) or skip execution (cancel)
        |
        v
clear and remember, or keep the pending operation
```

`get_current` uses the same lock so a reader does not observe a resolution
halfway through.

Overlapping `confirm` calls for the same id produce one `success` and one
`already_resolved`. The executor runs once. Overlapping `confirm` and
`cancel` produce one `success` and one `conflict`. They cannot leave the same
id both confirmed and cancelled.

The executor must not call back into the gateway. The lock is held across
`execute`, and a re-entrant call would deadlock.

## Executor

`OperationExecutor.execute(view)` performs the inventory effect. It does not
clear the pending operation.

`ProvisionalOperationExecutor` is the October implementation. It returns
success and does not modify inventory, write history, or persist anything.
Tests and the current gateway can confirm an operation without those
features.

`OperationConfirmationExecution` replaces that object with an inventory
executor. The web adapter and the gateway keep depending on
`OperationExecutor`. No HTTP change is required for the swap.

## What Flow still has to decide

- How a pending operation is created, and the real domain type behind the
  view.
- How `operation_id` values are generated, provided they are unique while
  remembered.
- The FSM states and the transitions into and out of confirmation. This
  contract does not add states.
- When the slot starts and stops exposing the current view.
- The product, unit, and operation vocabulary, together with the inventory
  feature that will own them.
- The real executor, including what a failed execution means for stock.
- Whether a successful execution that then fails to clear the slot needs a
  recovery path. Today the gateway reports `stale_operation` and does not
  remember a success if `clear` returns false.
- Durable idempotency after process restart, if a later executor must not
  apply the same operation twice.
- HTTP status codes for each `ResolutionResult`.

## Out of scope

This task does not implement FastAPI, HTML, inventory, history, resolution
persistence, the FSM, `PendingOperationFlow`, or `OperationConfirmationExecution`.
The slot has no production class on purpose. Test doubles live under
`tests/pi/pending_operation/` and are not a second pending-operation model.
