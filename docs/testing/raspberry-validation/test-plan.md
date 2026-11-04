# Test plan

Specification for the Raspberry Pi validation campaign. Procedures live in
[test-cases/](test-cases/). Numbers are not filled in here. A threshold that
the project has not agreed is marked **TO BE DEFINED**, with the baseline
that would justify it.

## Purpose

Show, on the project Raspberry Pi and a PC joined to its isolated Wi-Fi
cell, that:

- the board, the operating system, and the VoiceStock runtime can be
  identified and reproduced;
- the physical button and the USB microphone work through the VoiceStock
  adapters;
- the Pi can publish a WAV that matches the capture contract;
- the Pi access point and the PC client form an isolated link;
- the Pi HTTP client can carry text and a WAV to a real PC process;
- the operator page is served by the Pi and follows the pending-operation
  API;
- the Pi accepts and rejects contract payloads with its own validator;
- `PendingOperationFlow` moves through its phases on the device;
- one simulated end-to-end cycle uses the real Pi runtime and a
  contract-compatible PC response.

## Levels

| Level | Question it answers | Cases |
| --- | --- | --- |
| Hardware validation | Does this physical interface behave as the adapter assumes? | TC-ENV-001, TC-GPIO-001, TC-AUD-001, TC-NET-001, TC-NET-002, TC-NET-003 |
| Software component on the Raspberry Pi | Does this module, running on the Pi, honor its contract when the neighboring hardware or service is held still? | TC-AUD-002, TC-CON-001, TC-WEB-001 |
| Integration | Do two or more real components work together? | TC-PTT-001, TC-PTT-002, TC-COM-001, TC-COM-002, TC-COM-003, TC-FLOW-001 |
| Full real end-to-end | Does one spoken command become a validated pending operation, then idle after confirm or cancel, without an inventory write? | [TC-E2E-002](test-cases/TC-E2E-002.md). [EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) is **FAILED** on the written N1 criterion and is not **CLOSED_PASSED**. Inventory persistence was not tested. A stock change stays outside v0.5.0. |

A unit test that mocks GPIO or PortAudio does not satisfy a hardware case.
A hardware case that never starts `voicestock-pi` does not satisfy
TC-E2E-002 or TC-FLOW-001.

## Execution order

Run the cases in this order. Independent branches may be interleaved only
when their dependencies are already satisfied.

| Step | Case | What it unlocks | Why it is next |
| --- | --- | --- | --- |
| 1 | [TC-ENV-001](test-cases/TC-ENV-001.md) | A recorded Pi baseline of hardware, OS, Python, power diagnostics, and the network as found. PC facts are included when the PC is present. | Later Pi changes are deviations from this record. No setup script runs in this step. The Pi record can close without the PC. |
| 2 | [TC-GPIO-001](test-cases/TC-GPIO-001.md) | The button can notify press and release | Audio capture does not need the button. Push-to-talk does. |
| 3 | [TC-AUD-001](test-cases/TC-AUD-001.md) | A PortAudio name for the USB microphone | Capture needs that name. It does not need the button or the network. |
| 4 | [TC-AUD-002](test-cases/TC-AUD-002.md) | A WAV produced by `AudioCapture` | Push-to-talk and the audio client need a file that already matches the contract. |
| 5 | [TC-PTT-001](test-cases/TC-PTT-001.md) | Button and microphone through `voicestock-pi-ptt` | This is the product capture path without the PC and without the web cycle. |
| 6 | [TC-PTT-002](test-cases/TC-PTT-002.md) | Max-duration stop and ignored extra presses | Those races are easier to see before the PC is involved. |
| 7 | [TC-NET-001](test-cases/TC-NET-001.md) | Local access-point and PC-client profiles | Connectivity tests need the profiles. The baseline in step 1 must already exist. |
| 8 | [TC-NET-002](test-cases/TC-NET-002.md) | Pi and PC can exchange packets, and the cell stays off the Internet path | HTTP and the browser need this path. |
| 9 | [TC-NET-003](test-cases/TC-NET-003.md) | The cell comes back after reboot | A link that dies on reboot is not the deployed configuration. |
| 10 | [TC-COM-001](test-cases/TC-COM-001.md) | Text HTTP from the Pi client to the real PC server | Separates reachability of the server from WAV handling. |
| 11 | [TC-COM-002](test-cases/TC-COM-002.md) | A WAV arrives intact at `describe_received_audio` | Uses the current stub on purpose. It does not create a pending operation. |
| 12 | [TC-COM-003](test-cases/TC-COM-003.md) | Connection failure and timeout are reported by the client | Failure setup would contaminate the success samples of TC-COM-001. |
| 13 | [TC-WEB-001](test-cases/TC-WEB-001.md) | `/health` and idle `system-status` on the Pi address | The page can be checked before a pending operation exists. |
| 14 | [TC-CON-001](test-cases/TC-CON-001.md) | The Pi validator accepts and rejects the campaign payloads | The cycle trusts this module. It does not need the microphone. |
| 15 | [TC-FLOW-001](test-cases/TC-FLOW-001.md) | Integrated error handling: invalid contract, connection failure, and response timeout | Procedure version 2. [EX-TC-FLOW-001-20261104-01](executions/EX-TC-FLOW-001-20261104-01.md) is **PASSED_PENDING_DOCUMENTATION**, technical result **PASSED**, not **CLOSED_PASSED**. It does not wait on a deterministic contract fixture. |

