# Raspberry Pi–PC communication protocol comparison

## Purpose

This document compares transport alternatives for the VoiceStock MVP. The
Raspberry Pi must send recognized Spanish text to a PC over an isolated local
network and receive one structured response. The transport must remain
independent from `InterpretationService` and from the inventory contract carried
inside the response.

The resulting interaction is strictly request/response:

```text
Raspberry Pi                          PC
     |                                |
     | recognized text request       |
     |------------------------------->|
     |                                | replaceable handler
     | structured response            |
     |<-------------------------------|
```

Runtime Internet access is not required by any alternative considered here.
Dependencies may be installed during provisioning, but the deployed client and
server must operate entirely on the local network.

## Evaluation criteria

The alternatives are evaluated against the October MVP rather than against
hypothetical future requirements.

1. Natural fit for one request followed by one response.
2. Low implementation and operational complexity.
3. Explicit timeouts, status and error handling.
4. Straightforward UTF-8 and structured-data support.
5. Testability with an in-process or local stub handler.
6. Ability to keep the payload opaque to the transport layer.
7. Reasonable CPU, memory and dependency cost on a Raspberry Pi 3.
8. Ease of diagnosing the system from common development tools.

Expected end-to-end latency is dominated by speech recognition and command
interpretation. Micro-optimizing transport latency is therefore less valuable
than keeping the protocol observable and reliable.

## Alternatives

| Alternative | Request/response fit | Main advantages | Main drawbacks | MVP assessment |
|---|---|---|---|---|
| HTTP/1.1 with JSON | Direct | Standard status codes, mature tooling, simple stubs, easy UTF-8 JSON exchange, payload can remain opaque | Some header overhead; requires an HTTP server implementation on the PC | Best fit |
| WebSocket | Possible, but not its main strength | Persistent full-duplex channel; useful for unsolicited events or continuous streaming | Connection lifecycle, reconnection and message correlation add complexity that the current flow does not need | Reject for MVP |
| gRPC unary RPC | Direct | Typed service definitions, generated clients, deadlines and a well-defined RPC model | HTTP/2, Protocol Buffers and code generation add tooling and deployment cost; poor fit for a contract currently centered on inspectable JSON | Reject for MVP |
| Custom TCP protocol | Must be designed | Minimal protocol dependencies and full control | VoiceStock would need to own framing, message length, encoding, status, errors, compatibility and diagnostics | Reject for MVP |

### HTTP/1.1 with JSON

HTTP already models a client request followed by a server response and separates
protocol metadata from representation data. A single `POST` endpoint is enough
for the MVP. Both ends can be exercised locally, and the handler behind the PC
endpoint can be replaced without changing the wire protocol.

JSON messages exchanged between systems must use UTF-8. The official JSON
specification requires UTF-8 for interoperable exchange, which also covers
Spanish input without a project-specific text encoding.

### WebSocket

WebSocket provides two-way communication over a long-lived connection. That is
valuable when either peer sends unsolicited events or when a continuous stream
is needed. VoiceStock currently has neither requirement: the Raspberry initiates
one command and waits for one response. Adopting WebSocket now would introduce
connection state and request correlation without satisfying an MVP need.

It can be reconsidered if a later requirement introduces server push or a
continuous bidirectional audio/event stream.

### gRPC

Unary gRPC supports the required interaction, and deadlines are useful. Its
normal workflow, however, adds a service definition, generated bindings,
Protocol Buffers and an HTTP/2 runtime. Those costs would be justified for a
larger typed service surface, but not for the current single JSON-oriented
operation.

It can be reconsidered if VoiceStock grows multiple internal RPC services that
benefit from generated cross-language contracts.

### Custom TCP protocol

TCP provides a byte stream, not application messages. VoiceStock would have to
define and test framing, partial reads and writes, length limits, encoding,
timeouts and error representation. That work would reproduce capabilities
already provided by HTTP and would make manual inspection harder.

It can be reconsidered only if measurements show that HTTP overhead is a real
bottleneck on the target hardware.

## Recommendation

Use HTTP/1.1 with UTF-8 JSON over the isolated TCP/IP network:

- the Raspberry Pi acts as the HTTP client;
- the PC acts as the HTTP server;
- the MVP exposes one versioned `POST` endpoint for interpretation requests;
- `Content-Type` is `application/json`;
- both client and server use explicit timeouts and bounded body sizes;
- the server delegates to a replaceable handler;
- the transport layer treats the successful handler value as opaque.

The server framework and client library are implementation choices for
`RaspberryPiPCCommunication-02` and the corresponding Raspberry task. They must
preserve this protocol decision and must not leak a concrete interpretation
provider into the transport API.

## Minimum contract implications

The exact schema will be made executable during implementation, but the protocol
decision establishes these boundaries:

### Request

- Carries recognized text as a JSON string field.
- Rejects a missing, empty or non-string text field at the request boundary.
- Does not contain audio, provider configuration or inventory state.

### Response

- Uses an outer `TransportEnvelope<T>` owned by
  `RaspberryPiPCCommunication`.
- The envelope indicates transport-level success or failure.
- On success, `payload` is opaque to the transport and can later contain
  `ServiceResult<ContractPayload>`.
- A typed `ServiceResult` error is still a successfully transported payload; it
  must not be rewritten as a transport failure.
- Transport errors use stable machine-readable codes. Human-readable diagnostic
  detail is not contractual.

### HTTP and failure semantics

- `2xx`: the request reached the replaceable handler and its opaque result was
  serialized successfully.
- `4xx`: the HTTP request, media type, encoding or transport-level request shape
  is invalid.
- `5xx`: the server could not invoke the handler or serialize its result.
- Connection refusal, loss and client timeout produce no server envelope and
  remain client-side transport failures.
- Inventory operations, product matching, quantities and units are never
  inspected by this layer.

Concrete field names, endpoint paths, size limits and the HTTP status mapping
will be finalized with executable tests in `RaspberryPiPCCommunication-02`.

## Validation approach

The implementation can be validated without `InterpretationService`:

1. Start the PC server with a stub handler.
2. Send Spanish text from a local client using the documented JSON request.
3. Make the stub return an arbitrary JSON-serializable object.
4. Assert that the response preserves that object inside the transport envelope.
5. Exercise malformed JSON, unsupported media type, invalid request shape,
   timeout and unavailable-server cases separately.

## Limitations of this comparison

- No physical Raspberry Pi benchmark was needed because all four alternatives
  are viable at the expected message volume; the differentiator is complexity.
- The recommendation assumes one command per request and no server-initiated
  events.
- TLS is not selected for the isolated MVP network. Authentication and network
  exposure must be revisited before operating on an untrusted network.
- Exact libraries remain deliberately undecided until the server and client
  implementation tasks.

## References

- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)
- [RFC 8259: The JSON Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259.html)
- [RFC 6455: The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html)
- [gRPC core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/)
- [Python Socket Programming HOWTO](https://docs.python.org/3.11/howto/sockets.html)
