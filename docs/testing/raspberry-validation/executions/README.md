# Execution records

Filed executions:

- [EX-TC-ENV-001-20261027-01.md](EX-TC-ENV-001-20261027-01.md) — **PASSED_PENDING_DOCUMENTATION**. Not a closed pass.
- [EX-TC-GPIO-001-20261027-01.md](EX-TC-GPIO-001-20261027-01.md) — **BLOCKED**. Constructor failed before any button action.
- [EX-TC-GPIO-001-20261027-02.md](EX-TC-GPIO-001-20261027-02.md) — **FAILED**. Nine press and nine release callbacks in the supplied extract. Practice action omitted. Not a closed pass.
- [EX-TC-AUD-001-20261027-01.md](EX-TC-AUD-001-20261027-01.md) — **PASSED_PENDING_DOCUMENTATION**. Logitech G435 seen in 3 of 3 plugged enumerations. Not a closed pass. Not a WAV result.
- [EX-TC-AUD-002-20261103-01.md](EX-TC-AUD-002-20261103-01.md) — **PASSED_PENDING_DOCUMENTATION**. Five measured WAV captures at 16 kHz mono 16-bit on `88a95d5`. Not a closed pass. Review NOT_REVIEWED.
- [INC-EX-TC-AUD-002-20261103-01-01.md](INC-EX-TC-AUD-002-20261103-01-01.md) — observation. Earlier blocked `read()` and blocked worker `close()`, then two fix iterations. Does not fail the five measured runs.

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
