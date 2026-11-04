# Raspberry Pi hardware and integration validation

This campaign specifies how to show that the Raspberry Pi subsystem runs on
the real board and that its components integrate. It is a test specification.
Measurements live in execution records, not in this README.

Automated tests, mocks, and earlier development sessions are not evidence
for these cases. Passing a software test does not show that a GPIO pin, a
USB microphone, or the VoiceStock Wi-Fi cell works.

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
| Web server and operator UI | [TC-WEB-001](test-cases/TC-WEB-001.md) |
| Operation contract on the Pi | [TC-CON-001](test-cases/TC-CON-001.md) |
| Integrated error handling | [TC-FLOW-001](test-cases/TC-FLOW-001.md) |
| Real hardware end-to-end | [TC-E2E-002](test-cases/TC-E2E-002.md) |

The order and the reason each stage exists are in the
[test plan](test-plan.md). TC-E2E-001 and TC-WEB-002 were withdrawn before
execution. That withdrawal is recorded in the test plan and is not a pass.
How to measure is in the
[measurement methodology](measurement-methodology.md). ClickUp mapping is
the [traceability matrix](traceability-matrix.md). The report skeleton is
the [campaign summary](summary.md).

## What a later campaign must cover

This campaign does not validate:

- speech-to-text quality or accuracy;
- language-model interpretation quality;
- SQLite inventory persistence;
- a production end-to-end path from a real spoken command to a stock change.

The application on `develop` at `c151db2` can run a real audio path. The
default PC server remains the stub. `VOICESTOCK_AUDIO_PIPELINE=groq`
transcribes with Groq Whisper, interprets with `openai/gpt-oss-20b`, and
returns one version-1 contract. The Pi validates that contract and assigns
`product_id`. Confirm and cancel return the cycle to idle.
`ProvisionalOperationExecutor` does not persist inventory. That capability
is not, by itself, a campaign result.
[EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) records
one hardware run. It is **FAILED** on N1 and is not **CLOSED_PASSED**.
Its v0.5.0 decision is `ACCEPTED_WITH_KNOWN_LIMITATIONS`. A conversation
or a demonstration is not **CLOSED_PASSED**.

For the v0.5.0 claim, the intended path is physical push-to-talk capture,
WAV upload, real speech-to-text, real language-model interpretation,
contract validation, one pending operation, confirm or cancel, and idle.
That release claim excludes inventory persistence, a production accuracy
guarantee for speech-to-text, a production accuracy guarantee for
interpretation, and more than one operation in a single command. The
pipeline reports `unsupported_command` when the draft does not contain
exactly one operation. This campaign has no execution of that report.

[PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6) expects a real
end-to-end flow that includes real speech-to-text and interpretation.
TC-E2E-001 would have replaced that PC-side processing with a deterministic
contract. It was never executed and is withdrawn from this campaign. It
does not close PendingOperationWeb-08. It had no ClickUp task. Do not
invent an identifier.

