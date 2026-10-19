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

The HTTP server calls the service through `src/pc/main.py`, and
each `ServiceResult` travels as the payload of a successful `TransportEnvelope`.
See the [Raspberry Pi–PC communication interface](pc-communication.md).

An empty or blank text is rejected by the HTTP layer as `invalid_request`
before reaching the service; `invalid_input` protects callers that use the
service directly.

## Layer chain

The service is one link in the path from recognized text to a pending
operation. Each layer has a single owner, and only the owner defines its shape.
The service carries the result of the interpretation; it does not define the
domain schema and does not decide whether an operation is acceptable.

```text
PC                                                                 owner
──────────────────────────────────────────────────────────────────────────────
recognized text
   │
   ▼
InterpretationService.interpret(text)               InterpretationService
   │
   ▼
InterpretationProvider  ──►  InterpretationDraft    StructuredCommandInterpretation
   │                                                internal, not versioned
   ▼
contract mapper  ──────────►  ContractPayload       OperationContractValidation
   │                                                versioned JSON contract
   ▼
ServiceResult<ContractPayload>                      InterpretationService
   │
   ▼
TransportEnvelope<ServiceResult>                    RaspberryPiPCCommunication
──────────────────────── HTTP, isolated local network ─────────────────────────
Raspberry Pi
   │
   ▼
structural validation  (version, fields, types)     OperationContractValidation
   │
   ▼
semantic validation and product identification      OperationContractValidation
   │
   ├──► ValidationRejection   no pending operation is created
   │
   ▼
ValidatedOperation
   │
   ▼
PendingOperation  (waits for operator confirmation) PendingOperationFlow
```

| Type | Owner | Runs on | Meaning | Specification |
|---|---|---|---|---|
| `InterpretationDraft` | StructuredCommandInterpretation | PC | Fields the model extracted from the text: operation, product attributes, quantity, unit. Tentative, internal and without a contract version. | Pending: [StructuredCommandInterpretation-04](https://app.clickup.com/t/86e3ev4cx) |
| `ContractPayload` | OperationContractValidation | PC → Raspberry Pi | The versioned operation contract. The mapper on the PC is the only producer; the Raspberry Pi validates it. | [Operation contract](operation-contract.md) |
| `ServiceResult` | InterpretationService | PC → Raspberry Pi | Could the text be interpreted? | [This document](#serviceresult) |
| `TransportEnvelope` | RaspberryPiPCCommunication | PC → Raspberry Pi | Did the message travel? | [Raspberry Pi–PC communication](pc-communication.md#responsibilities-by-layer) |
| `ValidatedOperation` / `ValidationRejection` | OperationContractValidation | Raspberry Pi | A contract that identifies exactly one product and satisfies the domain rules, or a rejection with its reason. | [Operation contract](operation-contract.md#validating-a-payload-on-the-raspberry-pi); policy in [ADR-0006](../decisions/0006-identify-products-by-unique-attribute-match.md) |
| `PendingOperation` | PendingOperationFlow | Raspberry Pi | A validated operation with its own identifier, waiting for confirmation. It does not modify inventory. | Pending: [PendingOperationFlow-01](https://app.clickup.com/t/86e3ev7md); web boundary in [the flow contract](../research/pending-operation-web-flow-contract.md) |

The contract mapper exists (`pc.operation_contract.map_draft`) but is not yet
wired into the service, because the only registered provider is the stub.
Until a real provider is connected through the mapper, the `payload` of a
successful `ServiceResult` is the raw output of the stub
(`{"recognized_text": ...}`). That payload is not a `ContractPayload`, and the
Raspberry Pi validator rejects it as `invalid_structure`.

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

`payload` is the provider output today and the `ContractPayload` once the
contract mapper exists (see [Layer chain](#layer-chain)). A success result
never carries an `error`, and an error result never carries a `payload`.
`code` is the stable category callers
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
from pc.interpretation import (
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

## Boundaries with other components

### StructuredCommandInterpretation

StructuredCommandInterpretation implements real providers against the
[provider contract](#provider-contract) and registers them in
`default_registry()`. The provider owns the prompt, the model client, its
credentials and timeouts, and the conversion of the model answer into an
`InterpretationDraft`.

- The service does not inspect the draft and does not know its fields.
- The provider does not know or emit `ContractPayload`: the official JSON
  belongs to the contract mapper.
- The provider does not assign product identity and does not modify inventory
  or persistence.
- When the model produces no usable interpretation, the provider raises
  `ProviderError` and the caller receives `provider_failure`. A provider must
  never complete missing fields to return a success.

### OperationContractValidation

OperationContractValidation owns both ends of the contract: the mapper on the
PC that turns an `InterpretationDraft` into a `ContractPayload`, and the
validation on the Raspberry Pi that turns a `ContractPayload` into a
`ValidatedOperation` or a `ValidationRejection`.

- The service never defines, versions or validates the contract schema. It only
  carries the mapper output as the `payload` of a success.
- A successful `ServiceResult` means that the text was interpreted, not that the
  operation is valid. Structural and semantic validation, and the decision about
  which product the operation refers to, happen only on the Raspberry Pi.
- A draft that cannot be mapped fails explicitly on the PC; it is not sent as a
  partial `ContractPayload`.

### FaultHandlingRecovery

The service only reports failures; it does not recover from them.

- Every failure is returned as a typed `ServiceResult` error: no retries, no
  fallback to another provider and no state kept between calls.
- `detail` is diagnostic. Callers branch on `code`.
- On the Raspberry Pi, a transport error, a typed service error or a
  `ValidationRejection` ends the attempt without creating a pending operation.
  That minimal return to idle belongs to PendingOperationFlow; retries,
  operator notification and recovery policy belong to FaultHandlingRecovery.

## Automated verification

```bash
pytest tests/pc/interpretation
```

The tests use in-memory providers only and never access the network. They
cover `ServiceResult` invariants and serialization, success through the stub,
provider substitution, every service error category, unexpected exceptions,
provider selection and an import check that keeps the module independent of
HTTP and other network transports.
