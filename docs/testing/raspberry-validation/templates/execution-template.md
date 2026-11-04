# EX-<TEST-ID>-<YYYYMMDD>-<NN>

- Execution id:
- Test case: link to `../test-cases/<TEST-ID>.md`
- Procedure version:
- Status: IN_PROGRESS
- Review status: NOT_REVIEWED

## Session

- Start (ISO 8601 with numeric offset):
- End (ISO 8601 with numeric offset):
- Timezone name:
- Operator:
- Other participants:

## Revision under test

- Machine:
- Repository path:
- `git rev-parse HEAD`:
- `git status --porcelain` (empty or the deviation):
- Specification commit this case was written for, if different:

## Hardware inventory

The machine under test. For TC-ENV-001 this is the Raspberry Pi. A later
case that uses the PC fills the PC block as well. If the PC was not
available for a Pi-only case, write `NOT COLLECTED — PC NOT AVAILABLE` in
the PC block. That token does not document connectivity. A case whose
procedure needs the PC cannot leave the token in place: collect the PC
facts before the first measured sample.

- Model:
- Board revision, if printed:
- Power supply: or UNKNOWN
- Button wiring (BCM pin, physical pin, ground): or not used
- Microphone and USB port: or not used
- Cables and hubs:
- Other devices attached:

## PC inventory

- Status: collected in this execution, copied from a TC-ENV-001 record, or
  `NOT COLLECTED — PC NOT AVAILABLE`
- OS, kernel, Python, git SHA, and worktree:
- VoiceStock interface name, when this case uses the cell:

## Operating system and runtime

- `PRETTY_NAME` and `VERSION_ID`:
- `uname -srvmo`:
- `python --version`:
- `voicestock` version and commit reported by the install:
- `gpiozero`, `sounddevice`, `httpx`, `fastapi`, `uvicorn`:
- `vcgencmd get_throttled`: or command absent

## Configuration

- Interface names:
- Addresses:
- `VOICESTOCK_PC_URL`:
- `VOICESTOCK_PC_TIMEOUT`:
- `VOICESTOCK_PC_HOST` and `VOICESTOCK_PC_PORT`:
- `VOICESTOCK_WEB_HOST` and `VOICESTOCK_WEB_PORT`:
- `--pin`, `--bounce-time`, `--input-device`, `--max-duration`:
- Catalog path and SHA-256:
- Fixture or stub: `voicestock-pc-server` or the contract fixture

## Procedure

- Deviations from the case, or "none":
- Warm-up performed: yes or no

## Measurements

Raw samples (one row each). Durations in seconds with six decimal places.
Warm-up rows are labeled `warmup`. Failures and timeouts stay in this table
and are excluded from the duration summary.

| Sample | Kind | Outcome | Duration_s | Notes |
| --- | --- | --- | --- | --- |
| | | | | |

Summary, computed by [the methodology](../measurement-methodology.md):

| Metric | n | Unit | Mean | Median | Stdev | Min | Max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| | | | | | | | |

Metrics the case marks **NOT MEASURED** are listed here with that token.
They are not left blank.

## Evidence

| Evidence id | Description | SHA-256 | Location |
| --- | --- | --- | --- |
| | | | |

Locations are repository-relative paths or external URIs. Raw audio and
video use an external URI. Secrets are redacted.

## Expected and observed behavior

| Step | Expected | Observed |
| --- | --- | --- |
| | | |

## Criteria

| Criterion id | Result (pass/fail/blocked/not measured) | Evidence id |
| --- | --- | --- |
| | | |

## Incidents

- None, or links to `INC-<execution-id>-<nn>` records stored beside this
  file or under `../evidence/`.

## Deviations

- None, or a description and why the run continued.

## Final assessment

- Status after this run:
- Rationale, citing criterion ids:

## Review

- Reviewer:
- Date:
- Review notes:
- Review status: NOT_REVIEWED, REVIEWED, or CHANGES_REQUESTED

A review that requests changes does not delete this file. The next attempt
is a new execution id.

Finishing this record does not by itself update
`docs/bitacora/bitacora.md`. The bitácora gets one consolidated entry at
the end of the testing day, linking every execution from that day. See the
[campaign README](../README.md#bitácora).
