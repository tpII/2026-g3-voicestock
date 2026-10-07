# Raspberry Pi–PC communication interface

## Purpose

This interface transports recognized text from the Raspberry Pi to a
replaceable handler running on the PC, and the handler's result back. It does
not perform speech recognition, interpret inventory commands, validate
products, orchestrate pending operations or modify inventory.

The protocol is HTTP + JSON in a single request/response exchange: the
Raspberry Pi is the client and sends one text; the PC is the server and returns
one answer. WebSocket was rejected because there is no need for server push or
a long-lived channel; gRPC, because HTTP/2, Protocol Buffers and generated
bindings add complexity without a current need; a custom TCP protocol, because
framing, encoding, status and errors would become project-owned work. The full
comparison is in
[ADR-0001](../decisions/0001-use-http-json-for-pi-pc-communication.md).

## Responsibilities by layer

```text
HTTP request/response
└── TransportEnvelope<T>                 RaspberryPiPCCommunication
    └── ServiceResult<ContractPayload>   InterpretationService
        └── ContractPayload              OperationContractValidation
```

| Layer | Owner | Answers |
|---|---|---|
| `TransportEnvelope` | RaspberryPiPCCommunication | Did the message travel between Raspberry Pi and PC? |
| `ServiceResult` | InterpretationService | Could the text be interpreted? |
| `ContractPayload` | OperationContractValidation | Is the operation valid for the domain? |

RaspberryPiPCCommunication owns only the outer envelope. Neither the server nor
the client inspects the payload: they do not read or validate the operation,
product, quantity or unit, and they deliver the payload intact even when its
domain content is invalid.

The server's handler is `InterpretationService.interpret`, wired in
`src/pc/main.py`. That module is the only one that knows both layers:
`pc.communication` does not import `pc.interpretation`. The code is split by
where it runs: the server in `src/pc`, the client in `src/pi` and the
envelope both exchange in `src/shared` (see
[ADR-0002](../decisions/0002-split-source-by-runtime-pc-pi-shared.md)).

## Quick start: local roundtrip

These steps reproduce the full Raspberry Pi → PC → Raspberry Pi roundtrip on a
single machine. Install the project once:

```bash
python -m pip install -e ".[dev]"
```

Terminal 1, the PC server (defaults: `127.0.0.1:8000`, `stub` provider):

```bash
voicestock-pc-server
```

Terminal 2, the Raspberry Pi client:

```bash
voicestock-pi-client "agregá dos paquetes de arroz"
```

Expected output, exit code `0`:

```json
{
  "status": "success",
  "payload": {
    "status": "success",
    "payload": {
      "recognized_text": "agregá dos paquetes de arroz"
    },
    "error": null
  },
  "error": null
}
```

