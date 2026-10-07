# ADR-0004: Stock interpretation strategy and evaluation

## Status

Proposed

Proposal based on the September 2026 investigation, pending team review and
agreement on operational thresholds. This document records the supporting
evidence and the proposed decision; it is not a production interface specification.

## Context

VoiceStock needs to interpret Spanish inventory commands, including additions,
subtractions, corrections and cancellations. Interpretation runs on the PC,
not the Raspberry Pi, and must not modify inventory or persistence.
The provider must remain replaceable without changing transport or domain logic.

### Evaluated strategies

- Local inference on the PC through Ollama, primarily Qwen 3 4B Instruct.
- External inference through Groq, including GPT-OSS 20B, GPT-OSS 120B and
  Qwen 3.8 27B.
- External inference through Gemini, including Gemini 3.6 Flash.

The original local report contains the six-model comparison. Individual reports
are the source for the model identifiers and configurations used in each run.

### Comparison criteria

- Exact agreement with expected operations, products and quantities.
- Valid JSON and compliance with the experimental output schema.
- Correct handling of quantity corrections and single or multiple cancellations.
- Per-request latency and, for local inference, memory requirements.
- Connectivity, credentials, provider quotas and operational availability.

The original suite used an earlier product-and-quantity format. The precision
suite uses a list of operations and counts list order when checking exact match.
Successful response accuracy and complete-run coverage must be distinguished.

### Results and measurements

The [original benchmark](../testing/llm-benchmark.md) evaluated product and
quantity extraction using an earlier format. In the
[local model report](../../reports/llm-benchmark/benchmark_report.md), Qwen 3 4B
Instruct achieved 100% accuracy across five measured runs, with a **mean total
latency of 34.23 seconds** and peak RAM usage of approximately 3,132 MB. Warm-up
runs were excluded. It was the only one of the six local models compared to
achieve complete accuracy in that test.
The [precision benchmark](../../scripts/benchmarks/precision_benchmark.py)
extended the evaluation to ten cases covering operations, corrections,
cancellations and an integrated case. Results from the two suites are not
directly equivalent. The [observations](../../reports/llm-benchmark/observaciones.md)
preserve the comparison and link to individual runs.

The results relevant to this proposal are:

| Candidate | Observed result | Reported prompt contract | Mean latency per request |
| --- | --- | --- | --- |
| [Local Qwen 3 4B Instruct: original benchmark](../../reports/llm-benchmark/benchmark_report.md) | 5/5 correct runs of the same message | Original product and quantity format | **34.23 s** |
| [GPT-OSS 20B on Groq](../../reports/llm-benchmark/precision_20260929_213654/benchmark_report.md) | 10/10 correct cases, with no request errors | `contract.txt` | 0.63 s |
| [Gemini 3.6 Flash](../../reports/llm-benchmark/precision_20260929_202819/benchmark_report.md) | Correctly handled all cases evaluated across the two runs | `contract-copy.txt` and `contract.txt` | 3.23 s in the first run; 2.08 s for the additional case |

Gemini correctly handled the nine cases answered in the first run and
[the additional `negar_varias_agregaciones` case](../../reports/llm-benchmark/precision_20260929_204150/benchmark_report.md)
in a subsequent test. Coverage of all ten cases was verified across those two
runs, using the prompt contracts listed in the table.

These are measurements from the cited runs, not accuracy or performance
guarantees. Prompt contracts varied during the investigation, and the tests do
not include the complete audio, STT, transport and stock-update workflow. The
current evaluator also requires operations to appear in the same order as the
expected output. Ten cases refined during prompt development do not constitute
an independent evaluation of generalization.


A [local precision run](../../reports/llm-benchmark/precision_20260929_211830/benchmark_report.md)
also recorded 10/10 for Qwen 3 4B Instruct with `contract-copy.txt` and a mean
latency of 10.22 seconds. This does not replace the 34.23-second measurement from
the original suite: the prompts and workloads differ.

[GPT-OSS 120B achieved 8/10](../../reports/llm-benchmark/precision_20260929_213303/benchmark_report.md)
with `contract.txt`, whereas GPT-OSS 20B achieved 10/10 with that prompt contract
name. [Qwen 3.8 27B also achieved 10/10](../../reports/llm-benchmark/precision_20260929_212812/benchmark_report.md)
with `contract-copy-copy.txt`. Larger models did not consistently outperform
smaller ones on these experiments; this is not a general model ranking.

