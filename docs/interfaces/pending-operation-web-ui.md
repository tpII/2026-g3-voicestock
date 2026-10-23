# Pending operation page

How the operator page uses the
[pending-operation web API](pending-operation-web-api.md). The page is static
HTML, CSS, and JavaScript served by the Pi. It does not import Python and it
does not know the FSM, the gateway, or the executor.

What confirm and cancel mean is the
[operation workflow](../architecture/pending-operation-flow.md). The page
only applies the HTTP results below. It does not show status codes. The HTTP
shapes are the
[pending-operation web API](pending-operation-web-api.md#read-the-cycle).

Why the page is static files in the same process, with no CDN, no Node.js,
no separate frontend server, no WebSocket, and no SSE, is
[ADR-0009](../decisions/0009-use-in-process-fastapi-and-static-web-ui.md).
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

The page follows `phase` from `GET /api/v1/system-status`. It does not choose
the next phase. The physical button starts a capture.

| `phase` | What the operator sees |
| --- | --- |
| Connecting | First load, before the first status response: `Conectando...` in the workspace and `Conectando` in the header. |
| `idle` | `headline` and `detail` from the status. Normally `Listo para escuchar` and the request to press the button. Header: `Listo`. `operator_message`, when present, is shown under that text. |
| `recording` | `headline` and `detail` (`Escuchando...`, then the request to release the button). The card is hidden. Header: `Listo`. |
| `processing` | `headline` (`Procesando solicitud...`). The card is hidden. Header: `Listo`. |
| `wait_confirmation` | The pending card, when `pending_operation` is present. Eyebrow `Operación pendiente`. The title is `confirmation_message`. Then product, operation, quantity, and unit. Header: `Listo`. |
| Resolving | After Confirm or Cancel. Both buttons are disabled. The chosen one reads `Confirmando...` or `Cancelando...`. |
| Execution failure | The card stays. `No se pudo confirmar la operación.` The operation is still pending and can be tried again. The buttons are enabled. |
| Application not ready | `503` `application_not_ready`. The card is hidden. `VoiceStock todavía no está disponible. Reintentando conexión...` Header: `No disponible`. |
| Disconnected | `fetch` fails, or the body has no `phase`. `No se pudo conectar. Reintentando...` Header: `No disponible`. No browser error text. |

Connecting is the first load. `idle` is a status the server already returned.

When `recognized_text` has non-blank text, the card shows `Texto reconocido`
and that text in quotes. When the value is missing, blank, or not a string,
that section is hidden. The product, the operation, the quantity, the unit,
and Confirm and Cancel stay. The page does not invent a transcription.

API values are inserted with `textContent`.

## Polling

The page calls `GET /api/v1/system-status` about once a second. The next
wait starts after the previous request finishes, so a slow response does not
stack extra GETs. Application-not-ready and a lost connection wait about two
seconds and keep trying. Polling pauses while a confirm or cancel request is
in flight, then runs once as soon as that request finishes.

`GET /api/v1/pending-operation` remains in the API. The page does not poll it.

Those intervals are the current UI choice. They are not part of the HTTP
contract.

## Confirm and cancel

The POST uses the `operation_id` of the operation on screen.

Both buttons are disabled for that request, so a double click does not send
a second POST from the page. That is only a UX guard. The guarantee against
two resolutions is the lock in the application gateway, described in the
[operation workflow](../architecture/pending-operation-flow.md#confirmation-and-cancellation).

After the response, the page requests `GET /api/v1/system-status` immediately.

| HTTP result | Page |
| --- | --- |
| `200` `success` or `already_resolved` | `Operación confirmada` or `Operación cancelada`, then refresh. `already_resolved` is not shown as an error. |
| `409` `stale_operation` | `La operación cambió. Actualizando información...`, then refresh. The new operation replaces the old one. |
| `409` `conflict` | `La operación ya fue resuelta.`, then refresh. The page does not undo the winning action. |
| `503` `execution_failed` | Keep the card, explain that it can be tried again, enable the buttons. |
| `404` `no_pending` | Refresh. The following status shows `idle` when nothing is pending. |
| `503` `application_not_ready` | Application not ready, and keep polling. |
| network failure | Disconnected, and keep polling. |

A following status of `idle` returns the page to the idle headline and
detail. The short result message does not replace the workspace.
