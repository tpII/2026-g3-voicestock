# Remaining-case readiness

This note records what can be run next. It does not change any execution
status and it does not approve a case. Historical executions keep the
commits written in those records. The latest checkout named by those
records is `develop` at `485559c04a71ce634170372c78a7dc1bc4e1dbc7`. This
documentation branch now also contains `develop` at `c151db2`. That commit
adds the selectable Groq audio pipeline. It does not add an execution, and
it does not change a recorded result. The campaign fixtures live on this
documentation branch. `485559c` does not contain
`docs/testing/raspberry-validation/fixtures/`.

A module on `develop`, including the Groq pipeline, is not a passed test.
A **PASSED_PENDING_DOCUMENTATION** result is not **CLOSED_PASSED**.

## PC contract fixture, not implemented

`create_pc_app(..., audio_handler=...)` exists. `voicestock-pc-server`
defaults to `describe_received_audio`. That stub does not return an
operation contract. `VOICESTOCK_AUDIO_PIPELINE=groq` selects Groq Whisper
for speech-to-text and `openai/gpt-oss-20b` for one structured draft. The
Pi then validates the contract. That mode does not persist inventory.
There is still no separate entry point for the deterministic campaign
fixture. `groq` is not that fixture: it calls a transcription API and a
language model, and the contract depends on the WAV. Do not use it to pass
TC-WEB-002, TC-FLOW-001 trial B, or TC-E2E-001.
[EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) records
one real-path run. It is **FAILED** on N1 and does not accept those three
cases.

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
| [TC-GPIO-001](test-cases/TC-GPIO-001.md) | Four executions. Latest [EX-TC-GPIO-001-20261104-01](executions/EX-TC-GPIO-001-20261104-01.md) is **PASSED_PENDING_DOCUMENTATION**: 9 and 9 measured, cleanup evidenced, quiet intervals not instrumented, review NOT_REVIEWED. Attempts 01–03 stay **BLOCKED**, **FAILED**, and **FAILED**. | Cited by [EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md). The two November 3 PTT executions stay **FAILED**. |
| [TC-PTT-001](test-cases/TC-PTT-001.md) | Three executions. Latest [EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md) is **PASSED_PENDING_DOCUMENTATION**. Attempts 01 and 02 stay **FAILED**. | The written PTT status gate for FLOW trials A and C, and for WEB-002's button path, is met. Those cases are not executed. Trial B, WEB-002, and TC-E2E-001 stay blocked on the missing deterministic fixture. |
| [TC-PTT-002](test-cases/TC-PTT-002.md) | Two executions. Latest [EX-TC-PTT-002-20261104-01](executions/EX-TC-PTT-002-20261104-01.md) is **PASSED_PENDING_DOCUMENTATION**. Attempt 01 stays **BLOCKED**. Second press **NOT APPLICABLE**. | Max-duration behavior is evidenced for this test setting. It is not closed and it is not the product default. |
| [TC-COM-002](test-cases/TC-COM-002.md) | **PASSED_PENDING_DOCUMENTATION**, not closed. | WAV transport to the stub is evidenced. It is not contract generation. |
| [TC-WEB-001](test-cases/TC-WEB-001.md) | [EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md), **PASSED_PENDING_DOCUMENTATION**, not closed. | Idle page and health are evidenced. The generated `voicestock-pi` script was not the process under test. |

## Readiness matrix

