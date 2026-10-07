# ADR-0002: Use a local LLM with a replaceable provider for stock interpretation

## Status

Proposed

Proposal based on benchmarks conducted in September 2026, pending team review.
The initial selection and integration described here do not yet constitute an
implementation of the application service.

## Context

VoiceStock needs to interpret Spanish text into inventory operations. The
evaluated scope covers `agregar_stock`, `restar_stock`, product and quantity,
including corrections and cancellations within a single message. The provider
must be replaceable without changing Raspberry Pi–PC communication or inventory
logic.

This decision addresses the evaluation in
[StructuredCommandInterpretation-01](https://app.clickup.com/t/86e3ev3f6) and the
strategy documentation in
[StructuredCommandInterpretation-03](https://app.clickup.com/t/86e3ev430).
The implementation scope also includes units and relevant attributes. Current
tests represent them through product names but do not yet demonstrate their
extraction as independent fields.

Two strategies were investigated: running a local model on the PC through
Ollama, or calling an external API from the PC. The former enables interpretation
without Internet access; the latter depends on connectivity, availability and
provider quotas. The Raspberry Pi communicates over the local network in both
strategies.

Local and cloud strategies were evaluated in
[the strategy and evaluation record](0004-stock-interpretation-strategy-and-evaluation.md).
That document preserves alternatives, measurements, test limitations and the
technical conclusion. This ADR records the proposed architectural decision.
## Decision

Propose **Qwen 3 4B Instruct running on the PC through Ollama** as the initial
interpretation provider, using `think: false` and JSON Schema-constrained output.
Prioritize a local path without Internet or external quota dependencies.
Acceptance remains conditional on validating latency and resources for voice
interaction; the supporting measurements are retained in the research document.

Encapsulate inference behind a replaceable provider interface within the
interpretation service. Select one provider through configuration; Ollama, Groq
and Gemini details must remain in their adapters. This increment may implement
only the local adapter. Neither simultaneous implementation of a cloud provider
nor automatic switching between providers is required.

The interpreter receives text and a projection of the authorized catalog and
produces an interpretation draft (`InterpretationDraft`). It does not modify
inventory or persistence, perform deterministic catalog matching, or emit the
official JSON. Under
[StructuredCommandInterpretation-04](https://app.clickup.com/t/86e3ev4cx), the
OperationContractValidation mapper owns that transformation. Contract validation
belongs to that component, not the LLM adapter. InterpretationService retains
coordination and provider substitution responsibilities; the Raspberry Pi does
not host the model. Raspberry Pi–PC transport retains responsibility for sending
and receiving messages.

Use [the benchmark contract and schema](../../scripts/benchmarks/precision_benchmark.py)
as an experimental reference for defining the production interface. Document
that interface in `docs/interfaces/` under OperationContractValidation ownership,
without duplicating it here. Benchmark JSON is not automatically the official
contract. Schema-constrained generation does not replace subsequent validation:
valid JSON can still contain omissions or incorrect cancellations. The shared
catalog is defined in
[ADR-0003](0003-use-canonical-test-catalog-for-interpretation.md).

Keep **GPT-OSS 20B on Groq** as the preferred cloud alternative if local latency
or resources prove insufficient and the deployment has Internet access. Its
evaluation used a strict schema and `reasoning_effort: low`. Switching to this
alternative requires reviewing availability and quotas and repeating validation
with the same stable prompt contract.

### Precision acceptance criterion

Establish, from this decision onward, a threshold of **100% exact match across
all cases in the acceptance corpus within a single complete run**. Each case
must produce valid JSON, satisfy the experimental schema and match the expected
output: operations, products and quantities, including corrections and
cancellations. With the current evaluator, list order also matters. Responses
must not be repaired to count them as correct.

A run with omitted cases, incomplete responses or unanswered requests does not
meet the threshold, even if the answered cases are correct. Reports must
distinguish interpretation failures from execution failures. A run using
`--cases` is diagnostic, not acceptance of the complete corpus. If multiple
acceptance repetitions are performed, all must meet the threshold; do not select
only the best run.

Before the next comparison, freeze the corpus, expected outputs, catalog, prompt
contract and schema. Record their versions or hashes and the effective model
configuration so that results can be reproduced. Compare models using that same
suite; a prompt change starts a different experiment.

The 100% threshold expresses acceptance on those cases, not a guarantee for
every possible phrase. Historical results support the proposal, but the
threshold is established now: it is not presented as a predefined criterion of
those experiments. Add independent new phrases and unit and attribute cases
before claiming coverage of the task's full scope.

Acceptable numerical limits for latency and local resources, and for cost and
quota when using a cloud alternative, remain to be agreed before another
go/no-go comparison. Precision alone does not establish operational viability;
the initial selection therefore remains `Proposed`.

## Alternatives considered

- **GPT-OSS 20B on Groq as the initial provider:** a viable, faster cloud path in
  the evaluated workload. Retained as the preferred alternative, rather than
  the initial choice, because this proposal prioritizes local operation.
- **Gemini 3.6 Flash:** correctly handled all evaluated cases across the cited
  runs and remains a viable cloud alternative requiring Internet connectivity.
- **Selecting by model size alone:** rejected because task-specific results do
  not establish a consistent advantage for larger models.
- **Implementing local and cloud providers together:** not required for the
  current increment; a replaceable interface preserves future options.

See the research document for detailed comparisons and individual reports.

## Consequences

### Positive

- Local interpretation does not depend on Internet access, credentials or cloud
  quotas.
- The initial selection is supported by a complete run with 10/10 correct cases.
- The replaceable interface enables evaluating another implementation without
  coupling transport or inventory to a provider.
- The common schema enables response validation and provider comparison using
  the same criteria.

### Negative

- Inference depends on PC resources and availability. Observed local latency
  may seriously affect the voice experience and must meet agreed operational
  limits before acceptance.
- The observed 10/10 does not guarantee accuracy on new phrases or erroneous
  transcriptions. Prompts and configuration can change results.
- Schema-constrained output does not prevent interpretation errors.
- Reports store the prompt contract name, but not a copy of the effective prompt
  or all environment information needed to reproduce them.

### Follow-up

- Review this proposal and approve the initial provider before marking the ADR
  as `Accepted`, including the pending operational thresholds. Maintain a single
  initial strategy; implementing both providers is not mandatory.
- Define the production contract, including empty operation lists, element
  order, ambiguous products, missing quantities and expected errors.
- Implement the selected adapter respecting the InterpretationService interface
  and OperationContractValidation boundaries, with automated tests that do not
  depend on external services.
- Evaluate new phrases and repeat tests with a frozen prompt contract, catalog
  and configuration. Measure latency and resources on the target PC and in the
  workflow that includes STT.
- Record the effective prompt or its verifiable version, schema, catalog, model
  and configuration for each run; separate API errors from accuracy results.
- If a cloud provider is adopted, define output limits, timeouts and bounded
  retries based on actual service errors and quotas.
- Revisit the selection if a stable-corpus case stops passing, the model or its
  configuration changes, the PC fails to meet the agreed latency, or connectivity
  requirements change. Do not switch providers solely because of model size.
