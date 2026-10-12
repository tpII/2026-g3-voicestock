# Pending operation web API

## Purpose

The browser on the PC reads and resolves the current pending operation
through this HTTP API. The server runs on the Raspberry Pi.

FastAPI is an adapter. A route calls `PendingOperationQueryPort` or
`PendingOperationResolutionPort` and maps the result. It does not own the
pending operation, clear it, change the FSM, or execute inventory. Those
rules live in `pi.pending_operation`, described in the
[flow contract](../research/pending-operation-web-flow-contract.md).

The page that calls this API is described in the
[pending operation page](pending-operation-web-ui.md). This document is only
the HTTP contract.

## Base path

```text
/api/v1
```

There is one current pending operation, so the path is singular. There is
no collection and no alternate route.

| Method | Path | Port |
| --- | --- | --- |
| `GET` | `/api/v1/pending-operation` | `get_current()` |
| `POST` | `/api/v1/pending-operation/{operation_id}/confirm` | `confirm(operation_id)` |
| `POST` | `/api/v1/pending-operation/{operation_id}/cancel` | `cancel(operation_id)` |

Confirm and cancel have no request body. The id is the path segment.
`Content-Type` is not required.

The standalone `voicestock-pi-web` command does not receive ports. `/health`,
`/`, and `/static/*` still answer. The three routes above then return
`503` with `application_not_ready`. `/health` does not check the ports.

## Get the current operation

`GET /api/v1/pending-operation`

When one exists, `200` and only the public view fields:

```json
{
  "operation_id": "op-aaa",
  "recognized_text": "agregar diez unidades de coca cola",
  "product": "Coca-Cola",
  "operation": "agregar",
  "quantity": 10,
  "unit": "unidad",
  "confirmation_message": "Agregar 10 unidades de Coca-Cola"
}
```

`operation` is the opaque label carried by `PendingOperationView`. It is not
an FSM state. `quantity` is an integer.

When nothing is pending, `204` and an empty body. That is a normal state,
not an error. This GET does not use `404`.

Both responses send `Cache-Control: no-store`. The body is the current
state, not a document to cache.

## Confirm and cancel

```text
POST /api/v1/pending-operation/op-aaa/confirm
POST /api/v1/pending-operation/op-aaa/cancel
```

The HTTP status comes from `ResolutionResult.status`:

| Application status | HTTP | Body `status` |
| --- | --- | --- |
| `success` | `200` | `success` |
| `already_resolved` | `200` | `already_resolved` |
| `no_pending` | `404` | `no_pending` |
| `stale_operation` | `409` | `stale_operation` |
| `conflict` | `409` | `conflict` |
| `execution_failed` | `503` | `execution_failed` |

`200` body:

```json
{
  "status": "success",
  "operation_id": "op-aaa",
  "resolved_action": "confirm"
}
```

`resolved_action` is `confirm` or `cancel`. On `success` and
`already_resolved` it is the action that stands. On `conflict` it is the
action that already won, not the one that was rejected:

```json
{
  "status": "conflict",
  "operation_id": "op-aaa",
  "resolved_action": "confirm"
}
```

On `stale_operation`, `execution_failed`, and `no_pending`,
`resolved_action` is `null`. `no_pending` also has `operation_id` `null`,
because the application result does not name a current operation. The other
two repeat the requested id. A stale response does not include the id that
is still current.

`already_resolved` is `200`, not `409`. A retry of the same action did not
run the operation again, and the client's intent already holds. That memory
is the in-process `last_resolution` from the flow contract. It is not
durable idempotency. After a restart the same retry is not remembered.

`execution_failed` stays `503`. The route does not clear the pending
operation. The application layer keeps it so the client can retry. The body
has no exception text.

Cancel does not produce `execution_failed` in the current application path.
The HTTP map is shared with confirm, so a port that did return that status
would still get `503`.

## Scenarios

The application rule for each row is the
[flow contract](../research/pending-operation-web-flow-contract.md). This
table is only the HTTP result.

| Situation | HTTP |
| --- | --- |
| `confirm(AAA)` succeeds, the response is lost, `confirm(AAA)` is sent again | `200` `already_resolved`. The executor is not run again. |
| The page shows AAA, the current operation is already BBB, the page sends `confirm(AAA)` | `409` `stale_operation`. BBB is unchanged. |
| AAA was confirmed, then `cancel(AAA)` arrives | `409` `conflict`. `resolved_action` is the action that already won. |
| The executor fails | `503` `execution_failed`. The operation stays pending. |
| `cancel(id)` | `200` `success` when that id is still current. Inventory is not executed. |

There is no route that confirms whatever happens to be current. The path
always names `operation_id`.

`already_resolved` is not durable idempotency. The gateway remembers only
`last_resolution` in memory. A process restart drops it.

Clearing the pending operation before `execute` is not this contract. A
failed execution stays pending so the client can retry.

`ProvisionalOperationExecutor` is what confirm calls in this increment. It
reports success and does not change inventory. A `200` `success` from confirm
does not mean stock was updated. `OperationConfirmationExecution` replaces
that executor later. If a future real execution succeeds and the slot or FSM
resolution then fails, a retry could run the effect again. That risk is
recorded in the flow contract. This API does not solve it.

A blank or whitespace `operation_id` is `422`:

```json
{
  "code": "invalid_operation_id",
  "detail": "operation_id must be a non-blank string"
}
```

The route rejects it before calling the port. If the port still raises
`ValueError` with that same message, the adapter returns this `422`. Any
other exception is left to the server. It is not rewritten as `no_pending`
or `execution_failed`.

## Application not ready

When the route's port was not passed to `create_app`:

```json
{
  "code": "application_not_ready",
  "detail": "pending-operation application ports are not configured"
}
```

Status `503`. Query checks the query port. Confirm and cancel check the
resolution port. This is a different `503` body from `execution_failed`.

## What this API does not do

- It does not list several pending operations.
- It does not authenticate the caller.
- It does not use CORS, TLS, or a push channel.
- It does not cache the GET response.
- It does not survive a process restart as an idempotency log.