| Case | Code on `develop` | Fixture | Hardware seen in this campaign | Environment | Preconditions | Executed | Readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [TC-CON-001](test-cases/TC-CON-001.md) | `OperationValidator` and `PcResponseInterpreter` are in the tree. | The three JSON files are on this branch. On the Pi `develop` checkout they were absent and were extracted to an external directory. Contents were reported unmodified. | Pi only. No button and no PC request from the script. | [EX-TC-CON-001-20261104-01](executions/EX-TC-CON-001-20261104-01.md) ran on Python 3.13.5 at `c151db2`. | No PC fixture. | Yes | **PASSED_PENDING_DOCUMENTATION.** Technical result **PASSED**. Review NOT_REVIEWED. External hashes were not recomputed in this workspace. Not **CLOSED_PASSED**. |
| [TC-FLOW-001](test-cases/TC-FLOW-001.md) trials A and C | Runtime and the default stub exist. Trial A must start the server as stub, not `groq`. Trial C uses no server. | Not required. Trial A uses `describe_received_audio`. | Button, G435, and the cell were used in other cases. | `voicestock-pi` script missing unless the operator repeats the direct `main` call and records it. | Written gate: TC-PTT-001, TC-COM-002, and TC-WEB-001 are not **FAILED** or **BLOCKED**. [EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md) meets that wording. The two earlier PTT executions stay **FAILED**. | No | **Not executed.** The PTT status gate is met. The generated `voicestock-pi` script gap remains. Not a fixture case. |
| TC-FLOW-001 trial B | `create_pc_app` can take a handler. `groq` exists on `c151db2` and is not this fixture. No separate deterministic entry point ships the fixture. | Missing. The specification payload is only a JSON file. | The capture path now has a non-failed PTT execution. | Same script gap. | PTT status gate met. Fixture absent. | No | **Blocked by the missing fixture.** Do not substitute the stub or `groq`. [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) does not replace this trial. |
| [TC-WEB-002](test-cases/TC-WEB-002.md) | Page and confirm/cancel routes exist. The Groq pipeline can create a contract and is not the required fixture. | Missing PC contract entry point. | The button path is evidenced by the latest PTT execution. | Same script gap. Browser on the cell worked for TC-WEB-001. | TC-WEB-001 is not **FAILED**. The latest TC-PTT-001 execution is not **FAILED**. Fixture absent. | No | **Blocked by the missing fixture.** Not executed. Do not substitute the stub or `groq`. |
| [TC-E2E-001](test-cases/TC-E2E-001.md) | The same runtime. `groq` is a real pipeline, not the deterministic stand-in this case requires. | Missing, and the procedure also wants a server-side hash of each received WAV. | Needs the capture path and the page. The capture path has a non-failed PTT execution. | Same script gap. | TC-FLOW-001 trial B and TC-WEB-002 have no executions. Fixture absent. | No | **Blocked by the missing fixture and by those unexecuted trials.** The case stays simulated. [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) is a separate real-path run, **FAILED** on N1, and does not replace this case. |

## Suggested sequence

1. Keep the open reviews open. Do not mark GPIO, PTT, COM, NET, or WEB-001
   **CLOSED_PASSED** from this note.
2. TC-CON-001 has
   [EX-TC-CON-001-20261104-01](executions/EX-TC-CON-001-20261104-01.md).
   The technical result is **PASSED**. Review is still open, so the case
   is not **CLOSED_PASSED**. It does not close the N1 incident.
3. TC-PTT-001 now has
   [EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md).
   The technical result is **PASSED**. Review is still open. Attempts 01
   and 02 stay **FAILED**. FLOW trials A and C are no longer blocked by
   the PTT status gate. Trial B, TC-WEB-002, and TC-E2E-001 stay blocked
   on the missing deterministic fixture. Do not point them at `groq`.
4. Install `hatchling` in the Pi environment, or otherwise create
   `.venv/bin/voicestock-pi`, before treating the generated command as
   tested. Record the command that was actually used if the direct call
   remains the only option.
5. Implement the separate PC contract entry point. Then run TC-FLOW-001
   trial B, TC-WEB-002, and TC-E2E-001, in that order. Do not point those
   cases at `VOICESTOCK_AUDIO_PIPELINE=groq`. Trials A and C of
   TC-FLOW-001 can be scheduled once the PTT gate is met, without waiting
   for that entry point. Trial A starts the default stub.
6. Each of those runs needs its own execution record. This file is not one.
