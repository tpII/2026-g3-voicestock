# Pending operation web flow contract

Hand-off between the web adapter and the future `PendingOperationFlow`.

**Status:** the ports, the gateway, the provisional executor, the HTTP API,
and the operator page exist. `PendingOperationFlow` does not. This document
is the source of truth for that boundary. It is not the FSM design. When Flow
exists, its own design can absorb this note.

The stable stack decision is
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).
The comparison that led there is the
[web stack research](pending-operation-web-stack.md). The HTTP map is the
[pending-operation web API](../interfaces/pending-operation-web-api.md). The
page behavior is the
[pending operation page](../interfaces/pending-operation-web-ui.md). How to
install and open the server is the
[web setup guide](../setup/pi-web.md).

## Current shape

```text
                    PC browser
                        |
                     Ethernet
                        |
                 HTML / CSS / JS
                        |
                   HTTP API v1
                        |
                     FastAPI                 adapter only
                        |
          +-------------+-------------+
          |                           |
   QueryPort                  ResolutionPort
          |                           |
          +-------------+-------------+
                        |
             PendingOperationGateway     policy implemented now
               |                  |
               v                  v
        OperationExecutor    PendingOperationSlot
        provisional now      protocol only
                                    |
                                    v
                    PendingOperationFlow / FSM
                    not implemented yet
```

Today:

- `PendingOperationFlow` does not exist, and there is no production slot.
- `voicestock-pi-web` can start without the ports. `/health` still answers.
  The pending-operation routes then return `application_not_ready`.
- The production shape is still one Python process. The standalone command
  is for development and validation. It is not a second service.
- FastAPI calls the ports. It does not own the pending operation.

## Ownership

`PendingOperationFlow` will own:

- `PendingOperation`;
- the FSM;
- creation of the pending operation;
- the transition into `WAIT_CONFIRMATION`;
- the transition out of confirmation;
- the transition after cancellation;
- the real integration with the Pi runtime.

Those states are not defined here. The web only consumes
`PendingOperationQueryPort` and `PendingOperationResolutionPort`. FastAPI
does not own the pending operation, does not clear it, and does not modify
the FSM. The shape is the diagram above.

Flow should compose `PendingOperationGateway` and pass its slot and the
executor in. It should not reimplement confirm and cancel in the HTTP layer,
and it should not keep a second copy of the resolution rules.

`pi.web` stores the two ports and, when they are present, the versioned
routes call them. Without ports the API returns `application_not_ready` and
`/health` stays a liveness check. What `/health` does and does not mean is
the [web setup guide](../setup/pi-web.md).

The code lives in `pi.pending_operation`, because the page and the
orchestrator run on the Raspberry Pi. It is not in `shared`: the PC does not
exchange this contract.

## Query

`PendingOperationQueryPort.get_current()` returns a `PendingOperationView`,
or `None` when nothing is pending.

`PendingOperationView` is a read snapshot. Callers outside the owner,
including the page, must not receive the domain object Flow will define. The
gateway copies the public fields, so an internal subclass cannot leak extra
attributes through the port.

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

HTTP status codes for these results are the
[pending-operation web API](../interfaces/pending-operation-web-api.md).
There is no `confirm_current()` and no "confirm whatever is current". The id
is mandatory so a late click cannot resolve an operation the page is no
longer showing.

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
operation in place, so the operator can retry. Clearing the pending operation
before `execute` is not the current rule.

Cancel does not call the executor and does not modify inventory. In this
increment it only resolves that id as cancelled. The FSM transition that
follows still belongs to `PendingOperationFlow`.

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
executor. `PendingOperationWeb` does not provide it.

Flow must not reuse an `operation_id` while it is still the remembered one.
A reused id would be treated as already resolved and would not execute.

## Concurrency

FastAPI can deliver overlapping requests. The same rule has to hold for any
other adapter. The lock is therefore on the gateway, not in a route.

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
`OperationExecutor`. No HTTP change is required for the swap. Until that
replacement, confirming an operation does not modify real inventory.

## Slot

`PendingOperationSlot` is a protocol. This package has no production slot,
because the slot belongs to `PendingOperationFlow`.

`current()` exposes the snapshot the gateway may show. `clear(operation_id)`
returns whether that id was still current. The gateway treats `False` as
`stale_operation` and does not remember a success.

When Flow implements the slot, `clear` will probably have to perform the FSM
transition out of confirmation, not only `pending = None`. That decision is
not taken here.

## Execution succeeds, resolution fails

```text
real inventory execution succeeds
        |
        v
slot or FSM resolution fails
```

Today, if `execute` reports success and `clear` then returns false, the
gateway answers `stale_operation` and does not store `last_resolution`. A
later retry of the same id can call the executor again.

With `ProvisionalOperationExecutor` that retry has no inventory effect. Before
`OperationConfirmationExecution` is connected, the inventory feature has to
decide idempotency, the transaction boundary, or a recovery path for "the
stock changed, but the pending operation was not resolved". `PendingOperationWeb`
does not decide that. This note only keeps the risk and names its owner.

## Still open

- Integrating this gateway into the real `PendingOperationFlow`.
- The final lifecycle of the web app inside the single Pi process.
  `voicestock-pi-web` is not that lifecycle.
- The FSM after a successful confirm and after a cancel.
- How a pending operation is created, and the domain type behind the view.
- How `operation_id` values are generated, provided they stay unique while
  remembered.
- When the slot starts and stops exposing the current view, and what `clear`
  means as an FSM transition.
- The product, unit, and operation vocabulary, with the inventory feature.
- The real inventory executor, and what a failed execution means for stock.
- Durable idempotency after a process restart.
- Recovery when execution succeeds and slot or FSM resolution then fails.
- Persistence and operation history.
- Authentication or TLS, if a later increment requires them. They are not
  part of this web increment. See
  [ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).

## Out of scope for the original contract task

PendingOperationWeb-02 did not implement FastAPI, HTML, inventory, history,
resolution persistence, the FSM, `PendingOperationFlow`, or
`OperationConfirmationExecution`. The HTTP API and the page now exist; their
contracts are the interface documents linked above. The slot still has no
production class. Test doubles live under `tests/pi/pending_operation/` and
are not a second pending-operation model.
