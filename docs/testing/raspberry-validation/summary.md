# Campaign summary

This file is the outline of a later technical report. It is not the report
of a finished experiment. One baseline execution, three GPIO executions,
one microphone-enumeration execution, one WAV-capture execution, two
push-to-talk executions, one maximum-duration execution, and three
access-point executions are recorded, plus one connectivity execution and
one reboot-persistence execution, one text-HTTP execution, one
WAV-transfer execution, one client-error execution, one Pi web
execution, and one real end-to-end execution are recorded.
TC-ENV-001, TC-GPIO-001, TC-AUD-001, TC-AUD-002, TC-PTT-001, TC-PTT-002,
TC-NET-001, TC-NET-002, TC-NET-003, TC-COM-001, TC-COM-002, TC-COM-003, and
TC-WEB-001 are not closed. TC-E2E-002 has one execution at **FAILED**,
with the v0.5.0 decision `ACCEPTED_WITH_KNOWN_LIMITATIONS`. That decision
does not close the case. TC-WEB-002, TC-CON-001, TC-FLOW-001, and
TC-E2E-001 have no measurements. The second access-point execution includes a `hostapd`
diagnostic. That diagnostic is not TC-NET-002. The third access-point
execution is **PASSED_PENDING_DOCUMENTATION**: the technical configuration
assessment is **PASSED**, the evidence archive and the formal review are
still open, and it is not **CLOSED_PASSED**. It does not claim ICMP,
IPv4 isolation, reboot, service recovery, or long-term reliability.

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
TC-E2E-001 has no execution.

The application on `develop` at `c151db2` can also run the real path:
physical push-to-talk, WAV upload, Groq Whisper, `openai/gpt-oss-20b`, Pi
contract validation, one pending operation, confirm or cancel, and idle.
The PC server defaults to the stub. `VOICESTOCK_AUDIO_PIPELINE=groq`
selects that real path. Inventory is not persisted. v0.5.0 does not
include a production accuracy guarantee for speech-to-text or
interpretation, and it does not include more than one operation per
command.
[EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) is the
dedicated record. It is **FAILED** against the written N1 criterion. The
v0.5.0 decision for that test is `ACCEPTED_WITH_KNOWN_LIMITATIONS`. It
does not close the case and does not claim inventory persistence.

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
- [EX-TC-PTT-001-20261103-01](executions/EX-TC-PTT-001-20261103-01.md),
  **FAILED**. Microphone muted. Listening not verified.
- [EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md),
  **FAILED**. WAV contract met and the three measured files were heard.
  Listening table incomplete. GPIO prerequisite unmet. Not closed.
- [EX-TC-PTT-002-20261103-01](executions/EX-TC-PTT-002-20261103-01.md),
  **BLOCKED**. Max-duration observations met. TC-PTT-001 prerequisite
  unmet. Not a product failure of the duration limit. Not closed.
- [EX-TC-NET-001-20261103-01](executions/EX-TC-NET-001-20261103-01.md),
  **FAILED**. The access-point script rejected a connected `wlan0`.
  Not closed. Not a traffic result.
- [EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md),
  **FAILED**. Procedure version 1: the updated Pi script passed state
  detection and failed WPA2 activation. The PC script failed a MAC match.
  A manual `hostapd` session is recorded separately and is not a pass.
  Not closed. Not TC-NET-002.
