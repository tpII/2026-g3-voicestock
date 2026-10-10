# ADR-0004: Use an API provider with a replaceable local alternative

## Status

Proposed

The working strategy and operational limits were defined on 9 October 2026.
Team review remains pending. The benchmarks do not implement the production adapter.

## Context

VoiceStock interprets Spanish commands on the PC. The Raspberry Pi is not the
model host, and the interpreter does not modify inventory or persistence.
The evaluation is recorded in
[the strategy research](../research/stock-interpretation-strategy-and-evaluation.md).

## Decision

Use an external API as the initial strategy. Either evaluated API provider,
Groq or Gemini, may be selected through configuration according to availability
and credentials; this PR does not choose an exclusive API vendor.
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
- A fixed API vendor: deferred; the provider interface allows either evaluated API.
- Automatic fallback: not required for this PR.

## Consequences

- API operation needs Internet access and credentials on the PC.
- Provider quotas, failures and timeouts must be handled by the adapter.
- The local alternative needs verification against the agreed RAM limit.
- Historical reports lack complete per-run configuration snapshots.
- Adapter implementation and team approval remain pending; experimental results
  are not guarantees for unseen commands or the full audio workflow.
