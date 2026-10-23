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

Leave this table blank until a TC-ENV-001 execution exists. Fill the
Raspberry Pi column from that record. The PC column is filled only when
that execution collected the PC. If it says
`NOT COLLECTED — PC NOT AVAILABLE`, leave these PC cells empty and do not
treat the baseline as proof of PC connectivity. A case that uses the PC
records the PC facts in its own execution before measuring.

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

The bitácora in [../../bitacora/bitacora.md](../../bitacora/bitacora.md) gets
one entry per testing day, after the last execution of that day, as
described in the [campaign README](README.md#bitácora). It is not updated
after every case.

The campaign is planned for 23 October 2026 and 24 October 2026. Those are
scheduling targets. This table stays empty until a day has actually been
worked. Do not add those dates in advance, and do not fill outcomes for
cases that were not run. A case still unfinished after 24 October 2026
stays pending or blocked in the results table above.

| Date | Bitácora section | Executions |
| --- | --- | --- |
| | | |
