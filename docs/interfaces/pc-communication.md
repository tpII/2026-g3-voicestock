# Raspberry Pi–PC communication interface

## Purpose

This interface transports recognized text from the Raspberry Pi to a
replaceable handler running on the PC. It does not perform speech recognition,
interpret inventory commands, validate products or modify inventory.

The protocol choice is recorded in
[ADR-0001](../decisions/0001-use-http-json-for-pi-pc-communication.md).

## Responsibilities by layer

```text
HTTP request/response
└── TransportEnvelope<T>                 RaspberryPiPCCommunication
    └── ServiceResult<ContractPayload>   InterpretationService
        └── ContractPayload              OperationContractValidation
```

The server's handler is `InterpretationService.interpret`, wired in
`src/voicestock/pc_server.py`. That module is the only one that knows both
layers: the communication package does not import the interpretation package.

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
- text is exchanged as UTF-8 JSON;
- unknown fields are rejected;
- the request does not contain audio, inventory or provider configuration.

### Successful response

With the stub provider active, the payload is the `ServiceResult`:

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

`payload` is opaque to `RaspberryPiPCCommunication`. A typed service error is
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

The Raspberry client must therefore check the outer `status` first (did the
message arrive?) and then the inner `status` (could the text be interpreted?).
The service error codes are documented in the
[InterpretationService interface](interpretation-service.md).

### Error response

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
used for program flow.

| HTTP status | Error code | Meaning |
|---|---|---|
| `400` | `invalid_json` | The body is not valid JSON. |
| `415` | `unsupported_media_type` | `Content-Type` is not `application/json`. |
| `422` | `invalid_request` | The JSON does not match the transport request. |
| `500` | `handler_failure` | The replaceable handler raised an exception. |
| `500` | `serialization_failure` | The handler returned a value that cannot be encoded as JSON. |

