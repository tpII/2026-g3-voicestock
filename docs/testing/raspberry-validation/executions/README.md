# Execution records

Filed executions:

- [EX-TC-ENV-001-20261027-01.md](EX-TC-ENV-001-20261027-01.md) — **PASSED_PENDING_DOCUMENTATION**. Not a closed pass.
- [EX-TC-GPIO-001-20261027-01.md](EX-TC-GPIO-001-20261027-01.md) — **BLOCKED**. Constructor failed before any button action.
- [EX-TC-GPIO-001-20261027-02.md](EX-TC-GPIO-001-20261027-02.md) — **FAILED**. Nine press and nine release callbacks in the supplied extract. Practice action omitted. Not a closed pass.
- [EX-TC-GPIO-001-20261103-01.md](EX-TC-GPIO-001-20261103-01.md) — **FAILED**. Nine measured press/release pairs, practice excluded, pauses and idles empty. Ctrl+C cleanup not verified. Not a closed fail. Not a product-defect finding.
- [EX-TC-AUD-001-20261027-01.md](EX-TC-AUD-001-20261027-01.md) — **PASSED_PENDING_DOCUMENTATION**. Logitech G435 seen in 3 of 3 plugged enumerations. Not a closed pass. Not a WAV result.
- [EX-TC-AUD-002-20261103-01.md](EX-TC-AUD-002-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Five measured WAV captures at 16 kHz mono 16-bit on `88a95d5`. Not a closed pass. Review NOT_REVIEWED.
- [INC-EX-TC-AUD-002-20261103-01-01.md](INC-EX-TC-AUD-002-20261103-01-01.md) — observation. Earlier blocked `read()` and blocked worker `close()`, then two fix iterations. Does not fail the five measured runs.
- [EX-TC-PTT-001-20261103-01.md](EX-TC-PTT-001-20261103-01.md) — **FAILED**. Four button captures with the printed WAV format. Microphone muted. Listening not verified. Not a closed fail.
- [EX-TC-PTT-001-20261103-02.md](EX-TC-PTT-001-20261103-02.md) — **FAILED**. Three measured WAV files at the contract, heard by the operator. Phrase-match and defect columns not separately confirmed. GPIO prerequisite unmet. Not a closed fail.
- [EX-TC-PTT-002-20261103-01.md](EX-TC-PTT-002-20261103-01.md) — **BLOCKED**. Three `MAX_DURATION` captures and three later `RELEASED` captures. Second mechanical press not applicable. TC-PTT-001 prerequisite unmet. Not a product failure of the duration limit. Not closed.
- [EX-TC-NET-001-20261103-01.md](EX-TC-NET-001-20261103-01.md) — **FAILED**. Access-point script rejected connected `wlan0`. Not a closed fail. Not a traffic result.
- [INC-EX-TC-NET-001-20261103-01-01.md](INC-EX-TC-NET-001-20261103-01-01.md) — **OPEN**. Historical result unchanged: `10*` matched `100 (connected)` on the Pi script. Attempt 02 does not close this incident.
- [EX-TC-NET-001-20261103-02.md](EX-TC-NET-001-20261103-02.md) — **FAILED**. Updated Pi script passed state detection and failed WPA2 activation. PC script failed a transient MAC match. `hostapd` diagnostic authenticated two stations and is not a pass. Not closed. Not TC-NET-002.
- [EX-TC-NET-001-20261103-03.md](EX-TC-NET-001-20261103-03.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 2. Technical configuration assessment **PASSED**. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not ICMP, isolation, reboot, recovery, or long-term reliability. Does not close attempts 01 or 02.
- [EX-TC-NET-002-20261103-01.md](EX-TC-NET-002-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. 10/10 ICMP each way. IPv4 isolation after Ethernet removal. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not TC-NET-003.
- [EX-TC-NET-003-20261103-01.md](EX-TC-NET-003-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 2. Both reboots confirmed by boot id. AP and client returned without a setup script. IPv4 isolation held. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not a startup-time result.
- [EX-TC-COM-001-20261103-01.md](EX-TC-COM-001-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Ten text CLI calls to the stub on `192.168.50.2:8000`. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not TC-COM-002 or TC-COM-003.
- [EX-TC-COM-002-20261103-01.md](EX-TC-COM-002-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Five WAV uploads. Size and header matched. Local SHA-256 unchanged. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not a received-body digest. Not TC-COM-003.
- [EX-TC-COM-003-20261103-01.md](EX-TC-COM-003-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Three closed-port errors and three silent-peer timeouts. Python listener, not `ncat`. Not a run of procedure version 2. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Port cleanup NOT RECORDED.
- [EX-TC-WEB-001-20261103-01.md](EX-TC-WEB-001-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Procedure version 1. Standalone web server and idle integrated runtime. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not TC-WEB-002. Runtime exit status NOT RELIABLY RECORDED.
- [INC-EX-TC-NET-001-20261103-02-01.md](INC-EX-TC-NET-001-20261103-02-01.md) — **OPEN**. NetworkManager WPA2 activation timeout, then Beacon/handshake RSN mismatch. Fails the case.
- [INC-EX-TC-NET-001-20261103-02-02.md](INC-EX-TC-NET-001-20261103-02-02.md) — **OPEN**. PC profile `mac-address` was set from a temporary interface MAC.
- [INC-EX-TC-NET-001-20261103-02-03.md](INC-EX-TC-NET-001-20261103-02-03.md) — **OPEN**. Observation. PC script still uses `10*` for unmanaged detection. Not the exit of attempt 02.

Add one Markdown file per run:

```text
EX-<TEST-ID>-<YYYYMMDD>-<NN>.md
```

Copy [../templates/execution-template.md](../templates/execution-template.md).
Use the next `<NN>` for that test id and calendar date. A retest is a new
file. Do not replace the previous one.

Incident files for that run may sit next to it:

```text
INC-EX-<TEST-ID>-<YYYYMMDD>-<NN>-<MM>.md
```

Copy [../templates/incident-template.md](../templates/incident-template.md).
