# InterpretationService interface

## Purpose

`InterpretationService` turns recognized text into a `ServiceResult` without
depending on which backend performs the interpretation. The backend is a
replaceable provider: a deterministic stub today, a local model or an external
API later.

The service does not know about HTTP, does not validate inventory operations
and does not modify inventory.

## Position in the pipeline

```text
POST /api/v1/interpret                     RaspberryPiPCCommunication
        │
        ▼
InterpretationService.interpret(text)      InterpretationService
        │
        ▼
InterpretationProvider.interpret(text)
   ├── StubProvider                        available
   ├── local model provider                pending
   └── external API provider               pending
```

The HTTP server calls the service through `src/voicestock/pc_server.py`, and
each `ServiceResult` travels as the payload of a successful `TransportEnvelope`.
See the [Raspberry Pi–PC communication interface](pc-communication.md).

An empty or blank text is rejected by the HTTP layer as `invalid_request`
before reaching the service; `invalid_input` protects callers that use the
service directly.

## ServiceResult

Every call returns a `ServiceResult`. Expected and unexpected provider failures
are converted into typed results instead of escaping as exceptions, so the HTTP
layer always transports them as a successful `TransportEnvelope` payload.

Success:

```json
{
  "status": "success",
  "payload": {
    "recognized_text": "agregá dos paquetes de arroz"
  },
  "error": null
}
```

Failure:

```json
{
  "status": "error",
  "payload": null,
  "error": {
    "code": "provider_not_configured",
    "detail": "no provider available for 'gpt'"
  }
}
```

`payload` is the provider output. It will become `ContractPayload` once
`OperationContractValidation` defines it. `code` is the stable category callers
branch on; `detail` is diagnostic, non-contractual and must not be used for
program flow.

| Error code | Meaning |
|---|---|
| `invalid_input` | The text is not a non-blank string. The provider is not called. |
| `provider_not_configured` | No provider is selected, or the selected name is not registered. |
| `provider_failure` | The provider raised `ProviderError` or any unexpected exception. |

Unexpected exceptions are reported as `provider_failure` with a generic detail,
so internal error messages are not sent to the Raspberry Pi. Finer categories,
such as timeouts of a real model, will be added when such a provider exists.

## Provider contract

```python
class InterpretationProvider(Protocol):
    def interpret(self, text: str) -> object: ...
```

A provider:

- receives the recognized text unchanged;
- returns a JSON-serializable payload;
- reports expected failures by raising `ProviderError`;
- owns its own configuration, timeouts and network access, so both a local
  model and an external API fit the same port.

## Selecting the provider

Providers are registered by name in a `ProviderRegistry`. `default_registry()`
contains every provider shipped with VoiceStock. The service receives the
registry and the active provider name, and resolves the provider itself:

```python
from voicestock.interpretation import (
    InterpretationService,
    InterpretationSettings,
    default_registry,
)

settings = InterpretationSettings.from_environment()
service = InterpretationService(default_registry(), settings.provider)
result = service.interpret("agregá dos paquetes de arroz")
```

The active provider name comes from an environment variable:

```bash
VOICESTOCK_INTERPRETATION_PROVIDER=stub
```

| Value | Result |
|---|---|
| `stub` (default) | `StubProvider`, deterministic and offline. |
| blank | Every call returns `provider_not_configured`. |
| unregistered name | Every call returns `provider_not_configured`. |

## Automated verification

```bash
pytest tests/interpretation
```

The tests use in-memory providers only and never access the network. They
cover `ServiceResult` invariants and serialization, success through the stub,
provider substitution, every service error category, unexpected exceptions,
provider selection and an import check that keeps the module independent of
HTTP and other network transports.