Connection refusal, connection loss and client-side timeout do not produce an
HTTP response or a `TransportEnvelope`; the Raspberry client represents them as
local transport failures (see [client error codes](#client-error-codes)).

## Run the server

Install the project and development dependencies once:

```bash
python -m pip install -e ".[dev]"
```

Start the server. The interpretation provider defaults to the deterministic
stub:

```bash
voicestock-pc-server
```

The safe development defaults are `127.0.0.1:8000`. To accept connections from
the isolated LAN:

```bash
VOICESTOCK_PC_HOST=0.0.0.0 \
VOICESTOCK_PC_PORT=8123 \
voicestock-pc-server
```

The active PC firewall must allow the selected TCP port on the isolated network.
Do not expose this unauthenticated MVP endpoint to an untrusted network.

## Manual roundtrip

```bash
curl -i \
  -X POST http://127.0.0.1:8000/api/v1/interpret \
  -H "Content-Type: application/json" \
  --data '{"text":"agregá dos paquetes de arroz"}'
```

Expected status: `200 OK`. While the stub provider is active, the inner
`ServiceResult` payload echoes the recognized text.

A service error can be checked by selecting an unregistered provider:

```bash
VOICESTOCK_INTERPRETATION_PROVIDER=gpt voicestock-pc-server
```

The same request then returns `200 OK` with an inner `ServiceResult` whose
error code is `provider_not_configured`.

An invalid request can be checked with:

```bash
curl -i \
  -X POST http://127.0.0.1:8000/api/v1/interpret \
  -H "Content-Type: application/json" \
  --data '{"text":42}'
```

Expected status: `422 Unprocessable Content` with error code
`invalid_request`.

## Replaceable handler

`create_app(handler)` receives a callable with this conceptual contract:

```python
def handler(text: str) -> object:
    ...
```

The HTTP adapter validates only the transport request, invokes the callable and
serializes its opaque result. The handler must return a JSON-serializable value.
In production the handler is `InterpretationService.interpret`; tests may pass
any callable.

## Automated verification

The component tests use HTTPX's ASGI transport, so they exercise the complete
FastAPI request/response path without reserving a real TCP port:

```bash
pytest tests/communication
```

They cover valid Spanish text, envelope invariants, malformed JSON, invalid
request shapes, unsupported media type, handler failure, serialization failure
and host/port configuration.

`tests/test_pc_server.py` covers the integrated path PC server →
`InterpretationService` → provider: success, each service error inside a
successful envelope, transport errors that never reach the service, and import
checks ensuring the communication package does not know the interpretation
package and that no second HTTP server exists.

## Raspberry Pi client

`HttpInterpretationClient` is the Raspberry Pi side of this interface. The rest
of the Raspberry system must depend on the `InterpretationClient` protocol, not
on HTTP:

```python
class InterpretationClient(Protocol):
    def interpret(self, text: str) -> TransportEnvelope: ...
```

Every call returns a `TransportEnvelope` and never raises for a communication
failure. The caller checks the outer `status` (did the message travel?) and,
on success, hands `payload` to the next layer, which reads the inner
`ServiceResult`.

```python
from voicestock.communication import ClientSettings, HttpInterpretationClient

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
  shape: the payload is returned intact, even if its domain content is invalid;
- it does not know interpretation providers or the operation schema;
- it makes exactly one request per call: no retries and no flow recovery;
- it does not need Internet, only a route to the PC on the local network.

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `VOICESTOCK_PC_URL` | `http://127.0.0.1:8000` | Base URL of the PC server. |
| `VOICESTOCK_PC_TIMEOUT` | `10` | Seconds; must be finite and positive. |

`VOICESTOCK_PC_URL` must be an `http` or `https` URL with a host. The client
only consumes this address: assigning the PC a stable IP on the isolated
network belongs to `LocalNetworkInfra`, which has not fixed the addressing
plan yet. Until then, use the PC's current LAN IP and the port chosen with
`VOICESTOCK_PC_PORT`:

```bash
VOICESTOCK_PC_URL=http://<pc-ip>:8123
```

The timeout applies separately to each phase of the request: connecting,
sending and waiting for the response. A server that is down or silent
therefore returns an error to the caller instead of blocking indefinitely.
The default leaves room for a slow interpretation provider.

### Client error codes

Errors detected on the Raspberry use their own codes, which never collide with
the server codes above. In both cases the envelope has `status: "error"` and
`payload: null`.

| Error code | Meaning |
|---|---|
| `timeout` | Connecting, sending or waiting for the response exceeded the timeout. |
| `connection_failed` | Connection refused, reset or lost; nothing usable was received. |
| `request_encoding_failure` | The text cannot be encoded as UTF-8 JSON (for example, a lone surrogate); nothing was sent. |
| `unexpected_status` | The HTTP status does not match the envelope, or a non-200 response has no error envelope (for example, a 404 page from a wrong URL). |
| `invalid_response_encoding` | A 200 response body is not UTF-8 JSON. |
| `invalid_envelope` | A 200 response body is JSON but not a valid `TransportEnvelope`. |

Server error envelopes (`invalid_request`, `handler_failure`, etc.) are passed
through unchanged.

### Manual client check

With the server running (`voicestock-pc-server`):

```bash
python -c '
from voicestock.communication import ClientSettings, HttpInterpretationClient
with HttpInterpretationClient(ClientSettings.from_environment()) as client:
    print(client.interpret("agregá dos paquetes de arroz").model_dump_json())
'
```

Expected output: a success envelope whose inner `ServiceResult` echoes the
text. With the server stopped, the same command prints an error envelope with
code `connection_failed`.

### Automated client verification

```bash
pytest tests/communication/test_client.py tests/test_client_roundtrip.py
```

`tests/communication/test_client.py` uses HTTPX's `MockTransport` to cover the
happy path, UTF-8 encoding, payload pass-through, server error pass-through,
every client error code and the absence of retries.

`tests/test_client_roundtrip.py` uses real localhost sockets: a roundtrip
through the actual PC server and `InterpretationService`, a refused
connection on a closed port, and a socket that accepts the connection but
never answers, which must end in `timeout`.

## Pending physical verification

The client has not yet been run on the Raspberry Pi hardware. Once
`LocalNetworkInfra` provides the isolated network, this document must add the
PC address to use and the evidence of a physical PC–Raspberry roundtrip.
