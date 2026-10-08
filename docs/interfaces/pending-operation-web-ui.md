# Pending operation page

How the operator page uses the
[pending-operation web API](pending-operation-web-api.md). The page is static
HTML, CSS, and JavaScript served by the Pi. It does not import Python and it
does not know the FSM, the gateway, or the executor.

## Layout

A header shows VoiceStock and one connection label: `Conectando`, `Listo`, or
`No disponible`. The workspace below is a single column, at most about 760px
wide. There is no sidebar. Later sections such as inventory or history can
be added around this shell; this page does not render disabled navigation.

## What the operator sees

| Situation | Workspace |
| --- | --- |
| First load | `Conectando...` |
| `GET` 204 | `Listo para escuchar`, asking the operator to use the physical button |
| `GET` 200 | The `confirmation_message` as the title, then product, operation, quantity, unit, and the recognized text |
| `GET` or resolution `503` with `application_not_ready` | VoiceStock is not available yet, and the page keeps retrying |
| `fetch` fails | `No disponible`, with a short retry message and no browser error text |

API field names and status codes are not shown. Values from the API are
written with `textContent`.

Confirm is the primary button. Cancel is secondary. While a resolution
request is in flight both buttons are disabled, and the chosen one reads
`Confirmando...` or `Cancelando...`.

## Polling

The page calls `GET /api/v1/pending-operation` about once a second. The next
wait starts after the previous request finishes, so a slow response does not
stack extra GETs. `application_not_ready` and a lost connection wait about
two seconds.

The id sent to confirm or cancel is the `operation_id` of the operation on
screen, not a hard-coded current item.

## Resolution

| HTTP result | Page |
| --- | --- |
| `200` `success` or `already_resolved` | Brief confirmation or cancellation message, then an immediate GET. `already_resolved` is not shown as an error. |
| `409` `stale_operation` | Says the operation changed and refreshes. |
| `409` `conflict` | Says the operation was already resolved, then refreshes. |
| `503` `execution_failed` | Keeps the card, explains that it can be tried again, and enables the buttons. |
| `404` `no_pending` | Refreshes. The following GET shows the empty state when nothing is pending. |

A successful empty GET returns the page to `Listo para escuchar`. The short
result message does not replace the workspace.
