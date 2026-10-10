# Stock interpretation strategy and evaluation

## Scope

This research preserves the September 2026 experiments and their limitations.
The API-first strategy and operational limits are recorded in
[ADR-0004](../decisions/0004-use-api-provider-for-stock-interpretation.md).
The benchmarks do not implement a production adapter.

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
guarantees. The two contract filenames cited for the selected candidates have
identical content when checked on 7 October 2026. The tests do
not include the complete audio, STT, transport and stock-update workflow. The
current evaluator also requires operations to appear in the same order as the
expected output. Ten cases refined during prompt development do not constitute
an independent evaluation of generalization.


A [local precision run](../../reports/llm-benchmark/precision_20260929_211830/benchmark_report.md)
also recorded 10/10 for Qwen 3 4B Instruct with `contract-copy.txt` and a mean
latency of 10.22 seconds. This does not replace the 34.23-second measurement from
the original suite: the prompts and workloads differ.

Historical observations mention additional GPT-OSS 120B and Qwen 3.8 27B
experiments, but their individual reports are not versioned in this repository.
Their numerical results cannot be independently checked from the available
evidence and are excluded from this comparison.

Local precision tests used schema-constrained output and `think: false`.
GPT-OSS 20B used a strict schema and `reasoning_effort: low`. Groq experiments
also recorded 403 rejections and 429 limits, which are execution issues rather
than semantic interpretation errors.

### Test limitations

- `contract.txt` and `contract-copy.txt` were verified byte-for-byte identical on 7 October 2026 (SHA-256:
  `6da3c4cdadc485dcb6d39b6eac3c825f2bd7edf11c2b839b1d4cca5ca4c087f5`).
  Different filenames do not imply different instructions for the selected
  candidates. Historical reports do not preserve a per-run content hash.
- Reports identify prompt filenames but do not preserve the effective prompt
  or all environment details needed for full reproduction.
- The small corpus was used while tuning prompts; it is not an independent
  generalization test.
- Audio, STT, transport and stock updates are outside the measured workflow.
- Historical experiments must not be described as having used the acceptance
  threshold established after those experiments.

## Technical conclusion

Qwen 3 4B Instruct and GPT-OSS 20B each completed a versioned precision run
with 10/10 correct cases. Gemini 3.6 Flash answered nine cases correctly with
one API error; a later run answered the remaining case using `contract.txt`
instead of `contract-copy.txt`, whose contents were verified identical on 7 October 2026. This does not establish 10/10 in one complete Gemini run.

The initial strategy is an external API, either Groq or Gemini selected through
configuration. Local Qwen through Ollama is the second option. No automatic
fallback is required by this PR.

## Operational limits agreed on 9 October 2026

| Strategy | Maximum request latency | RAM limit |
| --- | --- | --- |
| External API | 8 s | Not specified |
| Local Ollama | 40 s | 3 GB |

The reported means (0.63 s for Groq, 3.23 s and 2.08 s for Gemini,
10.22 s for local precision and 34.23 s for the original local suite) are below
the respective latency limits. Averages alone do not show that every request
meets the limit. The original local peak of approximately 3,132 MB does not
establish compliance with 3 GB; the precision suite does not record RAM.
The memory unit convention and process scope must be consistent when assessing
that limit. These thresholds were defined after the experiments.

The [ADR](../decisions/0004-use-api-provider-for-stock-interpretation.md)
records the strategy and remains Proposed pending team review. Preserve the
historical reports and effective configuration evidence for subsequent validation.
