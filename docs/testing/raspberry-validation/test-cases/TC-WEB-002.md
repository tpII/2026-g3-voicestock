# TC-WEB-002 — Pending operation UI and HTTP resolution

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that a real pending operation appears in the Pi API and on the page,
and that confirm and cancel follow the HTTP map, including a repeated
confirm, a conflicting second action, and a stale id.

## Test level and type

Level: integration.

Type: functional.

## Requirements and ClickUp traceability

- ClickUp: [PendingOperationWeb-07](https://app.clickup.com/t/86e3eve7j).
- Requirement: the page and the resolution routes in
  [the API](../../../interfaces/pending-operation-web-api.md) and
  [the page](../../../interfaces/pending-operation-web-ui.md).
- This case does not close
  [PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6).

## Source modules and documentation

- `pi.web.api`, `pi.web.static.app.js`.
- `pi.pending_operation.gateway`.
- [Fixture payload](../fixtures/README.md).
- The PC process must be the contract fixture from the
  [test plan](../test-plan.md#fixture-requirements). The shipped
  `voicestock-pc-server` cannot create a pending operation.

## Preconditions and dependencies

- [TC-WEB-001](TC-WEB-001.md) showed the idle server.
- [TC-PTT-001](TC-PTT-001.md) showed the button path.
- The fixture entry point exists and is recorded by path and commit. If it
  does not exist, the execution is **BLOCKED**. Do not substitute the stub.

## Required hardware and software

- Pi, button, microphone, PC browser on the cell.
- Fixture listening on `192.168.50.2:8000`.
- `curl` on the PC or on the Pi. Prefer the Pi for API timing so the
  sample does not cross an unsynchronized pair of clocks more than the
  request itself already does. The browser check is separate and is not
  timed as an API duration.

## Preparation

Start the fixture. Start `voicestock-pi` as in TC-WEB-001 trial B, with
`--keep-recordings`, the campaign catalog, and
`VOICESTOCK_PC_URL=http://192.168.50.2:8000`.

Confirm idle with one `system-status` read before the first press.

## Execution

The page polls every 1000 ms. After each press, wait until the API shows
`wait_confirmation` before judging the page. A page that updates on the
next poll is correct. A page that never updates fails.

Trial 1, confirm from the page.

1. Press, speak briefly, release.
2. Poll `GET /api/v1/system-status` until `phase` is `wait_confirmation`
   or 30 seconds have passed. Thirty seconds is an operator abort for this
   wait, not a product budget. The client timeout is 10 seconds, so a
   healthy fixture returns well inside that abort.
3. `GET /api/v1/pending-operation` returns 200 and the body matches the
   [fixture table](../fixtures/README.md), including `unit` `unidad` and
   confirmation message `Agregar 2 unidades de Arroz Marolio 1 kg`.
4. Open or refresh `http://192.168.50.1:8000/` from the PC. The
   confirmation message and the `operation_id` on screen match the API.
5. Press Confirmar on the page. The API then shows `idle` and
   `pending-operation` returns 204.
6. Repeat `POST /api/v1/pending-operation/<id>/confirm` with that same id.
   Expect HTTP 200 and status `already_resolved`.

Trial 2, cancel from the page. Same capture steps. Press Cancelar. Expect
idle and 204. `POST` confirm on that id expects HTTP 409 and status
`conflict`, because the remembered action is cancel.

Trial 3, stale id. Capture once more and leave the operation pending. `POST`
confirm with a different non-empty id. Expect HTTP 409 and status
`stale_operation`. The original id is still pending. Then cancel the real
id from the page so the device is left idle.

Trial 4, second press. Capture once more. While the API shows
`wait_confirmation`, press and release the button again. Poll for five
seconds. `operation_id` must not change and a second pending object must
not appear. Then cancel.

Do not look for an inventory file. `ProvisionalOperationExecutor` reports
success and writes nothing. Record that the output directory gained WAV
files only because `--keep-recordings` was set.

## Observations and evidence

- Status JSON before and after each resolution.
- The operation ids.
- Whether the page text matched.
- WAV checksums if the files are kept as evidence of the capture, stored
  outside git.

## Metrics

| Metric | Rule |
| --- | --- |
| API time from release until `wait_confirmation` | Pi monotonic poll. This is API observation latency. Limit **TO BE DEFINED**. |
| UI lag after the API changes | User-observed. Not the same number. Limit **TO BE DEFINED**. |
| `/health` timing | Not repeated here |

## Acceptance criteria

1. Trial 1 creates one pending operation whose public fields match the
   fixture table, then the page confirm clears it.
2. A second confirm of that id is HTTP 200 `already_resolved`.
3. Trial 2 cancel clears it, and a later confirm of that id is HTTP 409
   `conflict`.
4. Trial 3 stale confirm does not clear the current operation.
5. Trial 4 does not replace the `operation_id`.
6. No trial writes an inventory database. Absence of a new SQLite file in
   the working directory is recorded. A successful confirm is not a stock
   change.
7. The fixture, not `voicestock-pc-server`, was the peer. The execution
   names the fixture command.

## Failure conditions

- The stub rejection message appears: wrong peer. **FAILED** as a procedure
  deviation, not as a product defect of the web UI.
- The page and the API disagree on `operation_id` or
  `confirmation_message` after more than one poll interval plus a second
  for the operator to look: **FAILED**.
- Fixture missing: **BLOCKED**.

## Recovery and cleanup

Cancel any leftover pending operation. Ctrl+C the Pi and the fixture.
Archive WAV files outside git.

## Limitations and exclusions

`execution_failed` (HTTP 503) is not produced by
`ProvisionalOperationExecutor`. This case does not cover it. Real
speech-to-text and real interpretation are not used. The synthetic
`recognized_text` is not a transcription result.
