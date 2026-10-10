# ADR-0004: Use an API provider with a replaceable local alternative

## Status

Proposed

The working strategy and operational limits were defined on 9 October 2026.
The initial API/model preference was narrowed on 10 October 2026.
Team review remains pending. The benchmarks do not implement the production adapter.

## Context

VoiceStock interprets Spanish commands on the PC. The Raspberry Pi is not the
model host, and the interpreter does not modify inventory or persistence.
The evaluation is recorded in
[the strategy research](../research/stock-interpretation-strategy-and-evaluation.md).

## Decision

Use **Groq with `openai/gpt-oss-20b`** as the principal initial interpreter on
the PC. The six-case basic/habitual audio → Whisper Small Q5_1 → GPT pipeline
returned 6/6 expected experimental JSON outputs. This supports starting the
provider implementation, not declaring production integration complete.
Other API providers remain replaceable alternatives through configuration.
Keep Qwen 3 4B Instruct through Ollama on the PC as the second option.
This priority does not require automatic fallback or implementing both adapters
in the same increment.

Preserve the replaceable provider interface of InterpretationService.
The interpreter returns an InterpretationDraft; OperationContractValidation
owns mapping to the production contract and subsequent validation.
The benchmark schema is experimental, not the production interface.

### Operational limits

- Local inference: at most 40 seconds per request and 3 GB RAM.
- API inference: at most 8 seconds per request.

These limits were set after the September experiments. Historical averages
are useful evidence but do not establish that every request meets the limit.
The original local report records approximately 3,132 MB peak RAM, so compliance
with the 3 GB limit is not established. The precision suite does not measure RAM.
Memory units and the measured process scope must be consistent when checking
this limit. API cost and quotas remain deployment configuration considerations.

### Precision

Retain the proposed 100% exact-match criterion on a complete corpus run,
without repairing responses. Omitted cases or API failures prevent a complete
successful run. The current evaluator includes operation order in equality.
Qwen and GPT-OSS 20B have versioned 10/10 runs. Gemini answered all cases across
two runs, with an API error in the first; this is not a single 10/10 run.

## Alternatives considered

- Local inference first: avoids Internet and external quotas, but is retained
  as the second option under the chosen strategy.
- Gemini as the initial provider: retains successful examples but the latest
  six-case audio pipeline had two API failures. Keep as an evaluated alternative
  rather than the principal provider.
- A provider permanently coupled to the service: rejected; Groq is the initial
  selection behind the existing replaceable interface.
- Automatic fallback: not required for this PR.

## Consequences

- API operation needs Internet access and credentials on the PC.
- Provider quotas, failures and timeouts must be handled by the adapter.
- The local alternative needs verification against the agreed RAM limit.
- Historical reports lack complete per-run configuration snapshots.
- Adapter implementation and team approval remain pending; experimental results
  are not guarantees for unseen commands or the full audio workflow.

## Audio pipeline follow-up — 10 October 2026

[The STT research](../research/speech-to-text-engine-evaluation.md) records
the audio pipeline: GPT OSS 20B 6/6, local Qwen 5/6, Gemini 3.8 Flash 4/6
with two request failures. GPT interprets the STT spelling «Coca-Cola 0» as
Zero, which Qwen selected incorrectly in that run. The experiments used the
benchmark catalog/schema, not InterpretationDraft or the official contract.

[Whisper Small Q5_1 is proposed for hardware validation](0005-use-whisper-small-q5-for-offline-stt.md).
STT runs on the Pi offline; the PC needs Internet to call Groq. Credentials
remain on the PC. The local Qwen alternative does not establish compliance
with the 3-GB limit: the latest observed Ollama RSS was approximately 3158 MiB
and missed the first loading peak. Remote LLM RAM cannot be measured from the
API client. Hardware STT, production adapters, units/attributes extraction,
latency acceptance and team review remain pending.
