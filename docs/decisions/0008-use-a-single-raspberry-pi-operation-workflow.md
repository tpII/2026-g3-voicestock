# ADR-0008: Use a single Raspberry Pi operation workflow as the cycle owner

## Status

Accepted — 23 October 2026.

## Context

A spoken inventory command on the Raspberry Pi crosses several components
that were built separately: push-to-talk capture, the HTTP client, contract
validation, the pending-operation gateway, and the operator page.

Each component already has a boundary. Capture does not know the contract.
The web adapter must not own the pending operation. The gateway already
decides confirm, cancel, stale identifiers, and in-memory retries. What was
missing was a single owner for the cycle that connects those boundaries:
when a capture may start, when a PC answer becomes a pending operation, and
when the device is idle again.

Without that owner, the phase of the device and the existence of a pending
operation could drift apart across callbacks and HTTP handlers.

## Decision

The Raspberry Pi uses one in-process orchestrator, `PendingOperationFlow`,
as the owner of the operation-cycle state machine and of the only pending
operation.

Peripheral components keep their existing responsibilities. `PushToTalkController`
captures audio. `RecordingSender` and `HttpInterpretationClient` move the WAV.
`PcResponseInterpreter` classifies the `TransportEnvelope`. `OperationValidator`
accepts or rejects the contract. `PendingOperationGateway` confirms and
cancels. The web application calls the query, resolution, and status ports.
It does not mutate the phase.

The behavior of that orchestrator is
[the operation workflow](../architecture/pending-operation-flow.md). How the
process is composed is the
[integrated runtime](../setup/pi-runtime.md).

## Alternatives considered

- **One state machine as the cycle owner.** Accepted. Transitions are
  explicit, and the pending operation exists only in `WAIT_CONFIRMATION`.
  Tests can drive the flow without GPIO or a microphone.
- **Distributed state across components and callbacks.** Rejected. Capture,
  the HTTP callback, and the page would each remember part of the cycle.
  A failure in one callback could leave another component believing a
  capture is still allowed, or that a pending operation still exists.
- **Orchestration inside the web endpoints.** Rejected. The page would start
  and stop the cycle, so a missing browser poll or a refresh could change
  the device phase. The physical button would no longer be the start of a
  capture. This also conflicts with
  [ADR-0009](0009-use-in-process-fastapi-and-static-web-ui.md), which keeps
  FastAPI as an adapter.

## Consequences

### Positive

- The phase and the pending operation have one source of truth.
- Transitions are explicit and can be tested without hardware.
- A second pending operation cannot be stored beside the current one.
- A later inventory executor or a real PC audio handler can be connected
  at the existing ports without a second cycle owner.
- The web UI reads status and resolves a named operation. It does not
  administer the state machine.

### Negative

- The flow, the push-to-talk worker, and the gateway lock have to stay
  consistent under concurrent button events and HTTP requests.
- The pending operation and the last resolution live in memory. They end
  when the process ends.
- The cycle cannot outlive that process, and this ADR does not add a
  recovery store.
- A later change still has to replace the provisional executor with real
  inventory execution, and replace the PC audio stub with the voice
  pipeline. Those are not part of this decision.
