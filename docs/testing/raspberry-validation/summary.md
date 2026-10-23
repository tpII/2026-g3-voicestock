# Campaign summary

This file is the outline of a later technical report. It is not the report
of a finished experiment. Every quantitative cell is empty on purpose.

Campaign status: **DESIGNED**.

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

No run has been performed for this campaign.

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

Fill this table from TC-ENV-001. Leave it blank until that execution exists.

| Item | Raspberry Pi | PC |
| --- | --- | --- |
| Model | | |
| OS | | |
| Kernel | | |
| Python | | |
| VoiceStock commit | | |
| Worktree clean | | |
| Microphone | | |
| Button pin (BCM) | | |
| Supply | | |
| VoiceStock interface | | |

## 6. Results

| Test | Executions | Status | Measured success | Notes |
| --- | --- | --- | --- | --- |
| TC-ENV-001 | none | DESIGNED | | |
| TC-GPIO-001 | none | DESIGNED | | |
| TC-AUD-001 | none | DESIGNED | | |
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

Duration summaries are added as tables copied from execution records, with
`n`, mean, median, standard deviation, minimum, and maximum, in
milliseconds, and with a link to the raw samples. Do not add a row before
the raw samples exist.

## 7. Incidents

None recorded. This sentence means the campaign has not been executed. It
does not mean the product has no defects.

## 8. Deviations from the specification

None recorded.

## 9. Conclusions

Do not write a conclusion, a pass claim, or a recommendation that the
hardware works until the closure checklist in the
[test plan](test-plan.md#closure-checklist-for-closed_passed) has been
applied to the cases the conclusion cites.

What can be said before any execution is only:

- the procedures are specified;
- the default PC audio stub cannot create a pending operation;
- simulated end-to-end execution is blocked on a fixture that is specified
  and not implemented;
- PendingOperationWeb-08 remains open regardless of TC-E2E-001.

## 10. Bitácora pointer

Future sessions are logged in [../../bitacora/bitacora.md](../../bitacora/bitacora.md)
as described in the [campaign README](README.md#bitácora). This summary
links to those sessions after they exist:

| Date | Bitácora section | Executions |
| --- | --- | --- |
| | | |
