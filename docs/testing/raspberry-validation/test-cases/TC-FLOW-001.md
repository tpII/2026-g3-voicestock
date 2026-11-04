# TC-FLOW-001 — Integrated Error Handling and Recovery

- Status: DESIGNED
- Executions: [EX-TC-FLOW-001-20261104-01](../executions/EX-TC-FLOW-001-20261104-01.md) (`PASSED_PENDING_DOCUMENTATION`; technical result PASSED; review NOT_REVIEWED; not `CLOSED_PASSED`)
- Procedure version: 2

Procedure version 2 is the text below. The execution record does not
change these steps. Release-to-idle time in that run is **NOT MEASURED**.

Procedure version 1 was not executed. It is preserved in
[TC-FLOW-001 procedure version 1](TC-FLOW-001-procedure-v1.md). Version 2
replaces it. Version 2 does not keep the deterministic success trial.

## Objective

Show that `PendingOperationFlow`, running inside `voicestock-pi` on the
Raspberry Pi, returns to `idle` with no pending operation when the PC does
not produce an acceptable operation.

The three measured conditions are distinguishable:

- Scenario A: the default stub answers HTTP 200 with `received_audio`.
  The Pi rejects that body as an operation contract.
- Scenario B: nothing listens on the PC port. The connection fails.
- Scenario C: a temporary server accepts the TCP connection and withholds
  the response past the Pi client timeout.

Successful pending-operation creation, confirm, cancel, and product
matching are not this case. Those observations are in
[TC-E2E-002](TC-E2E-002.md) and [TC-CON-001](TC-CON-001.md).

## Test level and type

Level: integration on the project hardware.

Type: functional, negative. No speech-to-text and no language model.

## Requirements and ClickUp traceability