Local precision tests used schema-constrained output and `think: false`.
GPT-OSS 20B used a strict schema and `reasoning_effort: low`. Groq experiments
also recorded 403 rejections and 429 limits, which are execution issues rather
than semantic interpretation errors.

### Test limitations

- Contracts changed during prompt development, so these are not all controlled
  comparisons on one frozen configuration.
- Reports identify prompt filenames but do not preserve the effective prompt
  or all environment details needed for full reproduction.
- The small corpus was used while tuning prompts; it is not an independent
  generalization test.
- Units and relevant attributes are represented in product names, not evaluated
  as independently extracted fields.
- Audio, STT, transport and stock updates are outside the measured workflow.
- The catalog is small and closed. The script defines `PRODUCTS` and
  `PRODUCT_DETAILS` separately; a shared canonical fixture is not yet implemented.
- Historical experiments must not be described as having used the acceptance
  threshold established after those experiments.

## Decision

Qwen 3 4B Instruct demonstrates a feasible local interpretation path on the
tested corpus, without Internet or external quota dependencies. Its latency is
a significant deployment trade-off. GPT-OSS 20B on Groq and Gemini 3.6 Flash
demonstrate viable cloud alternatives on the evaluated cases with lower observed
latency, but require Internet access.

The proposed initial strategy remains local Qwen through Ollama, with GPT-OSS
20B as the preferred cloud alternative if agreed local latency or resource
limits cannot be met. This recommendation is provisional, not an accepted
production decision.

Encapsulate inference behind a replaceable provider interface and select one
provider by configuration. Use Ollama with `think: false` and schema-constrained
output for the proposed local implementation. Do not require simultaneous cloud
implementation or automatic fallback. The interpreter produces an
`InterpretationDraft`; OperationContractValidation owns deterministic catalog
matching, contract validation and mapping to the official JSON.

Use a closed, versioned canonical test catalog. Derive prompt context and
validation data from that same source rather than maintaining manual copies.
This fixture is not a replacement for persistent ProductCatalog or SQLite.

From now on, acceptance requires **100% exact match on the complete frozen corpus
in one run**. Each response must be valid JSON, satisfy the experimental schema
and match expected operations, products and quantities, including list order
under the current evaluator. Do not repair responses to count them as correct.
Omitted cases, incomplete responses and unanswered requests do not establish
acceptance. If multiple acceptance repetitions are performed, all must pass.
A targeted `--cases` run is diagnostic only.
Before a new go/no-go comparison, agree on latency, resource and cloud cost/quota
thresholds and freeze the corpus, expected outputs, catalog, prompt and schema.
Record their versions or hashes and effective model settings. Add independent
phrases and missing unit/attribute coverage before claiming the full task scope.

## Alternatives considered

- **GPT-OSS 20B on Groq as the initial provider:** faster in the evaluated
  workload, but depends on Internet access and provider quotas. Retained as the
  preferred cloud alternative if local operational thresholds cannot be met.
- **Gemini 3.6 Flash:** correctly handled all evaluated cases across the cited
  runs and remains a viable cloud alternative requiring Internet access.
- **Selecting a larger model solely by parameter count:** rejected as a selection
  rule because the experiments do not show a consistent task-specific advantage.
- **Independent catalogs for prompts and validation:** rejected because silent
  divergence can appear as an interpretation error.

## Consequences

### Positive

- A local interpretation path avoids Internet, credentials and external quotas.
- Provider substitution remains possible without coupling inventory to an API.
- A complete-corpus acceptance gate makes success and regression explicit.
- A canonical catalog keeps interpretation context and validation consistent.

### Negative

- Local latency and PC resource requirements may limit the voice experience.
- Perfect accuracy on this small corpus does not guarantee unseen-input accuracy.
- Schema-constrained generation does not prevent semantic errors.
- Reproducibility requires preserving more configuration than historical reports
  currently record.

### Follow-up

- Agree on operational thresholds and review the initial provider before marking
  this proposal as `Accepted`.
- Implement the selected adapter within InterpretationService boundaries;
  document the official interface separately without treating benchmark JSON
  as the production contract.
- Implement the canonical fixture and consistency tests with
  OperationContractValidation.
- Repeat the complete frozen corpus and evaluate independent new phrases,
  units, attributes and the STT-inclusive workflow on the target PC.
- Revisit the selection if a stable case regresses, model configuration changes,
  agreed local limits are not met or connectivity requirements change.
