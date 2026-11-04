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

## Deterministic contract fixture, withdrawn as an active requirement

`create_pc_app(..., audio_handler=...)` exists. `voicestock-pc-server`
defaults to `describe_received_audio`. That stub does not return an
operation contract. `VOICESTOCK_AUDIO_PIPELINE=groq` selects Groq Whisper
for speech-to-text and `openai/gpt-oss-20b` for one structured draft. The
Pi then validates the contract. That mode does not persist inventory.

An earlier draft of this campaign required a separate PC entry point that
returned [service-success-payload.json](fixtures/service-success-payload.json)
for every accepted WAV. That entry point was never implemented. TC-E2E-001,
TC-WEB-002, and TC-FLOW-001 procedure version 1 trial B depended on it.
Those three items were never executed. They are withdrawn from the active
v0.5.0 campaign. See
[Withdrawn from the active v0.5.0 campaign](test-plan.md#withdrawn-from-the-active-v050-campaign).
Withdrawing them is not a pass and does not change
[EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md). That
run stays **FAILED** on N1. Its v0.5.0 decision stays
`ACCEPTED_WITH_KNOWN_LIMITATIONS`.

The active campaign does not require the deterministic fixture.
[TC-FLOW-001](test-cases/TC-FLOW-001.md) procedure version 2 uses the stub,
a closed port, and a temporary hold server. It does not use `groq`.

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
| [TC-PTT-001](test-cases/TC-PTT-001.md) | Three executions. Latest [EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md) is **PASSED_PENDING_DOCUMENTATION**. Attempts 01 and 02 stay **FAILED**. | The written PTT status gate for TC-FLOW-001 procedure version 2 is met. That case is not executed. |
| [TC-PTT-002](test-cases/TC-PTT-002.md) | Two executions. Latest [EX-TC-PTT-002-20261104-01](executions/EX-TC-PTT-002-20261104-01.md) is **PASSED_PENDING_DOCUMENTATION**. Attempt 01 stays **BLOCKED**. Second press **NOT APPLICABLE**. | Max-duration behavior is evidenced for this test setting. It is not closed and it is not the product default. |
| [TC-COM-002](test-cases/TC-COM-002.md) | **PASSED_PENDING_DOCUMENTATION**, not closed. | WAV transport to the stub is evidenced. It is not contract generation. |
| [TC-WEB-001](test-cases/TC-WEB-001.md) | [EX-TC-WEB-001-20261103-01](executions/EX-TC-WEB-001-20261103-01.md), **PASSED_PENDING_DOCUMENTATION**, not closed. | Idle page and health are evidenced. The generated `voicestock-pi` script was not the process under test. |

## Readiness matrix

| Case | Code on `develop` | Fixture | Hardware seen in this campaign | Environment | Preconditions | Executed | Readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [TC-CON-001](test-cases/TC-CON-001.md) | `OperationValidator` and `PcResponseInterpreter` are in the tree. | The three JSON files are on this branch. On the Pi `develop` checkout they were absent and were extracted to an external directory. Contents were reported unmodified. | Pi only. No button and no PC request from the script. | [EX-TC-CON-001-20261104-01](executions/EX-TC-CON-001-20261104-01.md) ran on Python 3.13.5 at `c151db2`. | No PC fixture. | Yes | **PASSED_PENDING_DOCUMENTATION.** Technical result **PASSED**. Review NOT_REVIEWED. External hashes were not recomputed in this workspace. Not **CLOSED_PASSED**. |
| [TC-FLOW-001](test-cases/TC-FLOW-001.md) | Runtime, default stub, and a closed port are available. Scenario C needs a temporary hold server written in the procedure, stored outside git. Groq must stay off. | Not required. Procedure version 1 trial B is withdrawn and was not executed. | Button, G435, and the cell were used in other cases. | `voicestock-pi` script missing unless the operator repeats the direct `main` call and records it. | Written gate: TC-PTT-001, TC-COM-002, and TC-WEB-001 are not **FAILED** or **BLOCKED**. [EX-TC-PTT-001-20261104-01](executions/EX-TC-PTT-001-20261104-01.md) meets that wording. The two earlier PTT executions stay **FAILED**. | No | **Not executed.** The PTT status gate is met. The generated `voicestock-pi` script gap remains. Not a fixture case. Not a pass. |

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
   and 02 stay **FAILED**. TC-FLOW-001 procedure version 2 is no longer
   blocked by the PTT status gate. It is not executed. Do not point it at
   `groq`.
4. Install `hatchling` in the Pi environment, or otherwise create
   `.venv/bin/voicestock-pi`, before treating the generated command as
   tested. Record the command that was actually used if the direct call
   remains the only option.
5. TC-FLOW-001 procedure version 2 can be scheduled without a
   deterministic fixture. Scenario A starts the default stub. Scenario B
   leaves the PC port closed. Scenario C uses the hold server in the
   procedure. Do not treat this note as an execution.
6. Each run needs its own execution record. This file is not one.
