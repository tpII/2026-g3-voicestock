# Campaign summary

This file is the outline of a later technical report. It is not the report
of a finished experiment. One baseline execution, three GPIO executions,
one microphone-enumeration execution, and one WAV-capture execution are
recorded. TC-ENV-001, TC-GPIO-001, TC-AUD-001, and TC-AUD-002 are not
closed. The other cases have no measurements.

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
- [EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md),
  **FAILED**. Nine measured pairs, practice excluded, quiet intervals
  empty. Cleanup after Ctrl+C not verified. Not a confirmed `close()`
  defect. Not closed.
- [EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Enumeration only. Not a WAV result.
- [EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Five measured WAV captures. Not closed.
  Review NOT_REVIEWED.

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
| TC-GPIO-001 | [EX-TC-GPIO-001-20261027-01](executions/EX-TC-GPIO-001-20261027-01.md); [EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md); [EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md) | BLOCKED, then FAILED, then FAILED | Attempt 03: 9 measured presses and 9 releases, practice excluded, 3 pauses and 3 idles empty. Cleanup not verified. Not closed. | Attempt 01 stopped before `READY` (`OSError: [Errno 22] Invalid argument`). Attempt 02 omitted the practice action. Pause and idle intervals on attempt 02: not measured. Attempt 03 does not rewrite those results. Logs remain on the Pi. |
| TC-AUD-001 | [EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md) | PASSED_PENDING_DOCUMENTATION | Criteria 1–4 met. Not closed. | G435 in 3 of 3 plugged lists, absent while unplugged. Query: `G435 Wireless Gaming Headset: USB Audio (hw:2,0)`. Default rate 48000 Hz. Detection latency NOT MEASURED. Logs remain on the Pi. |
| TC-AUD-002 | [EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | Criteria 1–4 and 6 met on 5/5 measured runs. Criterion 5 stores operator-reported hashes. Criterion 7 not triggered. Not closed. | Commit `88a95d5` on `fix/audio-capture-stream-shutdown`, not merged to `develop`. Device `voicestock_mic`. Duration error about −56.2 ms, tolerance **TO BE DEFINED**. `throttled=0x50005`. Review NOT_REVIEWED. WAV files remain on the Pi. |
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

Callback hold for
[EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md).
Practice is excluded. Each value is the printed release timestamp minus
the printed press timestamp. It is not GPIO edge latency. Edge latency is
**NOT MEASURED**. One decimal place is the display rounding. The
six-decimal second rows in that record are the source. No hold limit is
defined. This row is not an acceptance result, and it does not close
criterion 3.

| Metric | n | Unit | Mean | Median | Stdev | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Callback hold, attempt 03 | 9 | ms | 392.3 | 210.7 | 291.9 | 157.8 | 931.3 |

Formal TC-AUD-002 durations for
[EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md).
The warm-up is excluded. The source is the raw six-decimal second table in
that record. Display here is milliseconds to three decimal places, because
one decimal place prints the hold and duration-error standard deviations
as 0.0. No duration-error limit is defined. These rows are not a closed
pass.

| Metric | n | Unit | Mean | Median | Stdev | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Start | 5 | ms | 30.915 | 30.708 | 0.606 | 30.324 | 31.599 |
| Hold | 5 | ms | 3000.218 | 3000.208 | 0.027 | 3000.203 | 3000.266 |
| Stop | 5 | ms | 2.892 | 2.904 | 0.083 | 2.800 | 3.011 |
| WAV header duration | 5 | ms | 2944.000 | 2944.000 | 0.000 | 2944.000 | 2944.000 |
| Duration error | 5 | ms | -56.218 | -56.208 | 0.027 | -56.266 | -56.203 |

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

[EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md) is
**FAILED** because cleanup after Ctrl+C was not verified. The measured
press, release, pause, and idle observations are in that record. No
incident file was opened. The missing cleanup lines are not recorded as a
confirmed product defect.

[EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md) opened
no incident.

[EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md) links
[INC-EX-TC-AUD-002-20261103-01-01](executions/INC-EX-TC-AUD-002-20261103-01-01.md).
That incident records a blocked PortAudio `read()` before the callback
fix, then a worker blocked in `stream.close()` after the first fix, then
the second lifecycle correction on `022e2a6` and `88a95d5`. It is an
observation about earlier revisions. It does not fail the five measured
runs. It does not name a single proven PortAudio or queue defect.
`throttled=0x50005` is not identified as the cause of those blocks.

The remaining cases have not been executed. This section does not mean the
product has no defects.

## 8. Deviations from the specification

For EX-TC-ENV-001-20261027-01: the Pi checkout is `develop` at
`3aee132b4769f418bbe71efccaf8ed5f501e02c1`, not this documentation branch.
Session start, end, and operator were not recorded. The raw command
transcript was not archived. The PC was not inspected. Details are in the
execution record.

For the two GPIO executions on 27 October 2026: the Pi checkout is the
same `develop` commit, `3aee132b4769f418bbe71efccaf8ed5f501e02c1`. Session
start, end, operator, and timezone were not recorded. The raw logs were
not copied into Git. Their SHA-256 values are operator-reported.

After the blocked attempt, `lgpio` 0.2.2.0 was installed into the Pi
`.venv`. That change is later than the environment baseline. No repository
dependency manifest was modified. The install is not recorded here as a
step that a fresh checkout reproduces.

For EX-TC-GPIO-001-20261103-01: the Pi checkout is `develop` at
`1b814424b560cafb406ce7069011ba962a5fb82b`, with a clean worktree. The pin
factory printed `LGPIOFactory`. Package versions, the operator, and the
session start and end were not recorded. The raw log was not copied into
Git. Its SHA-256 is operator-reported. Cleanup after Ctrl+C was not
verified.

For EX-TC-AUD-001-20261027-01: the Pi checkout is the same `develop`
commit. USB port, hub, operator, and worktree status were not recorded.
The three raw logs were not copied into Git. Their SHA-256 values are
operator-reported.

For EX-TC-AUD-002-20261103-01: the Pi checkout is
`fix/audio-capture-stream-shutdown` at
`88a95d5754c72f419adb3461348161fa09f7ce8d`, with a clean worktree. That
branch was not merged into `develop`. The capture device was
`voicestock_mic`, an ALSA `plug` device, not the TC-AUD-001 hardware name.
`vcgencmd get_throttled` was `0x50005` at the evidence inventory. The
supply description, several package versions, the operator, and the
session start and end were not recorded. WAV files and raw logs were not
copied into Git. Supplied SHA-256 values are operator-reported. No
inventory-log hash is stored. The duration-error tolerance stays
**TO BE DEFINED**.

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
- TC-GPIO-001 attempt 03, on 3 November 2026, recorded the practice pair,
  nine measured press/release pairs, and empty pause and idle checks.
  Cleanup after Ctrl+C was not verified, so the execution is **FAILED**
  and is not closed. That attempt does not change the result of attempt
  01 or attempt 02;
- whether `lgpio` belongs in the project dependency configuration is still
  open. The Pi virtual environment was changed outside the repository
  manifests;
- the environment baseline does not show a USB microphone, a VoiceStock
  access point, or PC connectivity;
- TC-AUD-001 later enumerated a Logitech G435 on the USB receiver in 3 of
  3 plugged listings and recorded the name query
  `G435 Wireless Gaming Headset: USB Audio (hw:2,0)`. That execution does
  not record a WAV, a 16 kHz contract, or acoustic quality;
- TC-AUD-002 has one execution on 3 November 2026. Five of five measured
  runs published a WAV at 1 channel, sample width 2, and 16000 Hz. The
  execution is not closed. Review is NOT_REVIEWED. Speech intelligibility
  and quantitative audio quality were not evaluated. The code under test
  was still on `fix/audio-capture-stream-shutdown`;
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
27 October 2026. EX-TC-AUD-002-20261103-01 and
EX-TC-GPIO-001-20261103-01 were recorded on 3 November 2026.
This change does not add a bitácora section for either day. The table stays
empty until a real daily bitácora section exists. Unfinished cases stay
pending or blocked. They are not marked complete to match a planned date.

| Date | Bitácora section | Executions |
| --- | --- | --- |
| | | |
