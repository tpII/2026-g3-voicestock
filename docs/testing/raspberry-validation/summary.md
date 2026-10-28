# Campaign summary

This file is the outline of a later technical report. It is not the report
of a finished experiment. One baseline execution, two GPIO executions, and
one microphone-enumeration execution are recorded. TC-ENV-001, TC-GPIO-001,
and TC-AUD-001 are not closed. The other cases have no measurements.

Campaign status: **IN_PROGRESS**.

Specification revision: the git commit that contains this file on
`docs/raspberry-validation-campaign`. Record that commit in each execution.
Do not treat a commit SHA written here in advance as a result.

## 1. Objective

Determine whether the Raspberry Pi subsystem of VoiceStock operates on the
project hardware and whether its components integrate across GPIO, audio,
the isolated Wi-Fi cell, HTTP, contract validation, the pending-operation
cycle, and the operator page.

The simulated end-to-end pass replaces PC speech-to-text and interpretation
with a deterministic contract. It is not a production end-to-end pass.

## 2. Method

- Cases and order: [test-plan.md](test-plan.md).
- Measurement rules: [measurement-methodology.md](measurement-methodology.md).
- Traceability: [traceability-matrix.md](traceability-matrix.md).
- Each run: one execution record under [executions/](executions/).

Recorded executions:

- [EX-TC-ENV-001-20261027-01](executions/EX-TC-ENV-001-20261027-01.md),
  **PASSED_PENDING_DOCUMENTATION**.
- [EX-TC-GPIO-001-20261027-01](executions/EX-TC-GPIO-001-20261027-01.md),
  **BLOCKED**.
- [EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md),
  **FAILED**. The failure is the omitted practice action. The supplied
  extract still contains nine `PRESSED` lines and nine `RELEASED` lines.
