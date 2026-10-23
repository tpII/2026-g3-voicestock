# Operation contract interface

## Purpose

The operation contract is the JSON the PC sends to the Raspberry Pi to request
one inventory operation. The PC produces it from the interpretation of a spoken
command; the Raspberry Pi validates it and either turns it into a
`ValidatedOperation` or rejects it.

This document is enough to produce or validate a version 1 payload. The
machine-readable schema is
[`schemas/contract-payload-v1.schema.json`](schemas/contract-payload-v1.schema.json).

A payload is a request, not an operation. **A rejected payload never becomes a
pending operation and never moves stock.** A `ValidatedOperation` does not move
stock either: it only becomes a pending operation that the operator still has
to confirm.

## Responsibilities

```text
PC
  InterpretationDraft            StructuredCommandInterpretation
        │
        ▼
  map_draft                      OperationContractValidation (PC)
        │
        ▼
  ContractPayload  ── HTTP ──►   this contract
                                 Raspberry Pi
        │
        ▼
  OperationValidator             OperationContractValidation (Raspberry Pi)
        │
        ├──► ValidationRejection     no pending operation, no stock change
        ▼
  ValidatedOperation
        │
        ▼
  PendingOperationFlow           waits for operator confirmation
```

| Component | Responsibility |
|---|---|
| StructuredCommandInterpretation | Produces the `InterpretationDraft`. It does not know or emit `ContractPayload`. |
| OperationContractValidation, PC side | `pc.operation_contract.map_draft` is the only producer of `ContractPayload`. |
| OperationContractValidation, Raspberry Pi side | `pi.operation_contract.OperationValidator` produces `ValidatedOperation` or `ValidationRejection`. It is the authority on the validity of a payload and on product identity. |
| ProductCatalog | Will implement the `ProductResolver` port on top of persistence. |
| PendingOperationFlow | Consumes only `ValidatedOperation`. A rejection ends the attempt without creating a pending operation. The cycle is [the operation workflow](../architecture/pending-operation-flow.md). |

The canonical definition is the pydantic model `shared.operation_contract.ContractPayload`,
which both sides import, so the producer and the validator cannot keep diverging
copies. The contract travels as the `payload` of a successful `ServiceResult`
inside a `TransportEnvelope`; see the
[InterpretationService interface](interpretation-service.md#layer-chain).

Out of scope for this contract: the SQLite catalog, the web interface and the
recovery policy after a failure. They belong to ProductCatalog,
PendingOperationWeb and FaultHandlingRecovery.

## Contract version 1

```json
{
  "contract_version": "1",
  "operations": [
    {
      "operation": "add_stock",
      "product": {
        "name": "Coca Cola Zero 2L",
        "brand": null,
        "variant": null,
        "presentation": null
      },
      "quantity": 2,
      "unit": "unit"
    }
  ]
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `contract_version` | string | yes | Always `"1"` for this version. Any other value is rejected. |
| `operations` | array of objects | yes | Requested operations. Version 1 accepts exactly one item; see [Operation count](#operation-count). |
| `operations[].operation` | string | yes | `add_stock` (stock received) or `remove_stock` (stock taken out). |
| `operations[].product` | object | yes | Description of the product, not its identity. |
| `operations[].product.name` | string | yes | Product name, such as `Coca Cola Zero 2L` or `Arroz`. |
| `operations[].product.brand` | string or null | no | Brand, such as `Gallo`. |
| `operations[].product.variant` | string or null | no | Variant, such as `Zero`. |
| `operations[].product.presentation` | string or null | no | Size or package, such as `1 kg`. |
| `operations[].quantity` | integer | yes | Number of units. It must be positive; see [Semantic rules](#semantic-rules). |
| `operations[].unit` | string | yes | Always `"unit"`: version 1 only counts items. |

Rules that apply to every level:

- **Unknown fields are rejected.** There is deliberately no `product_id`: the
  model cannot choose a product.
- **Types are strict.** `"2"`, `2.0` and `true` are not integers, and a number
  is not a string.
- Optional product attributes may be omitted or sent as `null`.
- The payload is UTF-8 JSON. Names keep their accents (`Serenísima`).

## Producing a payload on the PC

The interpreter's draft is, for now, the JSON the model returns:

```json
{"operaciones": [{"operacion": "agregar_stock", "producto": "Coca Cola Zero 2L", "cantidad": 2}]}
```

`map_draft` translates it:

| Draft | Contract |
|---|---|
| `operacion: "agregar_stock"` | `operation: "add_stock"` |
| `operacion: "restar_stock"` | `operation: "remove_stock"` |
| `producto` | `product.name`, unchanged |
| `cantidad` | `quantity` |
| no unit | `unit: "unit"` |

```python
from pc.operation_contract import DraftMappingError, map_draft

try:
    payload = map_draft(draft)
except DraftMappingError:
    ...  # report a typed service error; never send a partial payload

wire_value = payload.model_dump(mode="json")
```

`map_draft` raises `DraftMappingError` when a field is missing or unknown, the
operation is not in its vocabulary, the product is blank or the quantity is not
an integer. It never completes a field to produce a payload. It does not
validate the domain: the operation count, the sign of the quantity and the
existence of the product are checked on the Raspberry Pi.

When the interpreter defines a typed `InterpretationDraft`, only the input side
of `map_draft` changes; the contract stays the same.

## Validating a payload on the Raspberry Pi

```python
from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    ValidatedOperation,
    load_catalog,
)

