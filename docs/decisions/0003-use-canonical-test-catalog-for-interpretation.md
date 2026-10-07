# ADR-0003: Use a canonical test catalog for interpretation and validation

## Status

Proposed

Decision proposed for integration of the October increment. The current
benchmark keeps products and their details in the script; this ADR does not
claim that the shared fixture is already implemented.

## Context

Interpretation needs names, brands, variants, presentations and units to
distinguish products. Experiments showed that the prompt and product context
are part of the evaluated configuration: changing that information can change
the result, even when the model remains the same.

[StructuredCommandInterpretation-02](https://app.clickup.com/t/86e3ev3p3) requires
a closed, canonical, versioned test catalog shared with
OperationContractValidation. It does not require implementing SQLite or the
persistent ProductCatalog model in October.

The [strategy and evaluation record](0004-stock-interpretation-strategy-and-evaluation.md)
records the experimental catalog setup and its limitations. This ADR records
the shared-data decision, not the benchmark results or the fixture schema.

## Decision

Use a single closed, versioned catalog fixture as the source of truth for
interpretation, validation and integration tests. Agree on its minimum fields
with OperationContractValidation: product identity, canonical name and the
information needed to distinguish brand, variant, presentation and unit. The
exact fixture schema is documented alongside its implementation, not duplicated
in this ADR.

Derive the textual projection sent to the LLM and the catalog data consumed by
validation from the fixture. Do not maintain independent manual product copies
in prompts, test schemas or validators. The projection may be compact, but must
preserve the distinctions needed to identify presentations; it must not collapse
distinct products into an ambiguous name.

Add tests checking that every product expected by the cases exists in the
fixture and that the projection and validation data originate from the same
version. Include both unambiguous and ambiguous references to verify that the
system does not invent a selection when information is missing.

Record the version or hash of the fixture and its projection in each comparison.
A catalog change requires reviewing expected outputs and repeating the
acceptance corpus from
[ADR-0002](0002-use-local-llm-for-stock-interpretation.md).

The fixture is test infrastructure, not the inventory database or a replacement
for ProductCatalog. The interpreter uses its context to extract a draft;
deterministic matching and validation remain OperationContractValidation
responsibilities. The LLM does not modify the catalog or stock.

## Alternatives considered

- **Independent lists per component:** initially simple, but can silently diverge
  and turn a data inconsistency into an apparent model error.
- **Copying the entire catalog into each prompt:** makes examples easy to edit,
  but multiplies sources of truth and makes experiments harder to reproduce.
- **Implementing ProductCatalog and SQLite now:** introduces persistence outside
  the current scope; a closed fixture enables integration and testing without
  that dependency.
- **Accepting any generated name:** avoids maintaining references, but prevents
  detecting invented products and resolving presentations in a controlled way.

## Consequences

### Positive

- Interpretation and validation share the same identities and presentations.
- Results can be associated with a specific catalog version.
- Ambiguous cases can be tested without a production database.
- The LLM provider can change without changing the test-data source.

### Negative

- The fixture and its projection require maintenance and consistency tests.
- A small catalog does not demonstrate behavior with a large inventory.
- Changing products or presentations may invalidate earlier comparisons.

### Follow-up

- Agree on and implement the shared fixture with OperationContractValidation.
- Replace experimental lists with derived projections, preserving historical
  reports without rewriting their results.
- Document location, fields, version and projection rules alongside the fixture.
- Review this decision when a persistent ProductCatalog exists: retain a common
  source and separate acceptance data from production data.
