# Raspberry Pi hardware and integration validation

This campaign specifies how to show that the Raspberry Pi subsystem runs on
the real board and that its components integrate. It is a test specification.
It does not contain measurements, logs, or execution results.

No test in this campaign has been executed. Automated tests, mocks, and
earlier development sessions are not evidence for these cases. Passing a
software test does not show that a GPIO pin, a USB microphone, or the
VoiceStock Wi-Fi cell works.

The language of this campaign follows the Raspberry Pi setup and architecture
documents it cites. Session notes in the project log stay in Spanish; see
[Bitácora](#bitácora).

## What this campaign covers

| Area | Cases |
| --- | --- |
| Environment and hardware baseline | [TC-ENV-001](test-cases/TC-ENV-001.md) |
| Physical GPIO button | [TC-GPIO-001](test-cases/TC-GPIO-001.md) |
| USB microphone and WAV capture | [TC-AUD-001](test-cases/TC-AUD-001.md), [TC-AUD-002](test-cases/TC-AUD-002.md) |
| Integrated push-to-talk | [TC-PTT-001](test-cases/TC-PTT-001.md), [TC-PTT-002](test-cases/TC-PTT-002.md) |
| Isolated Wi-Fi access point and PC link | [TC-NET-001](test-cases/TC-NET-001.md), [TC-NET-002](test-cases/TC-NET-002.md), [TC-NET-003](test-cases/TC-NET-003.md) |
| HTTP client and WAV transport | [TC-COM-001](test-cases/TC-COM-001.md), [TC-COM-002](test-cases/TC-COM-002.md), [TC-COM-003](test-cases/TC-COM-003.md) |
| Web server and operator UI | [TC-WEB-001](test-cases/TC-WEB-001.md), [TC-WEB-002](test-cases/TC-WEB-002.md) |
| Operation contract on the Pi | [TC-CON-001](test-cases/TC-CON-001.md) |
| Pending-operation cycle | [TC-FLOW-001](test-cases/TC-FLOW-001.md) |
| Simulated end-to-end | [TC-E2E-001](test-cases/TC-E2E-001.md) |

The order, the reason each stage exists, and the simulated end-to-end
strategy are in the [test plan](test-plan.md). How to measure is in the
[measurement methodology](measurement-methodology.md). ClickUp mapping is
the [traceability matrix](traceability-matrix.md). The report skeleton is
the [campaign summary](summary.md).

## What a later campaign must cover

This campaign does not validate:

- speech-to-text quality or accuracy;
- language-model interpretation quality;
- SQLite inventory persistence;
- a production end-to-end path from a real spoken command to a stock change.

[PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6) expects a real
end-to-end flow that includes real speech-to-text and interpretation.
[TC-E2E-001](test-cases/TC-E2E-001.md) replaces that PC-side processing with
a deterministic contract. A pass of TC-E2E-001 does not close
PendingOperationWeb-08. TC-E2E-001 has no ClickUp task yet. Its traceability
is **PENDING CLICKUP TASK CREATION**. Do not invent an identifier.

[InterpretationService-04](https://app.clickup.com/t/86e3ev2v6) is listed in
the matrix so the exclusion stays visible. No case in this campaign closes
it.

## Status

Campaign status: **DESIGNED**.

Every case is **DESIGNED** and unexecuted. Allowed statuses, and the rule
that forbids `CLOSED_PASSED` without evidence, are in the
[test plan](test-plan.md#status-model).

## Layout

```text
docs/testing/raspberry-validation/
├── README.md
├── test-plan.md
├── traceability-matrix.md
├── measurement-methodology.md
├── summary.md
├── fixtures/
├── test-cases/
├── templates/
├── executions/
├── evidence/
└── results/
```

`executions/`, `evidence/`, and `results/` are reserved for future runs.
Their READMEs are the retention rules. They do not hold results yet.
`fixtures/` holds specification inputs (the campaign catalog and contract
examples). Those files are not recordings and they are not evidence that a
test ran.

## How to execute a case

1. Read the case, the [test plan](test-plan.md), and the
   [measurement methodology](measurement-methodology.md).
2. Confirm the dependencies in the [execution order](test-plan.md#execution-order)
   are satisfied, or mark the run **BLOCKED**.
3. Copy [templates/execution-template.md](templates/execution-template.md)
   to `executions/EX-<test-id>-<YYYYMMDD>-<nn>.md`.
   Example: `executions/EX-TC-ENV-001-20261023-01.md`.
4. Use a new execution id for every run, including a retest. Do not edit an
   earlier execution into a later result.
5. Store or reference evidence as [evidence/README.md](evidence/README.md)
   requires. Record the assessment only after the predetermined criteria
   are compared with the observations.
6. Open an incident with
   [templates/incident-template.md](templates/incident-template.md) when a
   criterion fails or the procedure cannot be followed.
7. Update [summary.md](summary.md) and [traceability-matrix.md](traceability-matrix.md)
   only when an execution record exists. Until then the summary stays at
   "not executed".

A case file is the specification. An execution file is one run of that
specification.

## Evidence retention

- Commit execution records, incident records, redacted text logs, checksums,
  and short command transcripts.
- Do not commit raw WAV files, video, packet captures, private credentials,
  or long untrimmed logs.
- Prefer an external archive for those artifacts and store the URI plus a
  SHA-256 in the execution record.
- Redact Wi-Fi passphrases and API keys before saving a transcript. The
  prototype passphrase already lives in `scripts/voicestock-network.conf`;
  do not copy it into this campaign.
- Do not use `nmcli` output that prints `802-11-wireless-security.psk`.

## Bitácora

Do not add a bitácora session for a test that has not been run, and do not
backdate one. After a real session, append a dated section to
[../../bitacora/bitacora.md](../../bitacora/bitacora.md) in Spanish, in the
same shape as the existing entries. The session must include:

- the date of the work, not the date this campaign was written;
- the participants who were actually present;
- the test ids that were executed;
- a short summary of observations;
- incidents;
- relative links to the complete execution records;
- decisions and the next case.

The bitácora entry points at the execution record. It does not replace it
and it does not copy the measurements.

## Implementation notes that affect execution

These notes come from the current source. They are not physical results.

1. `voicestock-pc-server` always uses `describe_received_audio` in
   `pc.main`. That handler returns a `ServiceResult` whose payload describes
   the WAV. It does not return a `ContractPayload`. The Pi then rejects the
   body and returns to idle with the contract-rejection message. The same
   limit is already stated in the
   [operation workflow](../../architecture/pending-operation-flow.md#information-flow).
   The default server is therefore usable for transport checks and for the
   rejection trial of [TC-FLOW-001](test-cases/TC-FLOW-001.md). It cannot
   create a pending operation. [TC-WEB-002](test-cases/TC-WEB-002.md),
   the success trials of TC-FLOW-001, and [TC-E2E-001](test-cases/TC-E2E-001.md)
   need the fixture described in the
   [test plan](test-plan.md#simulated-end-to-end). That fixture is not
   implemented.
2. `WebServerSettings` in `src/pi/web/settings.py` says the default host is
   the Ethernet segment. The address `192.168.50.1` matches the Wi-Fi plan
   in [local network setup](../../setup/local-network.md) and
   [ADR-0010](../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md).
   This campaign follows the Wi-Fi documents. The docstring was not changed.
3. `SoundDeviceBackend.read` discards the PortAudio overflow flag. The
   application will not report a discontinuity by itself.
4. `voicestock-pi` deletes each WAV after the send unless
   `--keep-recordings` is set. `voicestock-pi-ptt` keeps the WAV unless
   `--delete-after-send` is set. Evidence procedures name the flag they need.
5. Confirming an operation uses `ProvisionalOperationExecutor`, which
   reports success and does not write inventory. A confirmed page is not
   evidence of a stock change.
6. The operator page polls `GET /api/v1/system-status` every 1000 ms
   (`POLL_INTERVAL_MS` in `src/pi/web/static/app.js`). That lag is not an
   API response time and not a button-to-pending latency.
7. The existing manual procedure in
   [push-to-talk setup](../../setup/push-to-talk.md) states that it has not
   been run on the project board. This campaign does not mark it done.
8. `tests/integration/test_pi_pc_audio_roundtrip.py` checks the stub in
   process. It is not a substitute for [TC-COM-002](test-cases/TC-COM-002.md).

## Related documents

- [Integrated runtime](../../setup/pi-runtime.md)
- [Push-to-talk setup](../../setup/push-to-talk.md)
- [Local network](../../setup/local-network.md)
- [Web setup](../../setup/pi-web.md)
- [Pending-operation workflow](../../architecture/pending-operation-flow.md)
- [Audio transport](../../interfaces/pc-audio-communication.md)
- [Operation contract](../../interfaces/operation-contract.md)
- [Pending-operation HTTP API](../../interfaces/pending-operation-web-api.md)
- [Pending-operation page](../../interfaces/pending-operation-web-ui.md)