validator = OperationValidator(InMemoryProductResolver(load_catalog(catalog_path)))

result = validator.validate(service_result_payload)   # already decoded JSON
# or: validator.validate_json(raw_bytes)              # raw JSON document

if isinstance(result, ValidatedOperation):
    ...  # hand it to PendingOperationFlow
else:
    ...  # result.reason explains why; no pending operation is created
```

The validator runs three stages in order. The first stage that fails decides
the rejection:

1. **Structural.** The payload is JSON, has a supported version and the
   expected fields and types.
2. **Product identification.** The product description identifies exactly
   one catalog product.
3. **Semantic rules.** The quantity and unit are acceptable for that product.

A valid payload produces:

```python
ValidatedOperation(
    operation="add_stock",
    product_id="coca-cola-zero-2l",   # assigned by the catalog, never by the model
    product_name="Coca Cola Zero 2L", # catalog label to show the operator
    quantity=2,
    unit="unit",
)
```

## Product identification

The policy is [ADR-0006](../decisions/0006-identify-products-by-unique-attribute-match.md).
In short:

1. Every attribute is normalized: accents and case are ignored, every
   character that is not a letter or digit becomes a space, and runs of spaces
   collapse. `Coca-Cola`, `coca cola` and `COCA  COLA` are equal; `1 kg` and
   `1kg` are not.
2. A catalog product is a candidate when it has every attribute present in the
   payload with the same normalized value. Attributes absent from the payload
   do not constrain the search.
3. Exactly one candidate identifies the product. None is `unknown_product`.
   Several are `ambiguous_product`, and there is no tie-breaking. A name that
   is empty after normalization is `insufficient_product_attributes`.

Each attribute is compared as a whole, not by prefix. With the October catalog,
which uses full names such as `Coca Cola Zero 2L`, the name `Coca Cola` is
`unknown_product`.

Identification goes through a port that does not depend on storage:

```python
class ProductResolver(Protocol):
    def resolve(self, query: ProductQuery) -> ProductResolution: ...
