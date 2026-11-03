# Remaining-case readiness

This note records what can be run next. It does not change any execution
status and it does not approve a case. Product behavior was read from
`origin/develop` at `485559c04a71ce634170372c78a7dc1bc4e1dbc7`. The campaign
fixtures live on this documentation branch. That commit of `develop` does
not contain `docs/testing/raspberry-validation/fixtures/`.

A module on `develop` is not a passed test. A **PASSED_PENDING_DOCUMENTATION**
result is not **CLOSED_PASSED**.

## PC contract fixture, not implemented

`create_pc_app(..., audio_handler=...)` exists. `voicestock-pc-server`
still defaults to `describe_received_audio`. That stub does not return an
operation contract. No CLI flag selects another handler.

A later change, outside this documentation commit, needs a separate PC
entry point that:

1. Uses the existing PC communication server.
2. Keeps WAV validation, including `audio/wav`, the 4 MiB limit, and
   `read_wav`.
3. Returns one deterministic version-1 operation contract.
4. Includes the synthetic `recognized_text` from
   [service-success-payload.json](fixtures/service-success-payload.json).
5. Does not call speech-to-text or a language model.
6. Records the received size and SHA-256 outside git.
7. Binds `192.168.50.2:8000` when that is the address under test.
8. Starts only when the operator chooses that entry point.
9. Leaves `voicestock-pc-server` on the current stub.

Until that entry point exists, success trials that need a contract stay
blocked. Pointing them at the stub and treating the rejection as a pending
operation is not allowed. The test plan already states this under
[fixture requirements](test-plan.md#fixture-requirements).

## Pi console script

On the Pi used for TC-WEB-001, `.venv/bin/voicestock-pi-web` existed.
`.venv/bin/voicestock-pi` did not. `python -m pip install -e .` failed
because `hatchling.build` could not be imported. Trial B called
`pi.runtime.main` directly. That workaround does not count as a test of
the generated executable. Cases whose procedure names `voicestock-pi`
need either that script or an explicit command deviation.

## Prerequisite results that stay as written

| Case | Latest campaign result | Effect on later cases |
| --- | --- | --- |
| [TC-GPIO-001](test-cases/TC-GPIO-001.md) | Three executions. Latest [EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md) is **FAILED**: measured presses met, cleanup not verified. Not closed. | Not a passed GPIO baseline. |
| [TC-PTT-001](test-cases/TC-PTT-001.md) | Both executions **FAILED**. Attempt 02 met the WAV file contract and left the listening table incomplete. The GPIO prerequisite was unmet. Not closed. | [TC-FLOW-001](test-cases/TC-FLOW-001.md) and [TC-WEB-002](test-cases/TC-WEB-002.md) require a PTT result that is not **FAILED** or **BLOCKED**. That gate is not met. |
| [TC-PTT-002](test-cases/TC-PTT-002.md) | [EX-TC-PTT-002-20261103-01](executions/EX-TC-PTT-002-20261103-01.md) is **BLOCKED** because TC-PTT-001 is unmet. Functional max-duration notes in that record are not a pass. | Not a passed capture-limit result. |
| [TC-COM-002](test-cases/TC-COM-002.md) | **PASSED_PENDING_DOCUMENTATION**, not closed. | WAV transport to the stub is evidenced. It is not contract generation. |
| [TC-WEB-001](test-cases/TC-WEB-001.md) | [EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md), **PASSED_PENDING_DOCUMENTATION**, not closed. | Idle page and health are evidenced. The generated `voicestock-pi` script was not the process under test. |

## Readiness matrix

| Case | Code on `develop` | Fixture | Hardware seen in this campaign | Environment | Preconditions | Executed | Readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [TC-CON-001](test-cases/TC-CON-001.md) | `OperationValidator` and `PcResponseInterpreter` are in the tree. | The three JSON files are on this branch: catalog, `contract-add-stock.json`, `service-success-payload.json`. They are not in `develop` at `485559c`. | Pi only. No button and no PC process. | Importing `pi` worked during TC-WEB-001. The three files still have to be placed on the Pi. TC-ENV-001 is **PASSED_PENDING_DOCUMENTATION**, not closed. | No PC fixture. | No | **Partially ready.** Runnable after the three files are provisioned on the Pi and their digests are recorded there. |
| [TC-FLOW-001](test-cases/TC-FLOW-001.md) trials A and C | Runtime and the shipped stub exist. | Not required. Trial A uses `describe_received_audio`. Trial C uses no server. | Button, G435, and the cell were used in other cases. Those cases are not passes. | `voicestock-pi` script missing unless the operator repeats the direct `main` call and records it. | Written gate: TC-PTT-001 is not **FAILED**. Both PTT executions are **FAILED**. TC-COM-002 and TC-WEB-001 are not **FAILED**. | No | **Blocked by the written PTT-001 gate.** The stub and the stopped-server setup themselves do not need the contract fixture. |
| TC-FLOW-001 trial B | `create_pc_app` can take a handler. No separate entry point ships it. | Missing. The specification payload is only a JSON file. | Same capture path, not a passed PTT result. | Same script gap. | Same PTT gate, plus the fixture. | No | **Blocked.** Do not substitute the stub. |
| [TC-WEB-002](test-cases/TC-WEB-002.md) | Page and confirm/cancel routes exist. | Missing PC contract entry point. | Needs a press that produces a pending card. TC-PTT-001 is **FAILED**. | Same script gap. Browser on the cell worked for TC-WEB-001. | TC-WEB-001 is not **FAILED**. TC-PTT-001 is **FAILED**. Fixture absent. | No | **Blocked.** |
| [TC-E2E-001](test-cases/TC-E2E-001.md) | The same runtime. No production STT stand-in beyond the missing fixture. | Missing, and the procedure also wants a server-side hash of each received WAV. | Needs the capture path and the page. | Same script gap. | TC-FLOW-001 trial B and TC-WEB-002 have no executions. | No | **Blocked.** A pass would still not be real speech-to-text or inventory persistence. |

## Suggested sequence

1. Keep the open reviews open. Do not mark GPIO, PTT, COM, NET, or WEB-001
   **CLOSED_PASSED** from this note.
2. Copy the three campaign JSON files to the Pi, record `sha256sum` there,
   and run TC-CON-001. That case does not wait for the PC fixture.
3. Before FLOW, WEB-002, or E2E, either produce a TC-PTT-001 execution that
   is not **FAILED**, or leave those cases unstarted. Attempt 02 is not
   that execution.
4. Install `hatchling` in the Pi environment, or otherwise create
   `.venv/bin/voicestock-pi`, before treating the generated command as
   tested. Record the command that was actually used if the direct call
   remains the only option.
5. Implement the separate PC contract entry point. Then run TC-FLOW-001
   trial B, TC-WEB-002, and TC-E2E-001, in that order. Trials A and C of
   TC-FLOW-001 can be scheduled once the PTT gate is met, without waiting
   for that entry point.
6. Each of those runs needs its own execution record. This file is not one.