- [EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 2 on `develop` at
  `485559c`. Technical configuration assessment **PASSED**. Evidence
  archive pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not ICMP,
  isolation, reboot, recovery, or long-term reliability.
- [EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Ten of ten
  measured ICMP replies in each direction. IPv4 isolation only after
  Ethernet was disconnected: no default route and `Network is unreachable`.
  Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not
  TC-NET-003.
- [EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 2. Both machines
  rebooted, confirmed by boot id. Units and `voicestock-client` returned
  without a setup script. IPv4 isolation held. Evidence pending. Review
  NOT_REVIEWED. Not **CLOSED_PASSED**. Not a startup-time result.
- [EX-TC-COM-001-20261103-01](executions/EX-TC-COM-001-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Ten of ten text
  CLI calls exited 0 against the stub on `192.168.50.2:8000`. Evidence
  pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not WAV, speech
  recognition, or interpretation quality. Latency budget **TO BE DEFINED**.
- [EX-TC-COM-002-20261103-01](executions/EX-TC-COM-002-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Five of five WAV
  uploads exited 0. Reported size 59436 matched the local file. Local
  SHA-256 unchanged. Evidence pending. Review NOT_REVIEWED. Not
  **CLOSED_PASSED**. Not a digest of the received body and not
  interpretation.
- [EX-TC-COM-003-20261103-01](executions/EX-TC-COM-003-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Three
  `connection_failed` and three `timeout` outcomes. The silent peer was
  Python, not the `ncat` example. Not a run of procedure version 2.
  Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Cleanup
  of port 8000 was NOT RECORDED.
- [EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md),
  **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Standalone page
  and idle integrated page. Ten of ten health reads HTTP 200. Trial B
  called `pi.runtime.main` because `voicestock-pi` was not installed.
  Runtime exit status NOT RELIABLY RECORDED. Not a button press or a
  pending operation. Review NOT_REVIEWED. Not **CLOSED_PASSED**.
- [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md),
  **FAILED**. Real Groq path on 2026-11-04. N1 created a pending
  operation. Known limitation
  [INC-EX-TC-E2E-002-20261104-01-01](executions/INC-EX-TC-E2E-002-20261104-01-01.md)
  stays **OPEN**. v0.5.0 decision for this test:
  `ACCEPTED_WITH_KNOWN_LIMITATIONS`. Not **CLOSED_PASSED**. Inventory
  persistence not tested. Does not close any other case.

## 3. Scope

Eighteen cases, TC-ENV-001 through TC-E2E-002, listed in the
[README](README.md#what-this-campaign-covers).

## 4. Exclusions

| Topic | Where it has to be validated later |
| --- | --- |
| Speech-to-text accuracy guarantee | A speech-to-text campaign. Not TC-E2E-001 and not [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md). |
| Interpretation accuracy guarantee | [InterpretationService-04](https://app.clickup.com/t/86e3ev2v6). The 2026-11-04 run does not close this task. |
| More than one operation per voice command | Outside v0.5.0. The pipeline rejects a draft that does not contain exactly one operation. No campaign execution records that rejection. |
| Closing PendingOperationWeb-08 | [PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6). [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) is **FAILED** on N1 and does not close the task. |
| SQLite inventory | A persistence campaign, after an executor replaces `ProvisionalOperationExecutor`. Excluded from v0.5.0. |

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
| TC-AUD-002 | [EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | Criteria 1–4 and 6 met on 5/5 measured runs. Criterion 5 stores operator-reported hashes. Criterion 7 not triggered. Not closed. | Commit `88a95d5` on `fix/audio-capture-stream-shutdown` at the time of the run. Later `origin/develop` is `1b81442`, which merges that fix. The measured revision is unchanged. Device `voicestock_mic`. Duration error about −56.2 ms, tolerance **TO BE DEFINED**. `throttled=0x50005` at the later inventory. Review NOT_REVIEWED. WAV files remain on the Pi. |
| TC-PTT-001 | [EX-TC-PTT-001-20261103-01](executions/EX-TC-PTT-001-20261103-01.md); [EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md) | FAILED, then FAILED | Attempt 02: 3 measured WAV files, 1 channel, width 2, 16000 Hz, `RELEASED`, files retained. Operator heard all three. Not closed. | Attempt 01: microphone muted; listening not verified; not a demonstrated software defect. Attempt 02 phrase match and defect columns not separately confirmed. Both ran while [EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md) was **FAILED**. PC not contacted. `develop` at `1b81442`. |
| TC-PTT-002 | [EX-TC-PTT-002-20261103-01](executions/EX-TC-PTT-002-20261103-01.md) | BLOCKED | 3 `MAX_DURATION` and 3 later `RELEASED`. No extra file while held. Format 6/6. Not closed. | Second mechanical press **NOT APPLICABLE**. Header duration 1.984 s versus 2 s. Error −16 ms. Gate **TO BE DEFINED**. Prerequisite TC-PTT-001 remains **FAILED**. Not a product failure of the limit. |
| TC-NET-001 | [EX-TC-NET-001-20261103-01](executions/EX-TC-NET-001-20261103-01.md); [EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md); [EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md) | FAILED, then FAILED, then PASSED_PENDING_DOCUMENTATION | Attempt 03: technical configuration PASSED. Evidence pending. Review NOT_REVIEWED. Not CLOSED_PASSED. | Attempt 01: `10*` matched `100 (connected)`. Attempt 02 failed WPA2 activation and a transient MAC match; its `hostapd` diagnostic is not a pass. Both stay **FAILED** on procedure version 1. Attempt 03 does not regrade them and does not measure ICMP, isolation, reboot, unit recovery, or long-term reliability. Pi commit confirmed `485559c`. Arch SHA **NOT RECORDED**. Ethernet left up. |
| TC-NET-002 | [EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | Connectivity: 10/10 each way. IPv4 isolation after Ethernet removal: no default route, no reply from `1.1.1.1`. Not closed. Review NOT_REVIEWED. | Tool RTT PC to Pi `0.808/4.407/5.545/1.272` ms. Pi to PC `4.101/4.561/5.827/0.512` ms. Printed-line median and sample stdev stay in the execution and do not replace those lines. Loss allowance and latency budget **TO BE DEFINED**. Pi Internet probe was `Network is unreachable`, not a three-packet loss rate. `tailscale0` observed only. Arch SHA **NOT RECORDED**. Not TC-NET-003. |
| TC-NET-003 | [EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | Both reboots confirmed by boot id. 10/10 functional replies in each post-reboot direction that was measured. No Pi default route. Not closed. Review NOT_REVIEWED. | Procedure version 2. No setup script. Arch Internet stayed on `wlo1` at metric 601. Pi Internet probe was `Network is unreachable`, not a three-packet loss rate. Startup time **NOT RECORDED**. Loss allowance **TO BE DEFINED**. Not a latency baseline. PC SHA **NOT RECORDED**. |
| TC-COM-001 | [EX-TC-COM-001-20261103-01](executions/EX-TC-COM-001-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | 10/10 CLI calls exit 0 with the stub text. Mean CLI duration 3092.4 ms. Not closed. Review NOT_REVIEWED. | Both machines reported `develop` `485559c`. Bind `192.168.50.2:8000`; the `ss` peer column is not a bind to every interface. Ten JSON responses were supplied interactively; no transcript file. Warm-up duration NOT RECORDED. Budget **TO BE DEFINED**. Not TC-COM-002. |
| TC-COM-002 | [EX-TC-COM-002-20261103-01](executions/EX-TC-COM-002-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | 5/5 WAV uploads exit 0. Size 59436 and header fields matched. Local SHA-256 unchanged. Not closed. Review NOT_REVIEWED. | Reused the TC-COM-001 server. No new `ss` paste. Mean CLI duration 3136.7 ms. Budget **TO BE DEFINED**. Not a received-body digest. Not TC-COM-003. Source file remains owned by the **FAILED** PTT attempt 02. |
| TC-COM-003 | [EX-TC-COM-003-20261103-01](executions/EX-TC-COM-003-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | 3/3 `connection_failed` and 3/3 `timeout`. Not closed. Review NOT_REVIEWED. | Procedure version 1. Python listener instead of the `ncat` example. Not relabeled as version 2. Scenario A has no TCP-attempt trace. Port cleanup NOT RECORDED. Durations stay out of TC-COM-001. |
| TC-WEB-001 | [EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md) | PASSED_PENDING_DOCUMENTATION | 10/10 health HTTP 200. Standalone 503. Three idle reads and pending HTTP 204. Not closed. Review NOT_REVIEWED. | Mean `curl` duration 86.2 ms. Budget **TO BE DEFINED**. `voicestock-pi` script absent. Exit status NOT RELIABLY RECORDED. Not TC-WEB-002. |
| TC-WEB-002 | none | DESIGNED | | |
| TC-CON-001 | none | DESIGNED | | |
| TC-FLOW-001 | none | DESIGNED | | |
| TC-E2E-001 | none | DESIGNED | | |
| TC-E2E-002 | [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) | FAILED | P1–P5 reported passed. N1 failed criteria 8 and 9. Not closed. | Release decision for this test: `ACCEPTED_WITH_KNOWN_LIMITATIONS`. Incident [INC-EX-TC-E2E-002-20261104-01-01](executions/INC-EX-TC-E2E-002-20261104-01-01.md) is OPEN. Inventory persistence not tested. |

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
confirmed product defect. A later PTT execution does not change this
status.

[EX-TC-PTT-001-20261103-01](executions/EX-TC-PTT-001-20261103-01.md) is
**FAILED** because the listening criterion was not met after the operator
reported a muted microphone. No incident file was opened. The mute is not
recorded as a software defect, and the files are not declared silent.

[EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md) is
**FAILED** because the five-field listening table was not completed and
because the GPIO prerequisite was unmet. The WAV contract observations
remain in that record. No incident file was opened. No HTTP transport was
tested.

[EX-TC-PTT-002-20261103-01](executions/EX-TC-PTT-002-20261103-01.md) is
**BLOCKED** because [EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md)
is still **FAILED**. The three `MAX_DURATION` holds and three later
`RELEASED` holds are in that record. No incident file was opened. The
duration-limit behavior is not recorded as a product failure.

[EX-TC-NET-001-20261103-01](executions/EX-TC-NET-001-20261103-01.md) is
**FAILED** and links
[INC-EX-TC-NET-001-20261103-01-01](executions/INC-EX-TC-NET-001-20261103-01-01.md),
which is **OPEN**. `require_managed` treated `100 (connected)` as
unmanaged because the shell pattern is `10*`. The access point was not
activated. The incident is not closed. Attempt 02 does not rewrite this
result.

[EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md) is
**FAILED** on procedure version 1. The operator reported the Pi
state-detection fix on `develop`. The script passed that check. The board
SHA was not recorded. Activation then failed with `supplicant-timeout`.
After a manual PMF disable, the Arch handshake failed with `IE_DIFFERENT`
because message 3/4 added a WPA-PSK-SHA256 AKM suite. The Broadcom cause
is not identified. The PC script failed because it stored a temporary MAC.
The PC script on `origin/develop` still contains `10*`; that pattern was
not the exit of this run.
[INC-EX-TC-NET-001-20261103-02-01](executions/INC-EX-TC-NET-001-20261103-02-01.md),
[INC-EX-TC-NET-001-20261103-02-02](executions/INC-EX-TC-NET-001-20261103-02-02.md),
and
[INC-EX-TC-NET-001-20261103-02-03](executions/INC-EX-TC-NET-001-20261103-02-03.md)
are **OPEN**. A foreground `hostapd` process authenticated the smartphone
and the Arch USB client. The operator confirmed ICMP only after
`ip addr add 192.168.50.1/24`. That experiment is not a pass and not
TC-NET-002. PMF stayed disabled. Isolation was not proven while Ethernet
was up. The sentence above about `10*` on `origin/develop` describes the
tip inspected for attempt 02. It is not a description of `485559c`.
Attempt 03 does not close these incidents.

[EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md) is
**PASSED_PENDING_DOCUMENTATION** on procedure version 2. The technical
configuration assessment is **PASSED**. Review is NOT_REVIEWED. The Pi
checkout was confirmed as `develop` at `485559c`. The Arch SHA was not
recorded. No incident was opened. The earlier incidents stay **OPEN**.
ICMP, isolation, reboot, and unit recovery were not measured. No
incident file was opened for that execution.

[EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md) is
**PASSED_PENDING_DOCUMENTATION**. No incident file was opened. The
functional IPv4 result does not close TC-NET-001 and does not execute
TC-NET-003.

[EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md) is
**PASSED_PENDING_DOCUMENTATION**. No incident file was opened. It does not
close TC-NET-001 or TC-NET-002.

[EX-TC-COM-001-20261103-01](executions/EX-TC-COM-001-20261103-01.md) is
**PASSED_PENDING_DOCUMENTATION**. No incident file was opened. It does not
close interpretation quality, WAV transfer, or the earlier network cases.

[EX-TC-COM-002-20261103-01](executions/EX-TC-COM-002-20261103-01.md) is
**PASSED_PENDING_DOCUMENTATION**. No incident file was opened. It does not
prove a digest of the received body, and it does not execute TC-COM-003.

[EX-TC-COM-003-20261103-01](executions/EX-TC-COM-003-20261103-01.md) is
**PASSED_PENDING_DOCUMENTATION**. No incident file was opened. The Python
listener is a tooling deviation from procedure version 1, not a product
defect. Port cleanup was not evidenced.

[EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md) is
**PASSED_PENDING_DOCUMENTATION**. No incident file was opened. It does not
press the button or create a pending operation.

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
branch was not merged into `develop` when the captures ran. A later
`origin/develop` commit,
`1b814424b560cafb406ce7069011ba962a5fb82b`, merges the fix. The measured
revision stays `88a95d5`. The capture device was
`voicestock_mic`, an ALSA `plug` device, not the TC-AUD-001 hardware name.
`vcgencmd get_throttled` was `0x50005` at the evidence inventory. The
supply description, several package versions, the operator, and the
session start and end were not recorded. WAV files and raw logs were not
copied into Git. Supplied SHA-256 values are operator-reported. No
inventory-log hash is stored. The duration-error tolerance stays
**TO BE DEFINED**.

For both TC-PTT-001 executions on 3 November 2026: the Pi checkout is
`develop` at `1b814424b560cafb406ce7069011ba962a5fb82b`. `--send-to-pc` was
not used. The input device was `voicestock_mic`. The latest TC-GPIO-001
execution was already **FAILED**, so the formal prerequisite was unmet.
WAV files were not copied into Git. Attempt 02 checksums are
operator-reported. Attempt 01 has no supplied checksums or `wave` fields. The observed
`.wav` paths for both attempts are in those execution records.

For EX-TC-PTT-002-20261103-01: the Pi checkout is the same `develop`
commit, checked clean after the run. `--max-duration` was 2 seconds for
this process only. `--send-to-pc` was not used. The latest TC-PTT-001
execution was already **FAILED**. The second mechanical press was not
possible on the momentary switch. WAV files were not copied into Git.
Checksums are operator-reported.

For EX-TC-NET-001-20261103-01: the Pi checkout is `develop` at
`1b814424b560cafb406ce7069011ba962a5fb82b`. A clean worktree was reported
earlier that day. This failed run did not capture a new `git status`.
Ethernet `eth0` stayed connected for SSH. That default route is a limit
for a later isolation test. It is not the cause of the script error. The
PC script was not run. No transcript hash was supplied. The setup script
was not modified.

For EX-TC-NET-001-20261103-02: the operator reported that the
state-detection fix was on `develop` and that the updated Pi script ran.
`git rev-parse HEAD` was not captured on either machine. Do not treat a
later `develop` tip as that checkout. Ethernet stayed at `192.168.1.100/24`.
The prescribed procedure stopped at script failure; manual PMF, MAC, and
`hostapd` steps are deviations. The configuration-file SHA-256 was
supplied and is in the execution. Other transcripts were not archived.
The scripts were not modified by the documentation of this run. Procedure
version 1 was not rewritten. A version 2 proposal existed when this
execution was recorded and was not applied to it. Adopting version 2
later does not change this paragraph.

For EX-TC-NET-001-20261103-03: the operator confirmed the Pi checkout as
`develop` at `485559c`, with a clean worktree. The porcelain text and the
Arch SHA were not captured. Ethernet stayed at `192.168.1.100/24`. No
transcript hash was supplied. The distribution `hostapd` unit was
observed masked, and deactivating the inactive `voicestock-ap` profile
produced a diagnostic that it was not active. Neither observation is a
failure. Procedure version 1 was not applied to this run, and this run
was not written back into attempts 01 or 02.

For EX-TC-NET-002-20261103-01: the ten-echo stage still had Ethernet
connected. Isolation was recorded only after the cable was removed. The
Pi probe to `1.1.1.1` returned `Network is unreachable` and is not a
three-packet loss rate. `tailscale0` was visible and was not tested.
Session times, the PC SHA, and transcript hashes were not supplied. The
procedure text was not edited. TC-NET-003 was not run in that execution.

For EX-TC-NET-003-20261103-01: procedure version 2 was used. Procedure
version 1 was not run. Ethernet stayed disconnected. Reboot timestamps,
startup time, the PC SHA, and transcript hashes were not supplied. The
ten-echo elapsed times are not boot times. `ipv4.never-default` was not
re-read. A local fallback console was not recorded.

For EX-TC-COM-001-20261103-01: both machines were reported at `develop`
`485559c`. The ten JSON responses were supplied interactively. The
warm-up duration, a raw transcript file, and its SHA-256 were not
supplied. The five persistent-client timings are not part of the
ten-sample mean. TC-COM-002 was not part of that execution.

For EX-TC-COM-002-20261103-01: the server was the one already running from
TC-COM-001. No new `ss` output was supplied. The warm-up duration, a
transcript file, packet captures, and a digest of the received body were
not supplied. The five JSON responses were supplied interactively. The
local SHA-256 was unchanged. TC-COM-003 was not run.

For EX-TC-COM-003-20261103-01: the run followed procedure version 1. The
silent peer was Python. `ncat` was neither shown absent nor executed.
Three accepts were logged for the timeout trial. No packet capture and no
closed-port TCP trace were supplied. The listener stop was not evidenced.
Procedure version 2 was written after this execution.

For EX-TC-WEB-001-20261103-01: trial B called `pi.runtime.main` because
the `voicestock-pi` script was absent. `hatchling.build` could not be
imported. The printed exit value followed an `echo` and is not the runtime
status. The warm-up duration and a fresh git revision were not supplied.
No button was pressed. What remains runnable is in
[readiness.md](readiness.md).

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
- TC-PTT-001 has two executions on 3 November 2026, both **FAILED** and
  not closed. Attempt 01 did not verify listening because the microphone
  was muted. Attempt 02 published three measured contract WAV files that
  the operator heard clearly. Phrase match and the defect columns were not
  separately confirmed. Both attempts ran while TC-GPIO-001 attempt 03 was
  **FAILED**, so another PTT execution is still required after that
  prerequisite is met. PC communication was not tested;
- TC-PTT-002 has one execution on 3 November 2026. The three long holds
  stopped with one `MAX_DURATION` file each, and the three following holds
  printed `RELEASED`. The execution is **BLOCKED**, not closed, because
  TC-PTT-001 is still **FAILED**. A second mechanical press was not
  possible while the switch stayed down. The duration error of −16 ms has
  no acceptance gate yet;
- TC-NET-001 has three executions on 3 November 2026. Attempts 01 and
  02 stay **FAILED** on procedure version 1 and are not closed. Attempt
  01 exited because `10*` matched `100 (connected)`. Attempt 02 did not
  produce the scripted NetworkManager cell. Its `hostapd` diagnostic and
  the operator-confirmed ICMP after a manual address assignment do not
  pass attempt 02 and do not execute TC-NET-002. Attempt 03 is
  **PASSED_PENDING_DOCUMENTATION** on procedure version 2: the repository
  installer on `develop` at `485559c` brought up the cell configuration.
  The technical assessment is **PASSED**. Evidence is still pending.
  Review is NOT_REVIEWED. That result does not measure ICMP, isolation,
  reboot, recovery, or long-term reliability, and it does not close the
  case. Procedure version 1 is preserved as a historical procedure. The
  proposal file remains a historical design artifact under its original
  filename.
  [EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md) is
  **PASSED_PENDING_DOCUMENTATION** on TC-NET-002 procedure version 1.
  Ten of ten measured echoes succeeded in each direction. After Ethernet
  was disconnected, the Pi had no default IPv4 route and `1.1.1.1` was
  unreachable. The loss allowance and the latency budget stay
  **TO BE DEFINED**. Review is NOT_REVIEWED.
  [EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md) is
  **PASSED_PENDING_DOCUMENTATION** on TC-NET-003 procedure version 2.
  Procedure version 1 was not run. The Pi boot id changed from
  `9cd60757-0417-4e4d-bdb8-282907f2f944` to
  `318f958f-a7ca-425d-a21f-ca68d2c70e05`, and the PC boot id changed from
  `8a0df48a-bae1-4844-a09e-72f8ea25437b` to
  `f41c0bc4-6b79-45bb-b24a-c1dd2f429ff4`. The access point and the client
  returned without a setup script. IPv4 isolation held. Startup time was
  not recorded. Review is NOT_REVIEWED. The case is not **CLOSED_PASSED**.
  [EX-TC-COM-001-20261103-01](executions/EX-TC-COM-001-20261103-01.md) is
  **PASSED_PENDING_DOCUMENTATION** on procedure version 1. Ten of ten text
  calls exited 0. The mean CLI duration is 3092.4 ms. The latency budget
  is **TO BE DEFINED**. Review is NOT_REVIEWED. It is not WAV transfer or
  interpretation quality.
  [EX-TC-COM-002-20261103-01](executions/EX-TC-COM-002-20261103-01.md) is
  **PASSED_PENDING_DOCUMENTATION** on procedure version 1. Five of five WAV
  uploads exited 0. Reported size and PCM fields matched the local file.
  The local SHA-256 was unchanged. Review is NOT_REVIEWED. It is not a
  digest of the received HTTP body and not interpretation quality.
  [EX-TC-COM-003-20261103-01](executions/EX-TC-COM-003-20261103-01.md) is
  **PASSED_PENDING_DOCUMENTATION** on procedure version 1. Both expected
  client errors occurred. The silent listener was Python, which is a
  tooling deviation and not a run of procedure version 2. Review is
  NOT_REVIEWED. Port cleanup was not recorded.
  [EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md) is
  **PASSED_PENDING_DOCUMENTATION** on procedure version 1. The standalone
  page and the idle integrated page matched the criteria. The generated
  `voicestock-pi` executable was not started. Review is NOT_REVIEWED.
  [readiness.md](readiness.md) records which later cases are still blocked.
  [ADR-0012](../../decisions/0012-evaluate-hostapd-for-the-voicestock-access-point.md)
  stays **Proposed** and is not renumbered. The accepted `hostapd` process
  is [ADR-0013](../../decisions/0013-run-the-voicestock-access-point-with-hostapd.md).
  Neither record replaces
  [ADR-0010](../../decisions/0010-use-isolated-raspberry-pi-wifi-access-point.md)
  or closes a network execution;
- the default PC audio stub cannot create a pending operation;
- `VOICESTOCK_AUDIO_PIPELINE=groq` can create one validated contract and
  does not persist inventory.
  [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md)
  records that path and is **FAILED** on N1. Its v0.5.0 decision is
  `ACCEPTED_WITH_KNOWN_LIMITATIONS`. Persistence was not tested;
- simulated end-to-end execution stays blocked on a fixture that is
  specified and not implemented. TC-E2E-001 is unchanged and has no
  execution;
- PendingOperationWeb-08 remains open. TC-E2E-002 does not close it.

## 10. Bitácora pointer

The bitácora in [../../bitacora/bitacora.md](../../bitacora/bitacora.md) gets
one entry per testing day, after the last execution of that day, as
described in the [campaign README](README.md#bitácora). It is not updated
after every case.

The campaign was planned for 23 October 2026 and 24 October 2026. Those
dates were scheduling targets. They are not entries in the table below.
EX-TC-ENV-001-20261027-01, EX-TC-GPIO-001-20261027-01,
EX-TC-GPIO-001-20261027-02, and EX-TC-AUD-001-20261027-01 were recorded on
27 October 2026. EX-TC-AUD-002-20261103-01, EX-TC-GPIO-001-20261103-01,
EX-TC-PTT-001-20261103-01, EX-TC-PTT-001-20261103-02, EX-TC-PTT-002-20261103-01,
EX-TC-NET-001-20261103-01, EX-TC-NET-001-20261103-02,
EX-TC-NET-001-20261103-03, EX-TC-NET-002-20261103-01,
EX-TC-NET-003-20261103-01, EX-TC-COM-001-20261103-01,
EX-TC-COM-002-20261103-01, EX-TC-COM-003-20261103-01, and
EX-TC-WEB-001-20261103-01 were recorded on
3 November 2026.
This change does not add a bitácora section for either day. The table stays
empty until a real daily bitácora section exists. Unfinished cases stay
pending or blocked. They are not marked complete to match a planned date.

| Date | Bitácora section | Executions |
| --- | --- | --- |
| | | |