```

`InMemoryProductResolver` is the current implementation. When it is built, it
checks that every product is identifiable by its own attributes and that no
identifier repeats. ProductCatalog must implement the same port and pass the
contract tests in `tests/pi/operation_contract/test_products.py`. Replacing the
catalog source does not change the JSON contract.

The October catalog is provisional:
`tests/fixtures/operation_contract/october_catalog.json`, with the ten products
of the precision benchmark. It will be replaced by the shared fixture of
StructuredCommandInterpretation.

## Semantic rules

| Rule | Rejection |
|---|---|
| `quantity` must be greater than zero. | `invalid_quantity` |
| `unit` must be one of the units the catalog product accepts (every October product accepts `unit`). | `incompatible_unit` |

Both operations are valid for every product of the October catalog.

## Rejections

A rejection is a `ValidationRejection(reason, detail, candidate_ids)`. Callers
branch on `reason`. `detail` is diagnostic text and must not be used for
program flow. `candidate_ids` is only set for `ambiguous_product`, for
diagnostics; none of the candidates is selected.

| Reason | Stage | Example payload | Example `detail` |
|---|---|---|---|
| `invalid_json` | structural | `{` | `payload is not valid UTF-8 JSON` |
| `invalid_structure` | structural | `quantity` missing | `operations.0.quantity: Field required` |
| `invalid_structure` | structural | `"quantity": "2"` | `operations.0.quantity: Input should be a valid integer` |
| `invalid_structure` | structural | `"product": {"name": "Sprite 2L", "product_id": "sprite-2l"}` | `operations.0.product.product_id: Extra inputs are not permitted` |
| `unsupported_version` | structural | `"contract_version": "2"` | `contract version '2' is not supported; expected '1'` |
| `unknown_operation` | structural | `"operation": "transfer_stock"` | `operations.0.operation: Input should be 'add_stock' or 'remove_stock'` |
| `unknown_unit` | structural | `"unit": "kg"` | `operations.0.unit: Input should be 'unit'` |
| `no_operations` | structural | `"operations": []` | `payload contains no operations` |
| `too_many_operations` | structural | two items in `operations` | `payload contains 2 operations; at most 1 is supported` |
| `insufficient_product_attributes` | identification | `"name": " "` | `the product description has no usable name` |
| `unknown_product` | identification | `"name": "Pepsi 2L"` | `no catalog product matches the description` |
| `ambiguous_product` | identification | `"name": "Coca Cola"` with Original and Zero variants in the catalog | `several catalog products match the description` |
| `invalid_quantity` | semantic | `"quantity": 0` | `quantity must be positive, got 0` |
| `incompatible_unit` | semantic | a product counted only in `kg` | `product 'harina' is not counted in 'unit'` |

`unknown_operation` and `unknown_unit` are reported only when the vocabulary
value is the only problem; combined with any other error the payload is
`invalid_structure`. The version is checked before the fields, so a payload
written for another version is `unsupported_version`.

## Operation count

`operations` is a list because one spoken command can mention several products
("vendimos dos arroz y tres fideos"), and the interpreter already returns a
list. A pending operation holds exactly one operation, so version 1 accepts
exactly one item (`SUPPORTED_OPERATION_COUNT = 1`):

- an empty list means the command cancelled everything, and is rejected as
  `no_operations`;
- more than one item is rejected as `too_many_operations`.

Accepting several operations needs a change in PendingOperationFlow, not in the
shape of the contract.

## Introducing a new contract version

The Raspberry Pi supports exactly one version and rejects any other value as
`unsupported_version`, before reading the rest of the payload. A PC that sends
a newer version to an older Raspberry Pi therefore gets an explicit rejection
and never a misread operation.

To introduce version 2:

1. Change `ContractVersion` and the models in
   `src/shared/operation_contract/payload.py`.
2. Update `map_draft` and the validator stages in the same change, so the PC
   and the Raspberry Pi always agree.
3. Publish the new schema as `docs/interfaces/schemas/contract-payload-v2.schema.json`
   and update this document. `tests/shared/operation_contract/test_schema_artifact.py`
   fails until the published file matches the model.
4. Deploy the PC and the Raspberry Pi together. During the transition, the
   side that is not updated rejects the other version instead of guessing.

Supporting two versions at the same time is not needed while both sides are
deployed together.

## Regenerating the published schema

The JSON Schema file is generated from the model:

```bash
python -c "import json; from shared.operation_contract import contract_json_schema; print(json.dumps(contract_json_schema(), indent=2, ensure_ascii=False))" > docs/interfaces/schemas/contract-payload-v1.schema.json
```

## Automated verification

```bash
pytest tests/shared/operation_contract tests/pc/operation_contract \
  tests/pi/operation_contract tests/integration/test_contract_producer_validator.py
```

- `tests/shared/operation_contract`: the canonical model and the published schema.
- `tests/pc/operation_contract`: the mapper, with golden drafts taken from the
  precision benchmark (`tests/fixtures/operation_contract/golden_drafts.json`).
- `tests/pi/operation_contract`: every structural, identification and semantic
  rejection, the catalog invariant and the resolver port contract.
- `tests/integration/test_contract_producer_validator.py`: each golden draft
  goes through the mapper, `ServiceResult`, `TransportEnvelope`, JSON and the
  Raspberry Pi validator.