[InterpretationService-04](https://app.clickup.com/t/86e3ev2v6) is listed in
the matrix so the exclusion stays visible. No case in this campaign closes
it.

## Status

Campaign status: **IN_PROGRESS**.

The procedures are **DESIGNED**. [TC-ENV-001](test-cases/TC-ENV-001.md) has
one execution, [EX-TC-ENV-001-20261027-01](executions/EX-TC-ENV-001-20261027-01.md),
at **PASSED_PENDING_DOCUMENTATION**. [TC-GPIO-001](test-cases/TC-GPIO-001.md)
has [EX-TC-GPIO-001-20261027-01](executions/EX-TC-GPIO-001-20261027-01.md)
(**BLOCKED**) and
[EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md)
(**FAILED**), and
[EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md)
(**FAILED**; measured GPIO events met, cleanup not verified), and
[EX-TC-GPIO-001-20261104-01](executions/EX-TC-GPIO-001-20261104-01.md)
(**PASSED_PENDING_DOCUMENTATION**; latest; technical result PASSED;
cleanup evidenced; quiet-interval durations not instrumented; not
**CLOSED_PASSED**). The three earlier GPIO results are unchanged.
[TC-AUD-001](test-cases/TC-AUD-001.md) has
[EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md)
at **PASSED_PENDING_DOCUMENTATION**. [TC-AUD-002](test-cases/TC-AUD-002.md)
has [EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION**. [TC-PTT-001](test-cases/TC-PTT-001.md)
has [EX-TC-PTT-001-20261103-01](executions/EX-TC-PTT-001-20261103-01.md)
and [EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md),
both **FAILED** and not closed.
[EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md)
is the latest execution, at **PASSED_PENDING_DOCUMENTATION**. It is not
**CLOSED_PASSED**. [TC-PTT-002](test-cases/TC-PTT-002.md)
has [EX-TC-PTT-002-20261103-01](executions/EX-TC-PTT-002-20261103-01.md)
at **BLOCKED**, and
[EX-TC-PTT-002-20261104-01](executions/EX-TC-PTT-002-20261104-01.md)
at **PASSED_PENDING_DOCUMENTATION**. The earlier result stays **BLOCKED**.
The two-second limit is a test parameter. [TC-NET-001](test-cases/TC-NET-001.md) has
[EX-TC-NET-001-20261103-01](executions/EX-TC-NET-001-20261103-01.md)
and [EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md),
both **FAILED** on procedure version 1, and
[EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md)
at **PASSED_PENDING_DOCUMENTATION** on procedure version 2. The technical
configuration assessment is **PASSED**. Evidence and review are still
open, so attempt 03 is not **CLOSED_PASSED** and does not claim ICMP,
isolation, reboot, recovery, or long-term reliability. Attempt 02's
`hostapd` diagnostic is not a pass. Attempt 03 does not close the case.
[TC-NET-002](test-cases/TC-NET-002.md) has
[EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION**. It is not **CLOSED_PASSED**.
[TC-NET-003](test-cases/TC-NET-003.md) has
[EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION** on procedure version 2. It is not
**CLOSED_PASSED**. Procedure version 1 of that case was not run.
[TC-COM-001](test-cases/TC-COM-001.md) has
[EX-TC-COM-001-20261103-01](executions/EX-TC-COM-001-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION**. It is not **CLOSED_PASSED**.
[TC-COM-002](test-cases/TC-COM-002.md) has
[EX-TC-COM-002-20261103-01](executions/EX-TC-COM-002-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION**. It is not **CLOSED_PASSED**.
[TC-COM-003](test-cases/TC-COM-003.md) has
[EX-TC-COM-003-20261103-01](executions/EX-TC-COM-003-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION** on procedure version 1. The silent
peer was a Python listener, not the `ncat` example. Procedure version 2
was written afterward and is not applied to that run. It is not
**CLOSED_PASSED**.
[TC-WEB-001](test-cases/TC-WEB-001.md) has
[EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md)
at **PASSED_PENDING_DOCUMENTATION**. It is not **CLOSED_PASSED**.
[TC-E2E-002](test-cases/TC-E2E-002.md) has
[EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md)
at **FAILED**. N1 did not meet the written rejection criterion. The
v0.5.0 decision for that test is `ACCEPTED_WITH_KNOWN_LIMITATIONS`. That
decision does not close the case and does not close any other case.
[TC-CON-001](test-cases/TC-CON-001.md) has
[EX-TC-CON-001-20261104-01](executions/EX-TC-CON-001-20261104-01.md)
at **PASSED_PENDING_DOCUMENTATION**. The technical result is **PASSED**.
Review is NOT_REVIEWED, so it is not **CLOSED_PASSED**. It does not close
the N1 incident.
What is still open is in [readiness.md](readiness.md). None of these cases is
**CLOSED_PASSED**. TC-FLOW-001 has no execution. TC-WEB-002 and TC-E2E-001
were withdrawn without an execution. Allowed statuses, and the rule that forbids `CLOSED_PASSED`
without evidence, are in the [test plan](test-plan.md#status-model).

## Layout

```text
docs/testing/raspberry-validation/
├── README.md
├── test-plan.md
├── traceability-matrix.md
├── measurement-methodology.md
├── summary.md
├── readiness.md
├── fixtures/
├── test-cases/
├── templates/
├── executions/
├── evidence/
└── results/
```

`executions/` holds the records that have been filed. `evidence/` and
`results/` still have no closed-run sheet. Their READMEs are the retention
rules.
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
8. Continue with the next case. Do not append the project bitácora from
   this step. The bitácora is written once, at the end of the testing day,
   as described in [Bitácora](#bitácora).

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

The project bitácora is updated once at the end of each testing day, not
after each test. During the day the operator does this for every case, in
order:

1. Execute the test.
2. Capture the measurements and the evidence.
3. Write that run's execution record.
4. Compare the observations with the acceptance criteria.
5. Update [summary.md](summary.md) and [traceability-matrix.md](traceability-matrix.md)
   from that record.
6. Continue with the next test.

At the end of the day, append one consolidated section to
[../../bitacora/bitacora.md](../../bitacora/bitacora.md), in Spanish, in the
same shape as the existing entries. The section uses the actual date and
the people who were present. It includes:

- the tests performed that day;
- a summary of the outcomes;
- the relevant measurements and findings, by link to the execution records
  rather than by copying the raw tables;
- incidents and blockers;
- links to the complete execution records;
- decisions and the next steps.

The planned testing days are 23 October 2026 and 24 October 2026. Those
dates are targets for scheduling. They are not evidence that a test ran,
and they are not headings to add before the day has happened. Do not create
a future bitácora entry. Do not backdate a result. Do not invent a
measurement.

If cases remain unfinished after 24 October 2026, leave them pending or
blocked in the campaign summary. Do not mark them complete to match the
planned days.

One daily entry points at the execution records of that day. It does not
replace them.

## Implementation notes that affect execution

These notes come from the current source. They are not physical results.

1. `voicestock-pc-server` defaults to `describe_received_audio` in
   `pc.main` when `VOICESTOCK_AUDIO_PIPELINE` is unset or `stub`. That
   handler returns a `ServiceResult` whose payload describes the WAV. It
   does not return a `ContractPayload`. The Pi then rejects the body and
   returns to idle with the contract-rejection message. The same limit is
   already stated in the
   [operation workflow](../../architecture/pending-operation-flow.md#information-flow).
   The default server is therefore usable for transport checks and for the
   rejection trial of [TC-FLOW-001](test-cases/TC-FLOW-001.md). It cannot
   create a pending operation.
   `VOICESTOCK_AUDIO_PIPELINE=groq` selects the real pipeline: Groq Whisper
   for speech-to-text, `openai/gpt-oss-20b` for the structured draft, then
   `map_draft` and the catalog check. The Pi validates the resulting
   contract. That mode is not a deterministic fixture.
   [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md)
   records one run and is **FAILED** on N1. It is not **CLOSED_PASSED**.
   Its v0.5.0 decision is `ACCEPTED_WITH_KNOWN_LIMITATIONS`.
   The deterministic fixture is not an active v0.5.0 requirement. TC-WEB-002
   and TC-E2E-001 were withdrawn without an execution. TC-FLOW-001 procedure
   version 2 tests error handling and does not need that fixture. Confirm
   still uses `ProvisionalOperationExecutor` and does not persist inventory.
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
- [hostapd evaluation note](hostapd-evaluation.md) (diagnostic only; not a passed case)
- [PC audio pipeline](../../setup/pc-audio-pipeline.md)
- [Audio and interpretation integration](../../architecture/audio-interpretation-integration.md)
- [ADR-0010](../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md)
- [ADR-0012](../../decisions/0012-evaluate-hostapd-for-the-voicestock-access-point.md) (**Proposed** evaluation; not renumbered)
- [ADR-0013](../../decisions/0013-run-the-voicestock-access-point-with-hostapd.md) (**Accepted** `hostapd` process; not a closed campaign result)
- [Web setup](../../setup/pi-web.md)
- [Pending-operation workflow](../../architecture/pending-operation-flow.md)
- [Audio transport](../../interfaces/pc-audio-communication.md)
- [Operation contract](../../interfaces/operation-contract.md)
- [Pending-operation HTTP API](../../interfaces/pending-operation-web-api.md)
- [Pending-operation page](../../interfaces/pending-operation-web-ui.md)
