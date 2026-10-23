# Traceability matrix

Campaign status: **DESIGNED**. Every case is unexecuted. The result column
stays `not executed` until an execution record is linked. Do not infer a
pass from the existence of a unit test.

ClickUp task names are the anchors. This campaign does not create or edit
those tasks.

| Test | ClickUp | Requirement covered here | Result |
| --- | --- | --- | --- |
| [TC-ENV-001](test-cases/TC-ENV-001.md) | None. Supporting baseline. | Identify the board, OS, runtime, and network as found before any change. | not executed |
| [TC-GPIO-001](test-cases/TC-GPIO-001.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | Physical press and release through `PushToTalkButton`. | not executed |
| [TC-AUD-001](test-cases/TC-AUD-001.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | USB microphone visible to PortAudio and, if present, to `arecord`. | not executed |
| [TC-AUD-002](test-cases/TC-AUD-002.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | `AudioCapture` publishes a 16 kHz mono 16-bit WAV. | not executed |
| [TC-PTT-001](test-cases/TC-PTT-001.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | Button and microphone through `voicestock-pi-ptt` without the PC. | not executed |
| [TC-PTT-002](test-cases/TC-PTT-002.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | Max duration, ignored press while recording, and wait for release. | not executed |
| [TC-NET-001](test-cases/TC-NET-001.md) | [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu) | Access-point and PC-client profiles match the documented cell. | not executed |
| [TC-NET-002](test-cases/TC-NET-002.md) | [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu) | Bidirectional reachability and isolation from the Internet path. | not executed |
| [TC-NET-003](test-cases/TC-NET-003.md) | [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu) | Profiles return after reboot. | not executed |
| [TC-COM-001](test-cases/TC-COM-001.md) | [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux) | Text client reaches the real PC server over the cell. | not executed |
| [TC-COM-002](test-cases/TC-COM-002.md) | [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux) | WAV body arrives and the stub reports the same size and format. | not executed |
| [TC-COM-003](test-cases/TC-COM-003.md) | [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux) | Client reports `connection_failed` and `timeout`. | not executed |
| [TC-WEB-001](test-cases/TC-WEB-001.md) | [PendingOperationWeb-07](https://app.clickup.com/t/86e3eve7j) | Pi HTTP server, idle status, and the page shell. | not executed |
| [TC-WEB-002](test-cases/TC-WEB-002.md) | [PendingOperationWeb-07](https://app.clickup.com/t/86e3eve7j) | Pending card, confirm, cancel, and the documented conflict responses. | not executed |
| [TC-CON-001](test-cases/TC-CON-001.md) | [OperationContractValidation-06](https://app.clickup.com/t/86e3ev73g) | Structural and catalog validation on the Pi interpreter. | not executed |
| [TC-FLOW-001](test-cases/TC-FLOW-001.md) | [PendingOperationFlow-05](https://app.clickup.com/t/86e3evaer) | Phases, single pending operation, stub rejection, and transport failure. | not executed |
| [TC-E2E-001](test-cases/TC-E2E-001.md) | **PENDING CLICKUP TASK CREATION** | Simulated Pi cycle with a contract fixture. | not executed |

## Tasks this campaign does not close

| ClickUp | Why no case closes it |
| --- | --- |
| [InterpretationService-04](https://app.clickup.com/t/86e3ev2v6) | Interpretation quality is out of scope. The fixture does not interpret speech. |
| [PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6) | That task expects a real end-to-end flow, including real speech-to-text and interpretation. TC-E2E-001 must not be used as the evidence that closes it. |

## Supporting checks without a task

TC-ENV-001 has no ClickUp id. It exists so later cases can name the machine
they ran on. Do not file a task only to fill this cell.

## Coverage the matrix does not claim

- Inventory persistence and SQLite are not mapped because they are not
  implemented on this path (`ProvisionalOperationExecutor`).
- PC-side contract production (`pc.operation_contract.map_draft`) is not
  executed here. TC-CON-001 feeds payloads to the Pi validator directly.
- GPIO electrical latency is not a requirement of this matrix until an
  instrument is available.
