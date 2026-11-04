# Groq audio pipeline comparison

Run from the PC with the active Conda or venv environment:

```bash
python scripts/benchmarks/groq_audio_pipeline_benchmark.py
```

The runner loads `config/api-keys.env` using the shared API key loader. It sends
all ten existing WAV fixtures to `whisper-large-v3` and
`whisper-large-v3-turbo`, then sends each unmodified transcription to
`openai/gpt-oss-20b` through Groq. Context and product vocabulary are shared
between STT models. Spanish, temperature zero and strict LLM JSON schema are
fixed. There is one measured pipeline per model/case, without warm-up.
Model order alternates per audio. No Raspberry or local inference is used.

HTTP 429 errors explicitly identifying tokens per minute trigger a retry after
2 seconds, repeated until success or manual interruption. Other errors are
saved without retry. Successful STT is retained when retrying the LLM.

Reports are saved after every case under
`reports/audio-stt-llm/groq_whisper_compare_TIMESTAMP_ID/`:

- `results.json`: original STT/LLM responses, effective prompts, evaluation and
  retry events.
- `environment.json`: models, settings, input hashes and retry policy.
- `benchmark_cases.csv`: per-case times, transcripts, WER/CER, JSON accuracy,
  retry counts and waiting time.
- `benchmark_summary.csv`: model comparison and aggregate times.
- `benchmark_report.md`: model/level summaries, side-by-side transcriptions,
  expected/actual JSON and retry tables.

`stt_api_s` and `llm_api_s` time the successful HTTP attempt including response
reading and JSON decoding. They include network and remote processing, not pure
inference. `pipeline_s` starts before WAV reading and ends after the LLM response
has been decoded; it includes all retries and waiting. It excludes benchmark
evaluation and report writing. Each stage additionally records its complete
elapsed time and rate-limit events. Failed-attempt timing is retained on errors.

JSON exactness compares the full operation list with the reference, including
order. WER/CER use the existing STT evaluator and retain digit/word differences.
These metrics do not replace semantic review of actions, quantities, names and
negations. The LLM never receives expected text or JSON. Audio references still
require human verification. Remote model RAM is not observable. No inventory
operation is executed. Previous benchmarks are unchanged.