- [EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Enumeration only. Not a WAV result.

## 3. Scope

Seventeen cases, TC-ENV-001 through TC-E2E-001, listed in the
[README](README.md#what-this-campaign-covers).

## 4. Exclusions

| Topic | Where it has to be validated later |
| --- | --- |
| Speech-to-text quality | A speech-to-text campaign. Not TC-E2E-001. |
| Interpretation quality | [InterpretationService-04](https://app.clickup.com/t/86e3ev2v6). |
| Real spoken command through STT and the model, then the web flow | [PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6). |
| SQLite inventory | A persistence campaign, after an executor replaces `ProvisionalOperationExecutor`. |

## 5. Environment

Filled from [EX-TC-ENV-001-20261027-01](executions/EX-TC-ENV-001-20261027-01.md).
The PC column is empty because that execution recorded
`NOT COLLECTED — PC NOT AVAILABLE`. That is not PC connectivity. A case
that uses the PC still has to record the PC before measuring. The Pi
commit below is the checkout on the board (`develop`), not the
documentation branch.

| Item | Raspberry Pi | PC |
| --- | --- | --- |
| Model | Raspberry Pi 3 Model B Rev 1.2 | |
| OS | Raspbian GNU/Linux 13 (Trixie), 13.6 | |
| Kernel | `6.18.50+rpt-rpi-v7`, `armv7l` | |
| Python | 3.13.5 | |
| VoiceStock commit | `3aee132b4769f418bbe71efccaf8ed5f501e02c1` on `develop` | |
| Worktree clean | yes | |
| Microphone | Baseline: no USB microphone reported. [EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md) later recorded a Logitech G435 Wireless Gaming Headset through its USB receiver. USB port and hub were not recorded in that execution. | |
| Button pin (BCM) | BCM 17, physical header pin 11, GND physical header pin 9. Recorded in the GPIO executions, not in the environment baseline. | |
| Supply | model NOT RECORDED; GPIO header with Dupont cables; `vcgencmd get_throttled` `0x50000` (15 of 15). Under load: NOT TESTED | |
| VoiceStock interface | not configured. Observed `wlan0` `192.168.1.38/24`, gateway `192.168.1.1` | |

## 6. Results

| Test | Executions | Status | Measured success | Notes |
| --- | --- | --- | --- | --- |
| TC-ENV-001 | [EX-TC-ENV-001-20261027-01](executions/EX-TC-ENV-001-20261027-01.md) | PASSED_PENDING_DOCUMENTATION | Criteria 1–5 met. Not closed. | Pi baseline only. No raw transcript. Review NOT_REVIEWED. `get_throttled` `0x50000` on 15 readings. |
| TC-GPIO-001 | [EX-TC-GPIO-001-20261027-01](executions/EX-TC-GPIO-001-20261027-01.md); [EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md) | BLOCKED, then FAILED | Attempt 02 extract: 9 `PRESSED` and 9 `RELEASED`, alternating, no missing pair. Not closed. | Attempt 01 stopped before `READY` (`OSError: [Errno 22] Invalid argument`). Attempt 02 omitted the practice action. Pause and idle intervals: not measured. Logs remain on the Pi. |
| TC-AUD-001 | [EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md) | PASSED_PENDING_DOCUMENTATION | Criteria 1–4 met. Not closed. | G435 in 3 of 3 plugged lists, absent while unplugged. Query: `G435 Wireless Gaming Headset: USB Audio (hw:2,0)`. Default rate 48000 Hz. Detection latency NOT MEASURED. Logs remain on the Pi. |
| TC-AUD-002 | none | DESIGNED | | |
| TC-PTT-001 | none | DESIGNED | | |
| TC-PTT-002 | none | DESIGNED | | |
| TC-NET-001 | none | DESIGNED | | |
| TC-NET-002 | none | DESIGNED | | |
| TC-NET-003 | none | DESIGNED | | |
| TC-COM-001 | none | DESIGNED | | |
| TC-COM-002 | none | DESIGNED | | |
| TC-COM-003 | none | DESIGNED | | |
| TC-WEB-001 | none | DESIGNED | | |
| TC-WEB-002 | none | DESIGNED | | |
| TC-CON-001 | none | DESIGNED | | |
| TC-FLOW-001 | none | DESIGNED | | |
| TC-E2E-001 | none | DESIGNED | | |

Callback hold for
[EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md).
Each value is the printed release timestamp minus the printed press
timestamp. It is not GPIO edge latency. Edge latency is **NOT MEASURED**.
The source is the callback extract in that record. The raw log is not in
Git. Display rounding is one decimal place, in milliseconds.

| Metric | n | Unit | Mean | Median | Stdev | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Callback hold, attempt 02 | 9 | ms | 515.4 | 239.9 | 478.1 | 112.3 | 1361.8 |

No hold limit is defined. This row is not an acceptance result.

## 7. Incidents

[EX-TC-ENV-001-20261027-01](executions/EX-TC-ENV-001-20261027-01.md) opened
no incident. `vcgencmd get_throttled` was `0x50000` on 15 readings. The
notes describe historical undervoltage and throttling flags, and no active
undervoltage or throttling flags. That value is not classified here as a
product failure. Power under load was not tested.

[EX-TC-GPIO-001-20261027-01](executions/EX-TC-GPIO-001-20261027-01.md) is
**BLOCKED**, not an incident of a button defect. Initialization failed in
the native GPIO backend before any press. No incident file was opened.

[EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md) is
**FAILED** because the written practice action was omitted. No incident
file was opened.

[EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md) opened
no incident. The remaining cases have not been executed. This section
does not mean the product has no defects.

## 8. Deviations from the specification

For EX-TC-ENV-001-20261027-01: the Pi checkout is `develop` at
`3aee132b4769f418bbe71efccaf8ed5f501e02c1`, not this documentation branch.
Session start, end, and operator were not recorded. The raw command
transcript was not archived. The PC was not inspected. Details are in the
execution record.

For both GPIO executions: the Pi checkout is the same `develop` commit,
`3aee132b4769f418bbe71efccaf8ed5f501e02c1`. Session start, end, operator,
and timezone were not recorded. The raw logs were not copied into Git.
Their SHA-256 values are operator-reported.

After the blocked attempt, `lgpio` 0.2.2.0 was installed into the Pi
`.venv`. That change is later than the environment baseline. No repository
dependency manifest was modified. The install is not recorded here as a
step that a fresh checkout reproduces.

For EX-TC-AUD-001-20261027-01: the Pi checkout is the same `develop`
commit. USB port, hub, operator, and worktree status were not recorded.
The three raw logs were not copied into Git. Their SHA-256 values are
operator-reported.

## 9. Conclusions

Do not write a conclusion, a pass claim, or a recommendation that the
hardware works until the closure checklist in the
[test plan](test-plan.md#closure-checklist-for-closed_passed) has been
applied to the cases the conclusion cites.

What this summary can say now:

- the procedures are specified;
- TC-ENV-001 has one Pi baseline execution and is not closed;
- TC-GPIO-001 attempt 01 did not initialize `PushToTalkButton`;
- TC-GPIO-001 attempt 02 printed nine press callbacks and nine release
  callbacks and did not meet the written procedure, because the practice
  action was omitted and the pause and idle intervals were not measured;
- whether `lgpio` belongs in the project dependency configuration is still
  open. The Pi virtual environment was changed outside the repository
  manifests;
- the environment baseline does not show a USB microphone, a VoiceStock
  access point, or PC connectivity;
- TC-AUD-001 later enumerated a Logitech G435 on the USB receiver in 3 of
  3 plugged listings and recorded the name query
  `G435 Wireless Gaming Headset: USB Audio (hw:2,0)`. That execution does
  not record a WAV, a 16 kHz contract, or acoustic quality;
- the default PC audio stub cannot create a pending operation;
- simulated end-to-end execution is blocked on a fixture that is specified
  and not implemented;
- PendingOperationWeb-08 remains open regardless of TC-E2E-001.

## 10. Bitácora pointer

The bitácora in [../../bitacora/bitacora.md](../../bitacora/bitacora.md) gets
one entry per testing day, after the last execution of that day, as
described in the [campaign README](README.md#bitácora). It is not updated
after every case.

The campaign was planned for 23 October 2026 and 24 October 2026. Those
dates were scheduling targets. They are not entries in the table below.
EX-TC-ENV-001-20261027-01, EX-TC-GPIO-001-20261027-01,
EX-TC-GPIO-001-20261027-02, and EX-TC-AUD-001-20261027-01 were recorded on
27 October 2026. This change does not add a bitácora section for that day
or for any other day. The table stays empty until a real daily bitácora
section exists. Unfinished cases stay pending or blocked. They are not
marked complete to match a planned date.

| Date | Bitácora section | Executions |
| --- | --- | --- |
| | | |
