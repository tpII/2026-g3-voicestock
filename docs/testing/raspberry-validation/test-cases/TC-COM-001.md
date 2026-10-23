# TC-COM-001 — Raspberry Pi HTTP client

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that `voicestock-pi-client` on the Raspberry Pi receives a transport
envelope from the real `voicestock-pc-server` across the VoiceStock cell,
using the text endpoint.

## Test level and type

Level: integration.

Type: functional and measurement.

## Requirements and ClickUp traceability

- ClickUp: [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux).
- Requirement: `POST /api/v1/interpret` with `{"text": "..."}` returns a
  `TransportEnvelope`. The contract is
  [Raspberry Pi–PC communication](../../../interfaces/pc-communication.md).

## Source modules and documentation

- `pi.communication.client.HttpInterpretationClient`.
- `pi.main`.
- `pc.main` and `pc.communication.server`.
- Default client URL is `http://127.0.0.1:8000`. On the Pi that default is
  the Pi itself, not the PC. This case must set `VOICESTOCK_PC_URL`.
- Default server bind is `127.0.0.1`. The PC process must set
  `VOICESTOCK_PC_HOST` or the Pi cannot connect. Bind to `192.168.50.2`,
  not `0.0.0.0`, so the server is not opened on the Internet interface.
  The README example uses `0.0.0.0` as a development override. This
  campaign does not use that override.

## Preconditions and dependencies

- [TC-NET-002](TC-NET-002.md) reachability criteria met.
- No interpretation quality is expected. The default provider is `stub`,
  which returns `{"recognized_text": "<the text>"}` inside a successful
  `ServiceResult`. That is the current server. Do not configure an API key.

## Required hardware and software

- Pi and PC on the cell.
- Both checkouts installed so `voicestock-pi-client` and
  `voicestock-pc-server` exist.
- Port 8000 free on `192.168.50.2`. If it is not, pick another port, record
  it, and use it in `VOICESTOCK_PC_URL`. Do not stop an unrelated service
  without writing the deviation.

## Preparation

On the PC:

```bash
VOICESTOCK_PC_HOST=192.168.50.2 VOICESTOCK_PC_PORT=8000 voicestock-pc-server
```

Leave it running. On the Pi, a warm-up call (discarded):

```bash
VOICESTOCK_PC_URL=http://192.168.50.2:8000 VOICESTOCK_PC_TIMEOUT=10 \
  voicestock-pi-client "agregá dos paquetes de arroz"
```

## Execution

Wrap the measured calls so the duration is monotonic on the Pi. Ten
measured calls. The text may stay constant; this case does not vary the
sentence to test a model.

```bash
python - <<'PY'
import os
import time
import subprocess
os.environ["VOICESTOCK_PC_URL"] = "http://192.168.50.2:8000"
os.environ["VOICESTOCK_PC_TIMEOUT"] = "10"
text = "agregá dos paquetes de arroz"
for index in range(1, 11):
    t0 = time.monotonic()
    completed = subprocess.run(
        ["voicestock-pi-client", text],
        check=False,
        capture_output=True,
        text=True,
    )
    t1 = time.monotonic()
    print(f"sample {index} exit {completed.returncode} duration {t1 - t0:.6f}")
    print(completed.stdout)
    print(completed.stderr)
PY
```

The client exits 0 when the envelope status is `success`.

Confirm the body parses as a success envelope whose service payload is
`{"recognized_text": "agregá dos paquetes de arroz"}` (the stub). Extra
whitespace in the printed JSON is fine. A contract-shaped payload is not
expected from this endpoint today.

## Observations and evidence

- Server bind address from the operator's notes (the process does not
  print a guaranteed banner; record the environment variables used).
- Ten stdout bodies and durations.
- Exit codes.

## Metrics

| Metric | Limit |
| --- | --- |
| Client duration | Recorded. Budget **TO BE DEFINED**. |
| Success count | 10 of 10 measured calls exit 0 with stub payload |
| Timeout | The configured 10 seconds is the client budget, not a measured SLA |

## Acceptance criteria

1. All ten measured calls exit 0.
2. Each body is a success `TransportEnvelope` and the inner service
   payload's `recognized_text` equals the text sent.
3. The server was bound to `192.168.50.2`, confirmed by `ss` or `ip` on
   the PC (`ss -ltnp` filtered to port 8000 is acceptable). The Internet
   interface does not need to show the port.
4. Durations are in the raw table. No duration fails the case until a
   budget exists, except a call that hits the client timeout: that call
   fails criterion 1.
5. No API key was required and none is in the transcript.

## Failure conditions

- Connection errors: **FAILED** after TC-NET-002 passed. Include the
  envelope code (`connection_failed` or other).
- A payload that is only a contract, or an error from a real provider:
  the server is not the default stub. **FAILED** as a configuration
  deviation if a provider other than `stub` was selected.
- Port already taken and no alternate was recorded: **BLOCKED**.

## Recovery and cleanup

Stop the PC server with Ctrl+C. Do not leave it bound. The next case
starts its own server.

## Limitations and exclusions

The text endpoint is not the path `voicestock-pi` uses for recordings.
WAV transfer is TC-COM-002. The stub's `recognized_text` echo is not
interpretation and does not close
[InterpretationService-04](https://app.clickup.com/t/86e3ev2v6).
A localhost run on one machine does not satisfy this case.