`voicestock-pi-client` sends one text and prints the resulting
`TransportEnvelope`. It exits with `0` for a success envelope, `1` for an error
envelope and `2` when no text is given. It exists for manual verification; the
rest of the Raspberry system uses the client class directly
(see [Raspberry Pi client](#raspberry-pi-client)).

## Running on the local network

On the real setup the server runs on the PC and the client on the Raspberry Pi,
connected through the isolated Ethernet network provided by `LocalNetworkInfra`.
This interface only consumes that network: it does not configure addresses or
the firewall. How to prepare the link is the
[Ethernet setup guide](../setup/local-network.md).

1. **PC: start the server listening on the network.** The default
   `127.0.0.1` only accepts local connections:

   ```bash
   VOICESTOCK_PC_HOST=0.0.0.0 VOICESTOCK_PC_PORT=8123 voicestock-pc-server
   ```

   The PC firewall must allow that TCP port on the isolated network. Do not
   expose this unauthenticated endpoint to an untrusted network.

2. **PC: use its VoiceStock Ethernet address**, `192.168.50.2`. That address
   is applied by the [Ethernet setup guide](../setup/local-network.md). Do not
   use the PC's Wi-Fi address for this client.

3. **Raspberry Pi: point the client at the PC** and send a text:

   ```bash
   export VOICESTOCK_PC_URL=http://<pc-ip>:8123
   export VOICESTOCK_PC_TIMEOUT=10
   voicestock-pi-client "agregá dos paquetes de arroz"
   ```

   The expected output is the same success envelope as in the quick start.
   The client needs no Internet access, only a route to the PC.

If the client prints `connection_failed`, check that the server is running with
`VOICESTOCK_PC_HOST=0.0.0.0`, the IP and port, and the PC firewall. If it
prints `timeout`, the PC accepted the connection but did not answer in time.

## Endpoint

```text
POST /api/v1/interpret
Content-Type: application/json
```

### Request

```json
{
  "text": "agregá dos paquetes de arroz"
}
```

Rules:

- `text` is required and must be a non-blank JSON string;
- text is exchanged as UTF-8 JSON: `á` travels as the bytes `c3 a1`;
- unknown fields are rejected;
- the request does not contain audio, inventory or provider configuration.

### Successful response

`200 OK`. With the stub provider active, the payload is the `ServiceResult`
shown in the [quick start](#quick-start-local-roundtrip).

`payload` is opaque to RaspberryPiPCCommunication. A typed service error is
still a successfully transported payload and is never converted into a
transport error:

```json
{
  "status": "success",
  "payload": {
    "status": "error",
    "payload": null,
    "error": {
      "code": "provider_not_configured",
      "detail": "no provider available for 'gpt'"
    }
  },
  "error": null
}
```

The caller must therefore check the outer `status` first (did the message
travel?) and then the inner `status` (could the text be interpreted?). The
service error codes are documented in the
[InterpretationService interface](interpretation-service.md).

### Error response

Every communication error, from the server or the client, is a
`TransportEnvelope` with `status: "error"`, `payload: null` and a code:

```json
{
  "status": "error",
  "payload": null,
  "error": {
    "code": "invalid_request",
    "detail": "request body is not valid"
  }
}
```

`code` is stable and machine-readable. `detail` is diagnostic and must not be
used for program flow. The codes are listed in the
[error catalogue](#communication-error-catalogue).

## Raspberry Pi client

`HttpInterpretationClient` is the Raspberry Pi side of this interface. The rest
of the Raspberry system must depend on the `InterpretationClient` protocol, not
on HTTP:

```python
class InterpretationClient(Protocol):
    def interpret(self, text: str) -> TransportEnvelope: ...
```

Every call returns a `TransportEnvelope` and never raises for a communication
failure. The caller checks the outer `status` and, on success, hands `payload`
to the next layer, which reads the inner `ServiceResult`:

```python
from pi.communication import ClientSettings, HttpInterpretationClient

with HttpInterpretationClient(ClientSettings.from_environment()) as client:
    envelope = client.interpret("agregá dos paquetes de arroz")

if envelope.status == "success":
    service_result = envelope.payload
else:
    handle_communication_error(envelope.error.code)
```

What the client does and does not do:

- it accepts any string, including blank text: the server decides whether the
  request is valid and its error envelope reaches the caller unchanged;
- it sends `{"text": ...}` as UTF-8 JSON with
  `Content-Type: application/json; charset=utf-8`;
- it validates only HTTP status, encoding, JSON and the `TransportEnvelope`
  shape, never the payload;
- it does not know interpretation providers or the operation schema;
- it makes exactly one request per call: no retries and no flow recovery;
- it does not need Internet, only a route to the PC.

### Configuration

| Variable | Side | Default | Meaning |
|---|---|---|---|
| `VOICESTOCK_PC_HOST` | PC | `127.0.0.1` | Interface the server listens on; `0.0.0.0` for the network. |
| `VOICESTOCK_PC_PORT` | PC | `8000` | TCP port of the server. |
| `VOICESTOCK_PC_URL` | Raspberry Pi | `http://127.0.0.1:8000` | Base URL of the PC server; `http` or `https` with a host. |
| `VOICESTOCK_PC_TIMEOUT` | Raspberry Pi | `10` | Seconds; finite and positive. |

The timeout applies separately to each phase of the request: connecting,
sending and waiting for the response. A server that is down or silent
therefore produces an error for the caller instead of blocking indefinitely.
The default leaves room for a slow interpretation provider.

## Communication error catalogue

Server codes come from the PC in an HTTP error response. Client codes are
produced on the Raspberry Pi when no usable response arrives; they never
collide with server codes. The client passes server envelopes through
unchanged, so the caller sees one list of codes.

| Code | Side | HTTP | Cause |
|---|---|---|---|
| `invalid_json` | Server | `400` | The body is not valid UTF-8 JSON. |
| `unsupported_media_type` | Server | `415` | `Content-Type` is not `application/json`. |
| `invalid_request` | Server | `422` | The JSON does not match the request (blank or non-string `text`, unknown fields). |
| `handler_failure` | Server | `500` | The replaceable handler raised an exception. |
| `serialization_failure` | Server | `500` | The handler returned a value that cannot be encoded as JSON. |
| `timeout` | Client | — | Connecting, sending or waiting for the response exceeded the timeout. |
| `connection_failed` | Client | — | Connection refused, reset or lost. |
| `request_encoding_failure` | Client | — | The text cannot be encoded as UTF-8 JSON (for example, a lone surrogate); nothing was sent. |
| `unexpected_status` | Client | any | The HTTP status contradicts the envelope, or a non-200 response has no error envelope. |
| `invalid_response_encoding` | Client | `200` | The response body is not UTF-8 JSON. |
| `invalid_envelope` | Client | `200` | The response body is JSON but not a valid `TransportEnvelope`. |

### Reproducing each error

With the server running as in the [quick start](#quick-start-local-roundtrip),
each command below prints an error envelope. Only `error` is shown; `status`
is `"error"` and `payload` is `null` in all of them.

**Server rejects the request (`invalid_request`).** Blank text:

```bash
voicestock-pi-client " "
```

```json
"error": { "code": "invalid_request", "detail": "request body is not valid" }
```

**Request encoding, server side (`invalid_json`).** A body with a byte that is
not valid UTF-8:

```bash
printf '{"text":"arroz \xff"}' | curl -s -i -X POST \
  http://127.0.0.1:8000/api/v1/interpret \
  -H "Content-Type: application/json" --data-binary @-
```

```text
HTTP/1.1 400 Bad Request
{"status":"error","payload":null,"error":{"code":"invalid_json","detail":"request body is not valid JSON"}}
```

**Wrong media type (`unsupported_media_type`):**

```bash
curl -s -i -X POST http://127.0.0.1:8000/api/v1/interpret \
  -H "Content-Type: text/plain" --data 'arroz'
```

```text
HTTP/1.1 415 Unsupported Media Type
{"status":"error","payload":null,"error":{"code":"unsupported_media_type","detail":"Content-Type must be application/json"}}
```

**Request encoding, client side (`request_encoding_failure`).** Text that is
not valid Unicode is rejected before anything is sent:

```bash
python -c '
from pi.communication import ClientSettings, HttpInterpretationClient
with HttpInterpretationClient(ClientSettings.from_environment()) as client:
    print(client.interpret("arroz \ud800").model_dump_json(indent=2))'
```

```json
"error": { "code": "request_encoding_failure", "detail": "text cannot be encoded as UTF-8 JSON" }
```

**Unexpected status (`unexpected_status`).** A URL with a wrong path reaches
the server, which answers `404` without an envelope:

```bash
VOICESTOCK_PC_URL=http://127.0.0.1:8000/wrong voicestock-pi-client arroz
```

```json
"error": { "code": "unexpected_status", "detail": "unexpected HTTP status 404" }
```

**Connection failure (`connection_failed`).** Stop the server and run:

```bash
voicestock-pi-client arroz
```

```json
"error": { "code": "connection_failed", "detail": "could not communicate with the PC server" }
```

**Timeout (`timeout`).** A socket that accepts connections but never answers
simulates a stuck PC. In one terminal:

```bash
python -c "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',8124)); s.listen(); time.sleep(60)"
```

In another, the client gives up after about one second:

```bash
VOICESTOCK_PC_URL=http://127.0.0.1:8124 VOICESTOCK_PC_TIMEOUT=1 voicestock-pi-client arroz
```

```json
"error": { "code": "timeout", "detail": "no response within 1.0 seconds" }
```

The remaining codes need a faulty handler or a non-conforming server, which
the stub provider cannot produce. Automated tests verify them:

| Code | Test |
|---|---|
| `handler_failure` | `tests/pc/communication/test_server.py::test_interpret_converts_handler_exception_to_transport_error` |
| `serialization_failure` | `tests/pc/communication/test_server.py::test_interpret_rejects_non_serializable_handler_result` |
| `invalid_response_encoding`, `invalid_envelope`, `unexpected_status` | `tests/pi/communication/test_client.py::test_malformed_responses_are_distinguishable` |

## Replaceable handler

`create_app(handler)` receives a callable with this conceptual contract:

```python
def handler(text: str) -> object:
    ...
```

The HTTP adapter validates only the transport request, invokes the callable and
serializes its opaque result. The handler must return a JSON-serializable value
and should not raise: an exception becomes `handler_failure`, and a
non-serializable value becomes `serialization_failure`. In production the
handler is `InterpretationService.interpret`, which always returns a
`ServiceResult`; tests may pass any callable.

## Automated verification

```bash
pytest tests/pc/communication tests/pc/test_pc_main.py tests/pi \
  tests/shared tests/integration tests/test_architecture.py
```

- `tests/pc/communication/test_server.py` exercises the FastAPI request/response
  path through HTTPX's ASGI transport: valid Spanish text, malformed JSON,
  invalid request shapes, unsupported media type, handler failure and
  serialization failure.
- `tests/pi/communication/test_client.py` uses HTTPX's `MockTransport`: happy
  path, UTF-8 encoding, payload and server error pass-through, every client
  error code and the absence of retries.
- `tests/shared/communication/test_contracts.py` covers envelope invariants;
  `tests/pc/communication/test_server_settings.py` and
  `tests/pi/communication/test_client_settings.py` cover configuration.
- `tests/pc/test_pc_main.py` covers the path PC server →
  `InterpretationService` → provider.
- `tests/integration/test_pi_pc_roundtrip.py` and `tests/pi/test_pi_main.py`
  use real localhost sockets: a roundtrip through the actual PC server, a
  refused connection and a silent socket that must end in `timeout`.
- `tests/test_architecture.py` checks the import boundaries: `pc` and `pi`
  never import each other, `shared` imports neither, `pc.communication` does
  not know `pc.interpretation` and no second HTTP server exists.

## Pending physical verification

The roundtrip has not yet been run between the physical PC and Raspberry Pi.
The PC address on the VoiceStock Ethernet link is `192.168.50.2`. Evidence of
that physical roundtrip is still pending.
