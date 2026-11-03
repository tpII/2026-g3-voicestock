# Traceability matrix

Campaign status: **IN_PROGRESS**. TC-ENV-001 has one execution and is not
closed. TC-GPIO-001 has three executions and is not closed. TC-AUD-001 has
one execution and is not closed. TC-AUD-002 has one execution and is not
closed. TC-PTT-001 has two executions and is not closed. TC-PTT-002 has
one execution and is not closed. TC-NET-001 has three executions and is not closed. TC-NET-002 has
one execution and is not closed. TC-NET-003 has one execution and is not
closed. TC-COM-001 has one execution and is not closed. TC-COM-002 has
one execution and is not closed. Every other case is unexecuted. The result column stays `not executed` until an execution
record is linked. Do not infer a pass from the existence of a unit test.
Do not treat **PASSED_PENDING_DOCUMENTATION** or a callback count as
**CLOSED_PASSED**.

ClickUp task names are the anchors. This campaign does not create or edit
those tasks.

| Test | ClickUp | Requirement covered here | Result |
| --- | --- | --- | --- |
| [TC-ENV-001](test-cases/TC-ENV-001.md) | None. Supporting baseline. | Identify the Pi board, OS, runtime, power diagnostic, and network as found. PC facts are optional here and are not a connectivity result. | [EX-TC-ENV-001-20261027-01](executions/EX-TC-ENV-001-20261027-01.md): **PASSED_PENDING_DOCUMENTATION**. Not closed. Not a VoiceStock-cell or microphone result. |
| [TC-GPIO-001](test-cases/TC-GPIO-001.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | Nine measured press callbacks and nine release callbacks through `PushToTalkButton`, with no unsolicited idle callbacks. | [EX-TC-GPIO-001-20261027-01](executions/EX-TC-GPIO-001-20261027-01.md): **BLOCKED** before `READY`. [EX-TC-GPIO-001-20261027-02](executions/EX-TC-GPIO-001-20261027-02.md): **FAILED**. The supplied extract has 9 `PRESSED` and 9 `RELEASED`. The practice action was omitted and the pause and idle intervals were **not measured**. [EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md): **FAILED**. Practice excluded. 9 and 9 measured. Three pauses and three idles empty. Criterion 3, cleanup after Ctrl+C, **not verified**. Not a confirmed `close()` defect. Not closed. |
| [TC-AUD-001](test-cases/TC-AUD-001.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | USB microphone visible to PortAudio and, if present, to `arecord`. | [EX-TC-AUD-001-20261027-01](executions/EX-TC-AUD-001-20261027-01.md): **PASSED_PENDING_DOCUMENTATION**. Logitech G435 in 3 of 3 plugged enumerations, absent while unplugged, negative probe `AudioDeviceNotFoundError`. Query recorded. Not closed. Not a 16 kHz or acoustic result. |
| [TC-AUD-002](test-cases/TC-AUD-002.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | `AudioCapture` publishes a 16 kHz mono 16-bit WAV. | [EX-TC-AUD-002-20261103-01](executions/EX-TC-AUD-002-20261103-01.md): **PASSED_PENDING_DOCUMENTATION**. Five of five measured runs published a 16 kHz mono 16-bit WAV on `88a95d5` (`fix/audio-capture-stream-shutdown`, not merged to `develop`). Duration-error tolerance remains **TO BE DEFINED**. Review NOT_REVIEWED. Not closed. Not a speech-quality result. |
| [TC-PTT-001](test-cases/TC-PTT-001.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | Button and microphone through `voicestock-pi-ptt`, including a listening check of the predetermined phrases, without the PC. | [EX-TC-PTT-001-20261103-01](executions/EX-TC-PTT-001-20261103-01.md): **FAILED**. Microphone muted. Listening not verified. Not a software-defect finding. [EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md): **FAILED**. Three measured files at 16 kHz mono 16-bit, `RELEASED`, and reported as clearly audible. Phrase match and defect columns **NOT SEPARATELY CONFIRMED**. GPIO prerequisite [EX-TC-GPIO-001-20261103-01](executions/EX-TC-GPIO-001-20261103-01.md) remains **FAILED**. PC not contacted. Not closed. |
| [TC-PTT-002](test-cases/TC-PTT-002.md) | [PushToTalk-06](https://app.clickup.com/t/86e3euv9u) | Max duration, ignored press while recording, and wait for release. | [EX-TC-PTT-002-20261103-01](executions/EX-TC-PTT-002-20261103-01.md): **BLOCKED**. Three long holds printed one `MAX_DURATION` each. No extra file while the button stayed down. Three later holds printed `RELEASED`. Second mechanical press **NOT APPLICABLE**. Header duration 1.984 s versus 2.000 s. Gate **TO BE DEFINED**. Prerequisite [EX-TC-PTT-001-20261103-02](executions/EX-TC-PTT-001-20261103-02.md) remains **FAILED**. Not a product failure of the duration limit. Not closed. |
| [TC-NET-001](test-cases/TC-NET-001.md) | [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu) | Access-point and PC-client profiles match the documented cell. | [EX-TC-NET-001-20261103-01](executions/EX-TC-NET-001-20261103-01.md): **FAILED** on procedure version 1. `setup_pi_access_point.sh wlan0` stopped with a false unmanaged error. `GENERAL.STATE` was `100 (connected)`. Criteria 1–4 not executed. No ping. Incident [INC-EX-TC-NET-001-20261103-01-01](executions/INC-EX-TC-NET-001-20261103-01-01.md) **OPEN**. Not closed. Not a traffic result. [EX-TC-NET-001-20261103-02](executions/EX-TC-NET-001-20261103-02.md): **FAILED** on procedure version 1. The updated Pi script passed state detection and failed WPA2 activation (`supplicant-timeout`, then RSN `IE_DIFFERENT` after PMF was disabled by hand). The PC script stored a transient MAC. A manual `hostapd` session authenticated two stations, and the operator confirmed ICMP after `ip addr add`. That diagnostic is not a pass and not TC-NET-002. Incidents [02-01](executions/INC-EX-TC-NET-001-20261103-02-01.md), [02-02](executions/INC-EX-TC-NET-001-20261103-02-02.md), and [02-03](executions/INC-EX-TC-NET-001-20261103-02-03.md) are **OPEN**. Pi commit SHA **NOT RECORDED**. Not closed. [EX-TC-NET-001-20261103-03](executions/EX-TC-NET-001-20261103-03.md): **PASSED_PENDING_DOCUMENTATION** on procedure version 2. Technical configuration assessment **PASSED** on `develop` `485559c`. Review NOT_REVIEWED. Not ICMP, isolation, reboot, or recovery. Does not close attempts 01 or 02 or their incidents. Arch SHA **NOT RECORDED**. Not **CLOSED_PASSED**. |
| [TC-NET-002](test-cases/TC-NET-002.md) | [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu) | Bidirectional reachability and isolation from the Internet path. | [EX-TC-NET-002-20261103-01](executions/EX-TC-NET-002-20261103-01.md): **PASSED_PENDING_DOCUMENTATION**. Technical connectivity and IPv4 isolation met. 10/10 measured echoes each way. After Ethernet removal, no Pi default route and `Network is unreachable` for `1.1.1.1` (not a three-packet loss rate). Arch Internet stayed on `wlo1`. Loss allowance and latency budget **TO BE DEFINED**. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not IPv6, Tailscale behavior, firewall, reliability, or reboot. |
| [TC-NET-003](test-cases/TC-NET-003.md) | [LocalNetworkInfra-04](https://app.clickup.com/t/86e3jutyu) | Profiles return after reboot. | [EX-TC-NET-003-20261103-01](executions/EX-TC-NET-003-20261103-01.md): **PASSED_PENDING_DOCUMENTATION** on procedure version 2. Technical reboot recovery **PASSED**. Pi and PC boot ids changed. `voicestock-hostapd.service`, `voicestock-ap-address.service`, and `voicestock-client` returned without a setup script. Addresses `192.168.50.1/24` and `192.168.50.2/24`. Arch default route stayed on `wlo1`. Pi had no IPv4 default route; `1.1.1.1` was `Network is unreachable`. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not startup time, IPv6, or long-term availability. Procedure version 1 was not run. |
| [TC-COM-001](test-cases/TC-COM-001.md) | [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux) | Text client reaches the real PC server over the cell. | [EX-TC-COM-001-20261103-01](executions/EX-TC-COM-001-20261103-01.md): **PASSED_PENDING_DOCUMENTATION**. Technical text HTTP **PASSED**. 10/10 measured CLI calls exit 0 with the stub `recognized_text`. Server local bind `192.168.50.2:8000`. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Latency budget **TO BE DEFINED**. Not WAV, real speech recognition, or interpretation quality. |
| [TC-COM-002](test-cases/TC-COM-002.md) | [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux) | WAV body arrives and the stub reports the same size and format. | [EX-TC-COM-002-20261103-01](executions/EX-TC-COM-002-20261103-01.md): **PASSED_PENDING_DOCUMENTATION**. Technical WAV transfer **PASSED**. 5/5 measured uploads exit 0. Reported size 59436 and PCM fields match the local file. Local SHA-256 unchanged. Evidence pending. Review NOT_REVIEWED. Not **CLOSED_PASSED**. Not a digest of the received body. Not speech recognition or interpretation. |
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