TC-CON-001 may run any time after TC-ENV-001. It is placed late so the
hardware work is not blocked on a software check. TC-GPIO-001 and
TC-AUD-001 do not depend on each other.

TC-ENV-001 may close with the PC marked `NOT COLLECTED — PC NOT AVAILABLE`.
That line is not a connectivity result. TC-NET-001 and every later case
that uses the PC must record the PC operating system, the checkout
revision, and the interface names in its own execution before the first
measured sample, if the baseline did not already record them. Those cases
stay **BLOCKED** until that PC inventory exists. Collecting it still does
not pass TC-NET-002.

TC-NET-001 procedure version 1 is preserved in
[TC-NET-001 procedure version 1](test-cases/TC-NET-001-procedure-v1.md).
It is the procedure executed by
[EX-TC-NET-001-20261103-01](executions/EX-TC-NET-001-20261103-01.md) and
[EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md). Both
are **FAILED** and not closed. Procedure version 2 is in force in
[TC-NET-001](test-cases/TC-NET-001.md).
[EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md) is the
first run of that version. It is **PASSED_PENDING_DOCUMENTATION**: technical
configuration **PASSED**, evidence pending, review NOT_REVIEWED, not
**CLOSED_PASSED**. The proposal file keeps its filename and is a historical
design artifact, not the procedure. Do not apply version 2 to attempts 01
and 02. The manual ping inside attempt 02 is not TC-NET-002.
[EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md) is the
first run of TC-NET-002 procedure version 1. It is
**PASSED_PENDING_DOCUMENTATION** and not closed.
[EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md) is the
first run of TC-NET-003 procedure version 2. It is
**PASSED_PENDING_DOCUMENTATION** and not closed. Procedure version 1 of
TC-NET-003 was not executed.

[EX-TC-COM-003-20261103-01](executions/EX-TC-COM-003-20261103-01.md) followed
[TC-COM-003 procedure version 1](test-cases/TC-COM-003-procedure-v1.md).
The `ncat` example was not run. A Python listener was. Procedure version 2
in [TC-COM-003](test-cases/TC-COM-003.md) was written after that execution
and is not applied to it. The run is **PASSED_PENDING_DOCUMENTATION** and
not **CLOSED_PASSED**.

Which later cases can start is in [readiness.md](readiness.md). That note
does not implement a deterministic contract entry point. The active v0.5.0
campaign no longer requires one.

