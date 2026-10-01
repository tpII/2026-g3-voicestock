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
HTTP response or a `TransportEnvelope`; the Raspberry client must represent them
as local transport failures.

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

## Pending Raspberry client work

The Raspberry client, destination address and timeout policy are not implemented
yet. Once available, this document must add:

- client setup and configuration;
- exact timeout behavior;
- connection-refused and connection-loss examples;
- a physical PC–Raspberry roundtrip over `LocalNetworkInfra`.
