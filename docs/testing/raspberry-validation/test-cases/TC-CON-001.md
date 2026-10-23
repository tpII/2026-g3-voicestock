# TC-CON-001 — Operation contract validation on the Raspberry Pi

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that `OperationValidator` and `PcResponseInterpreter`, running on the
Raspberry Pi with the campaign catalog, accept the campaign contract and
reject the neighboring invalid payloads.

## Test level and type

Level: software component on the Raspberry Pi.

Type: functional. No GPIO, no microphone, and no PC process.

## Requirements and ClickUp traceability

- ClickUp: [OperationContractValidation-06](https://app.clickup.com/t/86e3ev73g).
- Requirement: structural validation, product identity, and the rejection
  reasons implemented in `pi.operation_contract`. The contract document is
  [operation contract](../../../interfaces/operation-contract.md). The
  machine-readable schema is
  [schemas/contract-payload-v1.schema.json](../../../interfaces/schemas/contract-payload-v1.schema.json).

## Source modules and documentation

- `pi.operation_contract.validator.OperationValidator`.
- `pi.operation_contract.products.load_catalog`.
- `pi.pending_operation.response.PcResponseInterpreter`.
- [Campaign fixtures](../fixtures/README.md).
- Automated tests under `tests/pi/operation_contract/` are not a substitute
  for this run on the Pi.

## Preconditions and dependencies

- [TC-ENV-001](TC-ENV-001.md) so the Pi Python is identified.
- The campaign fixtures are on the Pi at a known commit. The interpreter
  must be the project environment (`python` that imports `pi`).

## Required hardware and software

- Raspberry Pi and the project environment.
- No button and no network.

## Preparation

```bash
sha256sum docs/testing/raspberry-validation/fixtures/campaign-catalog.json \
  docs/testing/raspberry-validation/fixtures/contract-add-stock.json \
  docs/testing/raspberry-validation/fixtures/service-success-payload.json
```

## Execution

Run on the Pi from the repository root:

```bash
python - <<'PY'
import json
from pathlib import Path
from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    load_catalog,
)
from pi.pending_operation.response import PcResponseInterpreter
from shared.communication import TransportEnvelope

root = Path("docs/testing/raspberry-validation/fixtures")
validator = OperationValidator(
    InMemoryProductResolver(load_catalog(root / "campaign-catalog.json"))
)
accepted = json.loads((root / "contract-add-stock.json").read_text(encoding="utf-8"))
print("ACCEPT", validator.validate(accepted))

def show(label, payload):
    result = validator.validate(payload)
    reason = getattr(result, "reason", None)
    print(label, type(result).__name__, getattr(reason, "value", reason), getattr(result, "detail", ""))

show("UNKNOWN", {
    "contract_version": "1",
    "operations": [{
        "operation": "add_stock",
        "product": {"name": "Fideos", "brand": None, "variant": None, "presentation": None},
        "quantity": 1,
        "unit": "unit",
    }],
})
show("AMBIGUOUS", {
    "contract_version": "1",
    "operations": [{
        "operation": "add_stock",
        "product": {"name": "Arroz", "brand": "Marolio", "variant": None, "presentation": None},
        "quantity": 1,
        "unit": "unit",
    }],
})
show("QUANTITY", {
    "contract_version": "1",
    "operations": [{
        "operation": "add_stock",
        "product": {"name": "Arroz", "brand": "Marolio", "variant": None, "presentation": "1 kg"},
        "quantity": 0,
        "unit": "unit",
    }],
})
show("VERSION", {"contract_version": "2", "operations": []})
show("UNIT", {
    "contract_version": "1",
    "operations": [{
        "operation": "add_stock",
        "product": {"name": "Arroz", "brand": "Marolio", "variant": None, "presentation": "1 kg"},
        "quantity": 1,
        "unit": "kg",
    }],
})
show("EXTRA", {**accepted, "note": "not a contract field"})

service = json.loads((root / "service-success-payload.json").read_text(encoding="utf-8"))
envelope = TransportEnvelope.success({
    "status": "success",
    "payload": service,
    "error": None,
})
outcome = PcResponseInterpreter(validator).interpret(envelope)
print("INTERPRETER", outcome.kind.value, outcome.recognized_text, outcome.validated_operation)

rejected = TransportEnvelope.success({
    "status": "success",
    "payload": {"received_audio": {"size_bytes": 1}},
    "error": None,
})
print("STUB_SHAPE", PcResponseInterpreter(validator).interpret(rejected).kind.value)
PY
```

Repeat the process three times. The output must be identical. There is no
duration gate.

## Observations and evidence

- The transcript.
- Fixture checksums.

## Metrics

No timing metric. Identity of the three transcripts is the repeat.

## Acceptance criteria

1. `ACCEPT` prints `ValidatedOperation` with `product_id`
   `arroz-marolio-1kg`, `product_name` `Arroz Marolio 1 kg`, `quantity` 2,
   and `unit` `unit`.
2. `UNKNOWN` prints `unknown_product`.
3. `AMBIGUOUS` prints `ambiguous_product`.
4. `QUANTITY` prints `invalid_quantity`.
5. `VERSION` prints `unsupported_version`.
6. `UNIT` prints `unknown_unit`.
7. `EXTRA` prints `invalid_structure`.
8. `INTERPRETER` prints `accepted` and the synthetic recognized text from
   the fixture, with the same product id as criterion 1.
9. `STUB_SHAPE` prints `contract_rejection`. That is the classification of
   today's audio stub, checked here without a microphone.
10. Three runs print the same lines.

## Failure conditions

- Any reason string differs: **FAILED**.
- `load_catalog` raises: **FAILED**. The fixture is part of the
  specification and must load on the Pi's interpreter.
- The command was run only on a laptop: **FAILED** as a procedure
  deviation. A laptop run may be attached as a note. It is not this case.

## Recovery and cleanup

None. The command does not write a file and does not touch GPIO.

## Limitations and exclusions

This case does not prove the PC mapper emits these payloads. It does not
create a pending operation inside `voicestock-pi`. The flow's use of the
same interpreter is TC-FLOW-001. Product matching rules are not redesigned
here; they are the ones in
[ADR-0006](../../../decisions/0006-identify-products-by-unique-attribute-match.md).
