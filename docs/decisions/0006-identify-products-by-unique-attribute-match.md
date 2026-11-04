# ADR-0006: Identify products by a unique, normalized attribute match

## Status

Proposed — 17 October 2026. Team review remains pending. The resolution port
and its first implementation belong to
[OperationContractValidation-03](https://app.clickup.com/t/86e3ev69h).

## Context

The interpreter on the PC describes the product it understood with attributes
such as name, brand, variant and presentation. Before a pending operation is
created, the Raspberry Pi must decide whether those attributes identify exactly
one product or whether the interpretation must be rejected. The layer chain is
described in the
[InterpretationService interface](../interfaces/interpretation-service.md).

The decision must hold several constraints:

- the model is not an authority on product identity: it can misspell a name,
  invent an attribute or return an identifier that does not exist;
- the result must be deterministic, so the same payload and catalog always give
  the same answer;
- the October catalog is a test fixture, and the final ProductCatalog and SQLite
  do not exist yet;
- similar products are common: the benchmark catalog already contains
  «Coca Cola» and «Coca Cola Zero», and the STT step can produce «Coca-Cola».

This ADR covers identity only. Quantity, unit compatibility and operation rules
belong to semantic validation, and the shape of the JSON belongs to the
versioned schema of
[OperationContractValidation-02](https://app.clickup.com/t/86e3ev5y6).

## Decision

### Identity authority

The catalog is the only source of product identity. The `ContractPayload`
describes a product with attributes and never carries a product identifier
chosen by the model. The validator assigns the identifier of the matched catalog
entry, and only a `ValidatedOperation` exposes it.

### Attributes

The policy uses four attributes. The schema of OperationContractValidation-02
fixes their final field names and types.

| Attribute | Required in the payload | Example |
|---|---|---|
| `name` | Yes | `arroz` |
| `brand` | No | `Gallo` |
| `variant` | No | `Zero` |
| `presentation` | No | `1 kg` |

Every catalog entry has an opaque identifier, a `name` and any subset of the
optional attributes.

### Normalization

Before comparing, each attribute value of the payload and of the catalog goes
through the same normalization:

1. Unicode NFKD decomposition and removal of combining marks, so `Serenísima`
   and `Serenisima` are equal;
2. case folding;
3. every character that is not a letter or digit becomes a space, so
   `Coca-Cola` and `Coca Cola` are equal;
4. runs of spaces collapse into one, and leading and trailing spaces are
   removed.

No other transformation is applied: no synonyms, no stemming, no edit distance
and no phonetic matching. A value that is empty after normalization counts as
absent.

### Matching rule

A catalog entry is a candidate when, for every attribute present in the
payload, the entry has that attribute with the same normalized value. Attributes
absent from the payload do not constrain the search. An attribute present in the
payload but missing in the entry excludes the entry.

| Candidates | Result | Rejection reason |
|---|---|---|
| `name` is absent after normalization | Rejected | `insufficient_product_attributes` |
| none | Rejected | `unknown_product` |
| exactly one | Identified: the entry identifier is assigned | — |
| more than one | Rejected | `ambiguous_product` |

There is no tie-breaking. The validator never picks the most generic entry, the
most common one or the first one, and it never asks the model again. An
ambiguous rejection lists the candidate identifiers for diagnostics, but none of
them is selected.

Example with the catalog entries `{name: Coca Cola, variant: Original}` and
`{name: Coca Cola, variant: Zero}`:

| Payload | Result |
|---|---|
| `{name: "coca-cola", variant: "zero"}` | Identified: Coca Cola Zero |
| `{name: "Coca Cola"}` | `ambiguous_product` |
| `{name: "Coca Cola", variant: "Light"}` | `unknown_product` |

### Catalog invariant

Every catalog entry must be identifiable: querying with all of its own
attributes must return exactly that entry. Because absent attributes do not
constrain the search, an entry whose attributes are a subset of another entry's
attributes breaks this invariant. In the example above, a plain
`{name: Coca Cola}` next to the Zero variant would never be identifiable, so the
catalog has to give it a distinguishing attribute such as `variant: Original`.
Fixture tests must check this invariant, and ProductCatalog must enforce it when
it is built.

### Resolution port

Identification goes through a port that does not know SQLite:

```python
class ProductResolver(Protocol):
    def resolve(self, query: ProductQuery) -> ProductResolution: ...
```

- `ProductQuery` carries the attributes of one product from the payload.
- `ProductResolution` is one of: identified with a `product_id`, unknown,
  ambiguous with the candidate identifiers, or insufficient attributes.
- `product_id` is an opaque string owned by the catalog.

The October implementation keeps the catalog in memory and loads it from the
fixture shared with StructuredCommandInterpretation
([StructuredCommandInterpretation-02](https://app.clickup.com/t/86e3ev3p3)).
ProductCatalog will implement the same port later on top of persistence.
Normalization and matching are implemented once and reused, and a shared set of
contract tests must pass against every implementation, so replacing the source
changes neither the JSON schema nor the result of a query.

### Order of validation

Identification runs after structural validation, because it needs a
structurally valid `ContractPayload`. It runs before the semantic rules that
depend on the product, such as unit compatibility. Any rejection produces a
`ValidationRejection` and no pending operation is created.

## Alternatives considered

| Criterion | Exact composite key | Unique attribute subset (chosen) | Normalization | Identifier from the model |
|---|---|---|---|---|
| Deterministic | Yes | Yes | Yes | No: the model can return any value |
| Independent of the model | Yes | Yes | Yes | No |
| Covers the October test catalog | Partly: an omitted presentation fails | Yes | Not by itself | Only if the model copies identifiers correctly |
| Handles «Coca Cola» vs «Coca Cola Zero» | Yes | Yes, rejecting the ambiguous case | Not by itself | Not verifiable |
| Cost when ProductCatalog arrives | Low | Low: same port and invariant | Low | Couples the catalog to the prompt |

- **Exact composite key.** Every attribute, including the absent ones, must be
  equal. It is the strictest option, but it rejects correct commands that omit a
  detail that is not needed to tell products apart, such as the presentation of
  a product sold in a single size.
- **Unique attribute subset.** Chosen. It accepts every description that is
  precise enough and rejects the rest, and the catalog invariant keeps every
  product reachable.
- **Spelling and accent normalization.** It is not an identification rule on its
  own. It is adopted as a fixed, limited step of the chosen rule, because STT and
  the model already differ in accents, case and hyphens.
- **Identifier from the model.** Rejected. It makes the model the identity
  authority, it cannot detect a valid identifier that belongs to the wrong
  product, and it ties the prompt to the internal keys of the catalog.

Fuzzy matching by edit distance or by similarity score was also rejected: it
picks candidates by a hidden threshold, which is the heuristic this policy is
meant to avoid.

## Consequences

- The model cannot create a product or select one by identifier: a wrong or
  invented description becomes an explicit rejection.
- A command that does not name the variant, such as «agregá dos Coca Cola», is
  rejected as ambiguous when there are several Coca Cola variants. The operator
  has to repeat it with the variant. Usability then depends on the catalog using
  attributes that people actually say.
- The catalog must satisfy the invariant, and the fixture tests have to check it.
- The validator does not resolve synonyms or colloquial names, such as «coca»
  for «Coca Cola». The model may translate them into catalog values, because it
  receives the catalog as context, and the validator still checks the result.
  If the validator ever needs synonyms, they must be added as explicit catalog
  data, never as fuzzy matching.
- Normalization does not unify spacing inside a value: `1 kg` and `1kg` are
  different. The catalog and the prompt must use one spelling.
- Semantic validation and ProductCatalog can be implemented without reopening
  this decision.
