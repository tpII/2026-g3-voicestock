# TC-FLOW-001 — PendingOperationFlow on the Raspberry Pi

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that `voicestock-pi` changes phase on the real button and microphone:
the shipped audio stub returns the cycle to idle with the contract-rejection
message, a missing PC returns the transport message, and a contract fixture
reaches `wait_confirmation` and back to idle without a second pending
operation.

## Test level and type

Level: integration.

Type: functional, including the negative paths the current server already
produces.

## Requirements and ClickUp traceability

- ClickUp: [PendingOperationFlow-05](https://app.clickup.com/t/86e3evaer).
- Requirement: one in-memory pending operation and the phases in
  [the workflow](../../../architecture/pending-operation-flow.md).

## Source modules and documentation

- `pi.pending_operation.flow.PendingOperationFlow`.
- `pi.runtime`.
- Operator messages in `flow.py`:
  - contract rejection: `El pedido no es una operación válida. Presioná el botón para intentar de nuevo.`
  - transport: `No se pudo comunicar con la PC. Presioná el botón para intentar de nuevo.`
  - capture: `No se pudo grabar el audio. Presioná el botón para intentar de nuevo.`
- [TC-CON-001](TC-CON-001.md) already classified the stub shape as
  `contract_rejection`. This case checks that the running process shows the
  matching operator message.

## Preconditions and dependencies

- [TC-PTT-001](TC-PTT-001.md), [TC-COM-002](TC-COM-002.md), and
  [TC-WEB-001](TC-WEB-001.md) are not **FAILED** or **BLOCKED**.
- Trial A uses `voicestock-pc-server` and the stub. It does not need the
  fixture.
- Trial B needs the fixture from the
  [test plan](../test-plan.md#fixture-requirements). If the fixture is
  absent, trial B is **BLOCKED** and trials A and C can still be recorded.
  The case is not **CLOSED_PASSED** while trial B is blocked.
- Trial C needs the ability to stop the PC peer.

## Required hardware and software

- Pi, button, microphone, campaign catalog, PC on the cell.
- `--keep-recordings` so the WAV survives the send. The flow deletes the
  file by default.

## Preparation

```bash
mkdir -p recordings/tc-flow-001
```

Start command, used for every trial. Restart it between trials so a leftover
message is not mistaken for the next result.

```bash
VOICESTOCK_PC_URL=http://192.168.50.2:8000 \
VOICESTOCK_PC_TIMEOUT=10 \
VOICESTOCK_WEB_HOST=192.168.50.1 \
VOICESTOCK_WEB_PORT=8000 \
  voicestock-pi \
  --pin <BCM_PIN> \
  --bounce-time 0.05 \
  --input-device "<QUERY>" \
  --output-directory recordings/tc-flow-001 \
  --catalog <CATALOG_PATH> \
  --keep-recordings
```

Poll:

```bash
curl -sS http://192.168.50.1:8000/api/v1/system-status
```

## Execution

Trial A, stub rejection. Start `voicestock-pc-server` on `192.168.50.2:8000`.
Confirm idle. Press, speak, release. Poll until the phase is `idle` and
`operator_message` is the contract-rejection sentence, or until the 30 second
operator abort. `pending_operation` must be null. `GET
/api/v1/pending-operation` stays 204. Repeat for three measured presses.
One practice press may be labeled and excluded.

Trial C, transport. Stop the PC server. Press, speak, release. Expect idle
and the transport sentence. Three measured presses. This trial does not
need the fixture. It is listed after A so the server is stopped on purpose.
Do not run it while trial A is still collecting samples.

Trial B, fixture success. Start the fixture instead of the stub. Press,
speak, release. Expect `processing` and then `wait_confirmation` with one
pending operation whose fields match the fixture table. While that id is
current, press again. The id must remain. Cancel through the API:

```bash
curl -sS -D - -X POST \
  http://192.168.50.1:8000/api/v1/pending-operation/<OPERATION_ID>/cancel
```

Expect HTTP 200, status `success`, `resolved_action` `cancel`, then idle.
Repeat the success-and-cancel pair for three measured cycles after one
warm-up cycle. A confirm cycle is reserved for TC-WEB-002 and TC-E2E-001 so
this case does not depend on the page. One of the three cycles may confirm
via `POST .../confirm` instead of cancel, to show the flow clears the slot
after `ProvisionalOperationExecutor` returns success. Record which cycles
confirmed.

Optional capture-failure probe, once: with the process idle, unplug the USB
microphone and press the button. Expect idle and the capture sentence, and
no pending operation. Replug the microphone into the same port before any
later case. If the press does something else, record the body and do not
force the hardware. This probe is required. If unplugging is unsafe on the
lab cable, mark the probe **BLOCKED** and the case cannot be
**CLOSED_PASSED**.

## Observations and evidence

- Status JSON at idle, during the wait, and after each settle.
- WAV paths and checksums for the kept files.
- Which peer process was running for each trial.

## Metrics

| Metric | Rule |
| --- | --- |
| Cycles that reach the expected message or phase | 3 of 3 per trial |
| API observation latency until the expected phase | Recorded. Limit **TO BE DEFINED**. |
| Concurrent pending operations | Must stay at most one |

Per-stage times inside the process are **NOT MEASURED**. The product does
not log monotonic stamps between capture, HTTP, and validation.

## Acceptance criteria

1. Trial A: three cycles end idle, with the contract-rejection message, and
   never with a pending operation.
2. Trial C: three cycles end idle, with the transport message.
3. Trial B: three cycles reach `wait_confirmation` with the fixture fields
   and return to idle after cancel or confirm, with 204 and a null pending
   operation.
4. A press during `wait_confirmation` does not change `operation_id`.
5. The capture-failure probe matches the capture sentence, or is
   **BLOCKED** with a reason.
6. Confirm, when used, does not create an inventory database.
7. Trial A was not used as evidence that a pending operation can be
   created.

## Failure conditions

- The wrong operator message for the peer that was actually running:
  **FAILED**.
- Two pending ids: **FAILED**.
- Trial B run against the stub and then described as a success: **FAILED**
  as a false pass. Reclassify that sample as trial A.
- Fixture not available: trial B **BLOCKED**.

## Recovery and cleanup

Cancel a leftover operation. Stop the Pi, the stub, and the fixture.
Replug the microphone if it was removed. Archive WAV files outside git.

## Limitations and exclusions

Service-error handling (`La PC no pudo interpretar el pedido...`) needs a
handler that returns `ServiceResult` failure. Neither the stub nor the
minimum fixture does that. The optional fixture mode in the test plan is
not required for this case. Do not claim the service-error sentence was
tested. SQLite and real interpretation are out of scope.
