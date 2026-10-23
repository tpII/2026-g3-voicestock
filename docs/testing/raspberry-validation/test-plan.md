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
| Integration | Do two or more real components work together? | TC-PTT-001, TC-PTT-002, TC-COM-001, TC-COM-002, TC-COM-003, TC-WEB-002, TC-FLOW-001 |
| Simulated end-to-end | Does the Pi runtime complete a cycle when only the unavailable PC interpretation is replaced? | TC-E2E-001 |
| Full real end-to-end | Does a spoken command become a validated operation and a stock change? | Not in this campaign |

A unit test that mocks GPIO or PortAudio does not satisfy a hardware case.
A hardware case that never starts `voicestock-pi` does not satisfy
TC-E2E-001.

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
| 15 | [TC-FLOW-001](test-cases/TC-FLOW-001.md) | Phase changes, including the stub's contract rejection | The success half waits on the fixture below. The rejection half does not. |
| 16 | [TC-WEB-002](test-cases/TC-WEB-002.md) | The page and the resolution routes follow one pending operation | Requires the fixture. It is narrower than the full simulated cycle. |
| 17 | [TC-E2E-001](test-cases/TC-E2E-001.md) | The simulated cycle across button, WAV, HTTP, contract, page, confirm, and cancel | Last, because it assumes the earlier interfaces already had their own records. |

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

The project bitácora is not part of this order. Execution records, the
summary, and this campaign's traceability are updated as each case
finishes. [The bitácora](README.md#bitácora) is appended once at the end of
the testing day. The planned days, 23 and 24 October 2026, are not
results. Unfinished cases stay pending or blocked if those days end first.

## Simulated end-to-end

TC-E2E-001 runs the real `voicestock-pi` process: physical button, USB
microphone, `AudioCapture`, `RecordingSender`,
`HttpInterpretationClient`, `PcResponseInterpreter`, `OperationValidator`,
`PendingOperationFlow`, and the in-process web UI.

Only the missing PC interpretation is replaced. The replacement must still
be reached through `POST /api/v1/interpret-audio` on a PC process that the
Pi can route to `192.168.50.2`.

### Why the shipped server is not enough

`voicestock-pc-server` calls `create_pc_app` with the default
`describe_received_audio` handler (`src/pc/main.py`). For a readable WAV
the Pi receives a success envelope whose service payload is
`received_audio` (size, duration, sample rate, channels, sample width).
`PcResponseInterpreter` removes `recognized_text` only when that field is a
string, then passes the rest to `OperationValidator`. `received_audio` has
no `contract_version`, so the validator rejects it. The flow returns to
`idle` and sets:

```text
El pedido no es una operación válida. Presioná el botón para intentar de nuevo.
```

`StubProvider` is also insufficient. It answers the text endpoint with
`{"recognized_text": "<input>"}` and is not the audio handler. The runtime
uploads audio, not text (`RecordingSender` calls `interpret_audio`).

`create_pc_app(..., audio_handler=...)` can take another handler, but no
environment variable, CLI flag, or config file selects one.
`voicestock-pc-server` does not expose the parameter.

### Fixture requirements

Do not implement the fixture as part of this documentation change. A later
change should add a PC entry point that:

1. Runs on the PC and binds with `ServerSettings` (host and port from
   `VOICESTOCK_PC_HOST` and `VOICESTOCK_PC_PORT`).
2. Builds the app with `pc.main.create_pc_app` so the existing audio route
   still enforces `audio/wav`, the 4 MiB limit (`MAX_AUDIO_BYTES`), and
   `read_wav` before the handler runs.
3. Supplies an audio handler that ignores the spoken content and returns
   `ServiceResult.success` of the object in
   [fixtures/service-success-payload.json](fixtures/service-success-payload.json).
   That object is a version-1 contract plus a synthetic `recognized_text`.
   The same bytes are returned for every WAV that `read_wav` accepts.
4. Does not call `describe_received_audio`, `StubProvider`, a transcription
   API, or a language model, and does not read API keys.
5. Writes the received length and SHA-256 to stderr, or to a path outside
   the repository. It does not copy the WAV into git.
6. Is selected only by starting that entry point. Starting
   `voicestock-pc-server` must keep today's stub.

Until that entry point exists, TC-WEB-002, the success trials of
TC-FLOW-001, and TC-E2E-001 stay **BLOCKED** at execution time. Their
specifications stay **DESIGNED**. Do not point those cases at the stub and
then treat the rejection as a successful pending operation.

The rejection trial in TC-FLOW-001 is different: it uses the stub on
purpose and expects the message quoted above.

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

Out of scope for every case:

- real speech-to-text quality;
- real language-model interpretation;
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
- TC-WEB-002
- TC-CON-001
- TC-FLOW-001
- TC-E2E-001

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
| Button-to-pending latency | User-observed interval, kept separate from HTTP time | No pending operation when the fixture response is valid |
| Repeated-cycle success rate | Passes over the planned repeats | A criterion inside the cycle fails |

The repeat counts are in the
[measurement methodology](measurement-methodology.md). They are sample
sizes, not performance limits.
