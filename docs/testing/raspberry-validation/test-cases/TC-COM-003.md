# TC-COM-003 — HTTP client connection failure and timeout

- Status: DESIGNED
- Executions: [EX-TC-COM-003-20261103-01](../executions/EX-TC-COM-003-20261103-01.md) (`PASSED_PENDING_DOCUMENTATION`; technical error handling PASSED; procedure version 1 with a Python listener deviation; not a run of version 2; evidence pending; review NOT_REVIEWED; not `CLOSED_PASSED`)
- Procedure version: 2

Procedure version 2 below is the procedure in force. It was written on
2026-11-03 after
[EX-TC-COM-003-20261103-01](../executions/EX-TC-COM-003-20261103-01.md).
That execution followed
[procedure version 1](TC-COM-003-procedure-v1.md) and used a Python
listener instead of the `ncat` example. It is not relabeled as a run of
this version.

A silent peer may be `ncat`, `nc`, or a Python standard-library TCP
listener. The pass depends on the behavior below, not on one executable
name.

## Objective

Show that `HttpInterpretationClient` reports `connection_failed` when the
PC server is down and `timeout` when a peer accepts TCP and does not
answer, without retrying.

## Test level and type

Level: integration.

Type: negative.

## Requirements and ClickUp traceability

- ClickUp: [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux).
- Requirement: client error codes in `pi.communication.client`. The client
  makes one attempt and does not raise for these failures.

## Source modules and documentation

- `pi.communication.client.ClientErrorCode`.
- [Communication interface](../../../interfaces/pc-communication.md).

## Preconditions and dependencies

- [TC-COM-001](TC-COM-001.md) so a success baseline exists. This case is
  not how connectivity is proved.
- The operator can stop the PC server.
- The timeout trial needs one silent TCP peer on the VoiceStock PC
  address. Any one of the listeners in the execution section is
  acceptable when it meets every silent-listener rule. Do not record
  `ncat` or `nc` as missing unless that check was actually made.
- If no silent listener can be started, the timeout trial is **BLOCKED**.
  It is not replaced with a shorter product timeout against a closed port.
  A closed port is `connection_failed`, not `timeout`.

## Required hardware and software

- Pi and PC on the cell.
- A free TCP port on `192.168.50.2` for the silent listener. Use 8000 only
  when the VoiceStock server is stopped.
- Either a compatible `ncat` or `nc`, or Python's standard-library
  `socket` module. Record which one was used.

## Preparation

Stop `voicestock-pc-server`. Confirm nothing is listening on the port:

```bash
ss -ltn | grep 8000 || true
```

The `|| true` is so a missing listener is a successful observation.

## Execution

Connection failure, three measured calls on the Pi. No warm-up, because the
failure is the behavior under test. Still record durations.

```bash
VOICESTOCK_PC_URL=http://192.168.50.2:8000 VOICESTOCK_PC_TIMEOUT=10 \
  voicestock-pi-client "agregá dos paquetes de arroz"
```

Repeat three times with the monotonic wrapper from TC-COM-001, changing the
range to three. Expect exit code 1 and envelope error code
`connection_failed`.

Timeout trial. On the PC, accept and do not answer. The listener must:

1. Bind specifically to the VoiceStock PC address, `192.168.50.2`.
2. Accept TCP connections.
3. Send no banner and no HTTP response.
4. Stay up for every measured attempt.
5. Record each accepted connection.
6. Be stopped after the experiment. Record the stop. A missing check does
   not prove the port was released.

`ncat` from nmap is one allowed tool, when that binary exists:

```bash
ncat -l 192.168.50.2 8000 -k
```

If the installed `ncat` or `nc` uses different flags, record the help text
and do not guess. A listener that sends a banner or an HTTP response
invalidates the trial.

A Python standard-library listener is the other allowed tool. Paste the
program that was run. It must bind `192.168.50.2`, accept, record the peer,
and not send. Holding the socket open until the client timeout expires is
enough.

On the Pi, set a short timeout so the session stays short. Five seconds is
the configured budget for this trial, not a product requirement:

```bash
VOICESTOCK_PC_URL=http://192.168.50.2:8000 VOICESTOCK_PC_TIMEOUT=5 \
  voicestock-pi-client "agregá dos paquetes de arroz"
```

Three measured calls. Expect exit 1 and error code `timeout`. The detail
string includes the configured number of seconds. The monotonic duration
must be greater than or equal to the configured timeout. A shorter
duration with code `timeout` fails, because the client would have given
up before its own budget. How far past the timeout the call may run is
**TO BE DEFINED**. The operator aborts at twice the configured timeout;
that abort is a safety stop, not a product limit.

The client must not print a second request. One call, one envelope.

## Observations and evidence

- Three connection-failure bodies and three timeout bodies.
- Durations, kept out of the TC-COM-001 success table.
- Which listener was used, and either its command or its pasted source.
- The accepted-connection log.
- Evidence that the listener was stopped.

## Metrics

| Metric | Rule |
| --- | --- |
| Error code | Exact match to `connection_failed` or `timeout` |
| Attempts per call | 1 |
| Timeout duration | At least the configured timeout. Upper slack **TO BE DEFINED**. |

## Acceptance criteria

1. With nothing listening, three calls exit 1 and the envelope code is
   `connection_failed`.
2. With a silent listener, three calls exit 1 and the envelope code is
   `timeout`.
3. No call retries inside one process invocation. The stdout is a single
   envelope.
4. Durations for the timeout trial are not folded into the success
   statistics of TC-COM-001.

Meeting these four criteria with a Python listener is a functional pass of
this version. It does not rewrite an earlier run that was performed under
procedure version 1.

## Failure conditions

- A closed port reported as `timeout`: **FAILED**.
- A silent listener reported as `connection_failed`: **FAILED**, after
  confirming the listener was actually accepting. If the listener never
  bound, the trial is **BLOCKED**.
- The client hangs past a safety abort of twice the configured timeout:
  stop it, record the abort, and **FAILED**. Twice the timeout is an
  operator safety stop, not a product requirement.

## Recovery and cleanup

Stop the silent listener. Do not leave port 8000 occupied. Do not leave
`VOICESTOCK_PC_TIMEOUT=5` exported in the operator's shell for later cases.
Later cases use 10 seconds unless they say otherwise. Record the check
that shows the port is free. Without that check, cleanup stays
NOT RECORDED.

## Limitations and exclusions

This case does not cover HTTP 415, 413, or a malformed JSON body. Those
paths are specified on the server and covered by automated tests. They can
be added as another case later; they are not required to claim the client
timeout and connection codes. `invalid_envelope` is not generated here.
One printed envelope does not by itself prove how many TCP handshakes the
kernel attempted. A connection log or a packet capture is the evidence for
that count.
