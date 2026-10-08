# Pending operation page

How the operator page uses the
[pending-operation web API](pending-operation-web-api.md). The page is static
HTML, CSS, and JavaScript served by the Pi. It does not import Python and it
does not know the FSM, the gateway, or the executor.

What confirm and cancel mean in this increment is the
[flow contract](../research/pending-operation-web-flow-contract.md). The page
only applies the HTTP results below. It does not show status codes.

Why the page is static files in the same process, with no CDN, no Node.js,
no separate frontend server, no WebSocket, and no SSE, is
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).
The page and the API share one origin, so this increment does not add CORS.
HTTPS and login are also out of this increment; the ADR records that.

## Layout

```text
header          VoiceStock and the connection label
workspace       one column, about 760px at most, centered
operation card  the pending operation, when there is one
status          short feedback that does not replace the workspace
```

The header labels are `Conectando`, `Listo`, and `No disponible`, each with
text, not color alone.

There is no sidebar. The shell can later hold Inventory, History, Products,
or Settings. Those sections are not implemented, and the page does not render
disabled navigation for them.

## States

| State | What the operator sees |
| --- | --- |
| Connecting | First load: `Conectando...` in the workspace and `Conectando` in the header. |
| Empty | `GET` 204. `Listo para escuchar`, asking the operator to press the physical button and speak. Header: `Listo`. |
| Pending | `GET` 200. Eyebrow `Operación pendiente`. The title is `confirmation_message`. Then product, operation, quantity, unit, and the recognized text in quotes. |
| Resolving | After Confirm or Cancel. Both buttons are disabled. The chosen one reads `Confirmando...` or `Cancelando...`. |
| Execution failure | The card stays. `No se pudo confirmar la operación.` The operation is still pending and can be tried again. The buttons are enabled. |
| Application not ready | `503` `application_not_ready`. The card is hidden. `VoiceStock todavía no está disponible. Reintentando conexión...` Header: `No disponible`. |
| Disconnected | `fetch` fails. `No se pudo conectar. Reintentando...` Header: `No disponible`. No browser error text. |

Empty and Connecting are different. A quiet first load is not the same screen
as "nothing is pending".

API values are inserted with `textContent`.

## Polling

The page calls `GET /api/v1/pending-operation` about once a second. The next
wait starts after the previous request finishes, so a slow response does not
stack extra GETs. Application-not-ready and a lost connection wait about two
seconds and keep trying.

Those intervals are the current UI choice. They are not part of the HTTP
contract.

## Confirm and cancel

The POST uses the `operation_id` of the operation on screen.

Both buttons are disabled for that request, so a double click does not send
a second POST from the page. That is only a UX guard. The guarantee against
two resolutions is the lock in the application gateway, described in the
flow contract.

After the response, the page requests the current operation immediately.

| HTTP result | Page |
| --- | --- |
| `200` `success` or `already_resolved` | `Operación confirmada` or `Operación cancelada`, then refresh. `already_resolved` is not shown as an error. |
| `409` `stale_operation` | `La operación cambió. Actualizando información...`, then refresh. The new operation replaces the old one. |
| `409` `conflict` | `La operación ya fue resuelta.`, then refresh. The page does not undo the winning action. |
| `503` `execution_failed` | Keep the card, explain that it can be tried again, enable the buttons. |
| `404` `no_pending` | Refresh. The following GET shows Empty when nothing is pending. |
| `503` `application_not_ready` | Application not ready, and keep polling. |
| network failure | Disconnected, and keep polling. |

A successful empty GET returns the page to `Listo para escuchar`. The short
result message does not replace the workspace.