- ClickUp: [PendingOperationFlow-05](https://app.clickup.com/t/86e3evaer).
- Requirement: the running flow returns to idle, with the operator message
  that matches the peer condition, and with no pending operation.

## Source modules and documentation

- `pi.pending_operation.flow.PendingOperationFlow`.
- `pi.runtime` and the `voicestock-pi` console script.
- `pi.communication.client.ClientErrorCode`: `connection_failed` and
  `timeout` are both transport failures. The public status does not publish
  `error.code`.
- Operator sentences in `flow.py`:
  - contract rejection: `El pedido no es una operación válida. Presioná el botón para intentar de nuevo.`
  - transport: `No se pudo comunicar con la PC. Presioná el botón para intentar de nuevo.`
  - service error, not expected here: `La PC no pudo interpretar el pedido. Presioná el botón para intentar de nuevo.`

Scenarios B and C use the same transport sentence. The execution
distinguishes them by the peer evidence and by the time until idle, not by
a second sentence. A contract-rejection sentence on B or C is the wrong
classification. A service-error sentence on A, B, or C is the wrong
classification.

## Preconditions and dependencies

- [TC-PTT-001](TC-PTT-001.md), [TC-COM-002](TC-COM-002.md), and
  [TC-WEB-001](TC-WEB-001.md) are not **FAILED** or **BLOCKED**.
- Raspberry Pi 3, BCM GPIO17, `voicestock_mic`, campaign catalog loaded by
  the Pi process. Record the catalog path and its SHA-256.
- Arch PC at `192.168.50.2`. Pi web UI at `http://192.168.50.1:8000/`.
- `VOICESTOCK_AUDIO_PIPELINE` is unset or `stub` for every PC process in
  this case. Do not set `groq`. Do not load API credentials.
- No deterministic contract fixture. Do not start one.

## Required hardware and software

- Pi, physical button, USB microphone, operator page, and PC on the cell.
- `voicestock-pi` and `voicestock-pc-server` on `PATH` in the project
  environments. If `voicestock-pi` is absent, the run is **BLOCKED** unless
  the execution quotes the exact `python -m pi.runtime` command that was
  used instead. That deviation stays in the record.
- Python standard library on Arch for the scenario C hold server. The
  script is stored outside this repository.

## Preparation

On the Pi:

```bash
mkdir -p recordings/tc-flow-001
```

Record this client timeout for the whole run. Five seconds is the test
setting. It is not a product latency budget.

```bash
export VOICESTOCK_PC_URL=http://192.168.50.2:8000
export VOICESTOCK_PC_TIMEOUT=5
export VOICESTOCK_WEB_HOST=192.168.50.1
export VOICESTOCK_WEB_PORT=8000
```

Start the Pi once. Do not restart it between cycles of one scenario, and
do not restart it between scenarios unless a crash forces a new execution
id.

```bash
voicestock-pi \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device voicestock_mic \
  --output-directory recordings/tc-flow-001 \
  --catalog <PI_CATALOG_PATH> \
  --keep-recordings
```

Confirm the process is up before the first press:

```bash
curl -sS -D - http://192.168.50.1:8000/health
curl -sS http://192.168.50.1:8000/api/v1/system-status
curl -sS -D - -o /dev/null -w 'pending_http=%{http_code}\n' \
  http://192.168.50.1:8000/api/v1/pending-operation
```

Expect health HTTP 200 and `{"status":"ok"}`, `phase` `idle`,
`pending_operation` null, and pending-operation HTTP 204.

On Arch, before scenario A, confirm the pipeline is not Groq:

```bash
printf '%s\n' "${VOICESTOCK_AUDIO_PIPELINE:-unset}"
```

The printed value must be `unset` or `stub`.

## Observations to record for every measured cycle

From button release, poll about twice a second until the expected idle
state appears, or until `VOICESTOCK_PC_TIMEOUT` plus 3 seconds. That window
is an observation abort. It is not a pass limit for product latency.

```bash
curl -sS -D - -w '\ntime_total=%{time_total}\n' \
  http://192.168.50.1:8000/api/v1/system-status
curl -sS -D - -o /dev/null -w 'pending_http=%{http_code}\n' \
  http://192.168.50.1:8000/api/v1/pending-operation
curl -sS -D - -o /dev/null -w 'health_http=%{http_code}\n' \
  http://192.168.50.1:8000/health
```

Record, per cycle:

- scenario id and measured index (`A1`–`A3`, `B1`–`B3`, `C1`–`C3`);
- peer evidence (listening process, or its absence, or a hold-server
  `ACCEPTED` line);
- `phase`, `operator_message`, and `pending_operation`;
- pending-operation HTTP status;
- health HTTP status;
- seconds from release until the first status read that shows the expected
  idle message, if that read exists, otherwise **NOT OBSERVED** inside the
  window;
- `time_total` of that status read, as API observation time;
- the sentence visible on `http://192.168.50.1:8000/`;
- WAV filename under `recordings/tc-flow-001/` and its SHA-256.

Do not invent a latency budget. Per-stage time inside the Pi process is
**NOT MEASURED**.

One practice press may precede each scenario. Label it `practice` and
exclude it from the three measured cycles.

## Execution

### Scenario A — invalid operation contract

On Arch, with Groq unset:

```bash
export VOICESTOCK_PC_HOST=192.168.50.2
export VOICESTOCK_PC_PORT=8000
unset VOICESTOCK_AUDIO_PIPELINE
voicestock-pc-server
```

Confirm something is listening on `192.168.50.2:8000` before the first
measured press. The stub returns a successful HTTP body whose payload is
`received_audio`, not a version-1 contract.

Speak any short phrase. The words are not interpreted.

Expected after each of three measured cycles, inside the observation
window, without restarting `voicestock-pi`:

- `phase` is `idle`;
- `operator_message` is exactly `El pedido no es una operación válida. Presioná el botón para intentar de nuevo.`;
- `pending_operation` is null;
- pending-operation HTTP status is 204;
- health HTTP status is 200;
- the page shows that same contract-rejection sentence;
- no second pending operation appears.

Stop `voicestock-pc-server` before scenario B. Confirm
`192.168.50.2:8000` is no longer listening.

### Scenario B — connection failure

Leave the Pi process running. Do not start a server on
`192.168.50.2:8000`. Record the command that shows the port is closed, for
example:

```bash
ss -ltn 'sport = :8000'
```

An empty listening list is the peer evidence. A refused connection is not
a contract rejection and not a response timeout.

Expected after each of three measured cycles, without restarting
`voicestock-pi`:

- `phase` is `idle`;
- `operator_message` is exactly `No se pudo comunicar con la PC. Presioná el botón para intentar de nuevo.`;
- `pending_operation` is null and pending-operation HTTP status is 204;
- health HTTP status is 200;
- the page shows that same transport sentence;
- the return to idle is not explained as a contract rejection.

If the closed port still produces the contract-rejection sentence, that
cycle is **FAILED**.

### Scenario C — response timeout

On Arch, save the following script outside the repository, at
`~/voicestock-test-evidence/tc-flow-001/hold_server.py`. Do not commit it.

```python
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOLD_SECONDS = 30


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        print(f"ACCEPTED {self.path} bytes={length}", flush=True)
        time.sleep(HOLD_SECONDS)
        body = b'{"status":"success","payload":{},"error":null}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        print("RESPONDED", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("192.168.50.2", 8000), Handler)
    print("HOLD_READY", flush=True)
    server.serve_forever()
```

`HOLD_SECONDS` is 30. The Pi timeout for this run is 5. The server must
still be inside `sleep` when the Pi gives up. It does not call Groq, does
not read credentials, and does not touch inventory.

Start it only after port 8000 is free:

```bash
python3 ~/voicestock-test-evidence/tc-flow-001/hold_server.py
```

Wait for `HOLD_READY`. Each measured cycle must print `ACCEPTED` before
the Pi returns to idle. A cycle with no `ACCEPTED` line is not scenario C.

Expected after each of three measured cycles, without restarting
`voicestock-pi`:

- the hold server printed `ACCEPTED`;
- `phase` is `idle`;
- `operator_message` is the transport sentence from scenario B, not the
  contract-rejection sentence and not the service-error sentence;
- `pending_operation` is null and pending-operation HTTP status is 204;
- health HTTP status is 200;
- the page shows the transport sentence;
- another press can start the next cycle while this same Pi process is
  still up.

Record the release-to-idle time. An immediate refusal, with no `ACCEPTED`
line, is scenario B evidence and does not satisfy scenario C.

### Recovery cycle

After scenario C, stop the hold server and free port 8000. Start the stub
again with the scenario A command. Do not restart `voicestock-pi`. One
measured press must end like scenario A: contract-rejection sentence, idle,
HTTP 204, health 200. This cycle checks that the runtime is still usable.
It does not call Groq and it does not require a success contract. Label it
`R1`. It is not one of the nine error cycles.

## Evidence

Store notes outside git under
`~/voicestock-test-evidence/tc-flow-001/`. Do not commit WAV files, the
hold script as a campaign binary, or credentials. The procedure text above
is the specification of the hold script. The execution record quotes the
SHA-256 of the copy that was actually run.

## Metrics

| Metric | Rule |
| --- | --- |
| Measured cycles per scenario | 3, practice excluded |
| Cycles that show the expected message, idle, and HTTP 204 | 3 of 3 per scenario |
| Release-to-idle time and status `time_total` | Recorded when observed. Budget **TO BE DEFINED**. |
| Pending operations during an error cycle | 0 |

## Acceptance criteria

1. Scenario A: three measured cycles end `idle` with the contract-rejection
   sentence, `pending_operation` null, and pending-operation HTTP 204.
   The stub was the peer. Groq was not enabled.
2. Scenario B: three measured cycles end `idle` with the transport
   sentence, null pending operation, and HTTP 204, while nothing was
   listening on `192.168.50.2:8000`.
3. Scenario C: three measured cycles end `idle` with the transport
   sentence, null pending operation, and HTTP 204, and each cycle has an
   `ACCEPTED` line from the hold server. The configured Pi timeout is
   recorded and is shorter than `HOLD_SECONDS`.
4. No measured error cycle shows a pending operation or a second id.
5. The Pi process is not restarted between the measured cycles of a
   scenario. Health stays HTTP 200 at the check that records idle.
6. The page shows the same sentence the API recorded for that cycle.
7. `R1` repeats the scenario A outcome on the still-running Pi after the
   hold server has been stopped.
8. B is not recorded as a contract rejection. C is not recorded as an
   immediate connection refusal. Neither is recorded as a service error.

## Failure conditions

- The operator sentence does not match the peer that was actually running:
  **FAILED**.
- A pending operation appears: **FAILED**.
- Scenario C has no `ACCEPTED` line: **FAILED** as the wrong condition, not
  as a pass of scenario B.
- Groq, an API key, or a contract-fixture success payload was used:
  **FAILED** as a procedure deviation.
- The Pi process exits or `/health` stops answering: **FAILED** for the
  cycles that could not be checked. A restart is a new execution id.

## Recovery and cleanup

Stop the hold server with Ctrl+C. Stop the stub. Stop `voicestock-pi`.
On Arch and on the Pi, confirm the test listeners are gone:

```bash
ss -ltn 'sport = :8000'
```

Archive WAV checksums outside git. Do not leave the hold server running.
Do not leave `VOICESTOCK_PC_TIMEOUT=5` exported for a later Groq run unless
that later execution records the value on purpose.

## Limitations and exclusions

This case does not cover:

- a successful contract, including any deterministic fixture response;
- confirm or cancel;
- a simulated end-to-end pass;
- speech-to-text or language-model accuracy;
- inventory persistence;
- unplugging the microphone or other capture failures.

`error.code` is not on `system-status`. This procedure does not require a
log line that prints `connection_failed` or `timeout`. The peer evidence
is the distinction. Service-error handling is not claimed.
