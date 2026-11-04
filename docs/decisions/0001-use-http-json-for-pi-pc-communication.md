# ADR-0001: Use HTTP with JSON for Raspberry Pi–PC communication

## Status

Accepted

## Context

VoiceStock needs one local-network interaction in which the Raspberry Pi sends
recognized text to the PC and receives a structured response. The Raspberry Pi
must work without Internet access, and the transport must not depend on a
specific interpretation provider or understand the inventory payload.

HTTP, WebSocket, gRPC and a custom TCP protocol were compared in
[the communication research](../research/raspberry-pi-pc-communication.md).

## Decision

Use HTTP/1.1 with UTF-8 JSON over the isolated local network.

The Raspberry Pi is the client and the PC is the server. Communication uses a
versioned `POST` endpoint, explicit timeouts and an outer
`TransportEnvelope<T>`. The transport owns only that envelope; a successful
payload remains opaque and may contain `ServiceResult<ContractPayload>`.

This ADR selects the wire protocol, not a Python framework or client library.

## Alternatives considered

- **WebSocket:** rejected because the MVP does not require server push,
  full-duplex messaging or a long-lived channel.
- **gRPC:** rejected because HTTP/2, Protocol Buffers and generated bindings add
  complexity without a current need for a larger typed RPC surface.
- **Custom TCP:** rejected because framing, encoding, status, errors and
  compatibility would become project-owned protocol work.

## Consequences

### Positive

- The interaction maps directly to request/response.
- Requests and responses are inspectable with standard tools.
- A stub handler can test the transport before `InterpretationService` exists.
- Transport failures stay separate from typed service and domain failures.
- Runtime operation does not require Internet access.

### Negative

- HTTP headers add minor overhead compared with a custom binary protocol.
- The team must define endpoint versioning, body limits, timeout defaults and
  an exact transport-envelope schema during implementation.
- Without TLS, this design is only appropriate for the isolated trusted MVP
  network.

### Follow-up

- `RaspberryPiPCCommunication-02` must define the executable transport contract
  and implement the PC server with a replaceable handler.
- The Raspberry client must implement matching timeout and error behavior.
- `RaspberryPiPCCommunication-04` must document setup, examples and operation
  after both ends exist.