The project bitácora is not part of this order. Execution records, the
summary, and this campaign's traceability are updated as each case
finishes. [The bitácora](README.md#bitácora) is appended once at the end of
the testing day. The planned days, 23 and 24 October 2026, are not
results. Unfinished cases stay pending or blocked if those days end first.

## Withdrawn from the active v0.5.0 campaign

<a id="simulated-end-to-end"></a>
<a id="fixture-requirements"></a>

TC-E2E-001 and TC-WEB-002 were designed and never executed. This campaign
no longer keeps them as active cases. Their standalone specifications were
removed because they contained only that unexecuted text. This section is
the record of that scope change. It is not an execution and it is not a
pass.

TC-E2E-001 would have run the real Pi runtime against a PC handler that
returned one fixed operation contract for every accepted WAV. TC-WEB-002
would have exercised the pending-operation card and the confirm and cancel
routes against that same contract. Both overlap the real integration path
already exercised in
[TC-E2E-002](test-cases/TC-E2E-002.md). The team will not maintain a
deterministic PC fixture only to finish v0.5.0.

[TC-FLOW-001 procedure version 1](test-cases/TC-FLOW-001-procedure-v1.md)
also required that fixture for its success trial. That procedure was not
executed. Procedure version 2 keeps the identifier and drops the success
trial. It tests invalid-contract, connection-failure, and response-timeout
behavior. It is **DESIGNED** and has no execution.

[fixtures/service-success-payload.json](fixtures/service-success-payload.json)
remains in the tree as a historical payload. No active v0.5.0 case requires
a PC entry point that returns it.

## PC audio path used by the remaining cases

`voicestock-pc-server` defaults to the stub. `VOICESTOCK_AUDIO_PIPELINE`
unset or `stub` keeps `describe_received_audio`. A readable WAV then
returns a success envelope whose payload is `received_audio`. That object
has no `contract_version`. The Pi rejects it, returns to `idle`, and sets:

```text
El pedido no es una operación válida. Presioná el botón para intentar de nuevo.
```

That rejection is scenario A of
[TC-FLOW-001](test-cases/TC-FLOW-001.md). It is not a pending operation.

`VOICESTOCK_AUDIO_PIPELINE=groq` transcribes the WAV with Groq Whisper,
asks `openai/gpt-oss-20b` for one structured draft, and returns a version-1
contract plus `recognized_text` when that draft matches one catalog
product. The Pi validator assigns `product_id`. Confirm and cancel do not
persist inventory. Setup is
[the PC audio pipeline guide](../../setup/pc-audio-pipeline.md).

That mode is current product behavior on `develop` at `c151db2`. It is the
peer required by TC-E2E-002. It is not a production accuracy guarantee.
[EX-TC-E2E-002-20261104-01](executions/EX-TC-E2E-002-20261104-01.md) is
**FAILED** on the written N1 criterion. Its v0.5.0 decision remains
`ACCEPTED_WITH_KNOWN_LIMITATIONS`. That decision does not close the case
and does not close the campaign.

## Campaign catalog

Product identity for every contract case is
[fixtures/campaign-catalog.json](fixtures/campaign-catalog.json). It is a
JSON list that `pi.operation_contract.load_catalog` can read. Two rice
products share name and brand and differ in presentation, so a query with
only the shared attributes is ambiguous and a query with the presentation
identifies one product. This follows
[ADR-0006](../../decisions/0006-identify-products-by-unique-attribute-match.md).

The catalog is a specification input. It is not the production catalog and
it is not loaded unless the operator passes `--catalog`.

## In scope and out of scope

In scope: the areas in the [campaign README](README.md#what-this-campaign-covers).

Out of scope for every case, and excluded from the v0.5.0 claim:

- a production-grade speech-to-text accuracy guarantee;
- a production-grade language-model interpretation accuracy guarantee;
- more than one operation in a single voice command;
- SQLite or any inventory mutation;
- closing [PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6);
- closing [InterpretationService-04](https://app.clickup.com/t/86e3ev2v6);
- changing application code, network scripts, or system configuration in
  order to make a case pass during the same execution that records the
  failure.

A configuration change after a failure is a new execution. The first record
stays **FAILED** or **BLOCKED** with the incident attached.

## Status model

| Status | Meaning |
| --- | --- |
| PLANNED | The need is known and the procedure is not written. |
| DESIGNED | The procedure and the acceptance criteria are written. Nobody has executed them for this campaign. |
| IN_PROGRESS | An execution record is open and the run is not finished. |
| BLOCKED | The run cannot start or cannot finish because a precondition is missing. This is not a product failure. |
| FAILED | A predetermined criterion was not met. |
| PASSED_PENDING_DOCUMENTATION | Every criterion was met and the execution record, evidence, or review is still incomplete. |
| CLOSED_PASSED | The run passed and the closure checklist below is complete. |
| CLOSED_FAILED | A failed run is fully documented and reviewed. This is administrative closure. It is not approval of the product. |

New cases start at **DESIGNED**. Do not move a case to **CLOSED_PASSED**
from CI, from a mock, or from an anecdotal note.

### Closure checklist for CLOSED_PASSED

All of the following must be true:

1. A completed execution record exists and uses a unique id.
2. The required evidence is stored or referenced.
3. The measurements required by the case are recorded, or the case states
   that a metric is not measurable and the record says **NOT MEASURED**.
4. Each criterion was compared with the observations.
5. Incidents and deviations are written down, including an explicit "none".
6. Someone other than the operator has reviewed the record, or the record
   explains why a second reviewer was not available and the status stays
   below **CLOSED_PASSED** until that review happens.
7. The [traceability matrix](traceability-matrix.md) and the
   [summary](summary.md) cite that execution.

**PASSED_PENDING_DOCUMENTATION** is the status when the behavior passed and
any of items 1–7 is still open. It is not a license to skip them.

## Identifiers

Test ids in this campaign:

- TC-ENV-001
- TC-GPIO-001
- TC-AUD-001
- TC-AUD-002
- TC-PTT-001
- TC-PTT-002
- TC-NET-001
- TC-NET-002
- TC-NET-003
- TC-COM-001
- TC-COM-002
- TC-COM-003
- TC-WEB-001
- TC-CON-001
- TC-FLOW-001
- TC-E2E-002

Sixteen cases are active. TC-WEB-002 and TC-E2E-001 were specified, never
executed, and withdrawn from this campaign. Removing them is not a pass.
See [Withdrawn from the active v0.5.0 campaign](#withdrawn-from-the-active-v050-campaign).

Execution ids: `EX-<test-id>-<YYYYMMDD>-<nn>` with `<nn>` starting at `01`
for that test id and date. Incident ids: `INC-<execution-id>-<nn>`.

## Unagreed thresholds

Do not invent a pass limit for these. Record the samples. The first accepted
baseline is a later decision, taken from raw samples of runs that were
otherwise valid, and written into the case before those numbers become
gates.

| Topic | What to record now | Hard fail that already exists |
| --- | --- | --- |
| GPIO edge latency | **NOT MEASURED** unless an external instrument is named | A scripted press/release pair produces no callback |
| Recording duration error | Header duration minus the monotonic hold | Format is not 16 kHz, mono, signed 16-bit |
| Stream start time | Monotonic time until `AudioCapture.start` returns | Start raises, including the implementation's 5 s worker wait |
| ICMP loss and RTT | Loss count and RTT samples from `ping` | Zero successful replies in the measured set, or the route uses the wrong interface |
| HTTP duration | Monotonic time around one client call on the Pi | Wrong envelope status or wrong error code for that trial |
| UI lag | Time from the API showing `wait_confirmation` until the page shows it | The page never shows the API confirmation text |
| Button-to-pending latency | User-observed interval, kept separate from HTTP time | No pending operation when TC-E2E-002's assigned positive command was spoken to the Groq peer |
| Repeated-cycle success rate | Passes over the planned repeats | A criterion inside the cycle fails |

The repeat counts are in the
[measurement methodology](measurement-methodology.md). They are sample
sizes, not performance limits.
