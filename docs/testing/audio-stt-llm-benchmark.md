# Audio → STT → LLM → JSON

## Scope

Run the six basic/habitual audio cases through Whisper Small Q5_1 and the local
Ollama model `qwen3:4b-instruct`, using the precision benchmark contract, catalog
and JSON schema. Compare the generated JSON with the original prompt's expected
operations. The LLM receives only the STT transcription as user-message content;
it does not receive the reference text or expected JSON. No output is applied to
inventory.

One request per case at each stage, no warm-up or automatic retries. Models stay
loaded between cases, Whisper remains resident while Qwen runs, and the first
Qwen request includes loading if initially unloaded. The focus is the final
result and component memory, not latency.

```bash
conda activate voicestock
python scripts/benchmarks/audio_stt_llm_benchmark.py
```

Prerequisites: existing Whisper worker and Small Q5_1 weights, installed Qwen,
running local Ollama, `psutil`, and permission to read process RSS. The runner
checks that unrelated LLM models are not initially resident. Whisper uses CPU,
Spanish, four threads, greedy decoding and no context between requests. Qwen
uses the existing contract, temperature zero, `think=false`, JSON-schema output
and ten-minute keep-alive; inference placement/context remain Ollama defaults.
The selected model digest and observed resident size/VRAM are saved.

API credentials are automatically loaded from ignored `config/api-keys.env`,
with existing environment variables taking precedence. See
[API key setup and integration](../setup/api-keys.md) for future providers.
This describes credential loading; the current pipeline runs local Qwen.

## Measurements and outputs

Results live under `reports/audio-stt-llm/run_TIMESTAMP/`:

- `benchmark_report.md`: per-case expected text, STT output, actual JSON,
  expected JSON, correctness flags and RSS peaks.
- `results.json`: full prompts, raw responses, component memory measurements
  for both stages and Ollama resident metadata.
- `benchmark_cases.csv`: concise results and memory by case.
- `environment.json`: settings, hashes, model inventory and Whisper load memory.

RAM uses process RSS in MiB sampled every 10 ms. Whisper is its worker process;
Qwen memory is the sum of all processes named Ollama (server and model runners),
including server overhead. Before/after and sampled peaks are saved. Simultaneous
combined peak is measured directly rather than adding peaks from different times.
RSS may double-count shared pages and excludes dedicated GPU VRAM; observed
Ollama `size_vram` is retained separately. Memory read failures are explicit.

JSON syntax, schema, operation sequence, product sequence, quantities and exact
expected JSON are evaluated separately. Schema-constrained output alone does
not prove correct interpretation. References still require verification against
the recording. A single pass is exploratory evidence, not a stability estimate.

## Recorded first run

[Results](../../reports/audio-stt-llm/run_20261010_175923/benchmark_report.md)
contain six single-pass requests: 5/6 expected JSON matches. `restar_ambos`
selected regular Coca Cola instead of Zero from the transcription «Coca-Cola 0».
The initial sampler missed Ollama's `llama-server` process. An external trace
corrected component RSS for cases 2–6; first-case loading peak is unavailable
and explicitly marked. No inference was repeated. The runner now recognizes
`llama-server` for future full measurements.

## Gemini variant

```bash
python -m pip install -e '.[gemini,stt-benchmark]'
python scripts/benchmarks/audio_stt_gemini_benchmark.py
```

The Gemini runner loads credentials automatically from `config/api-keys.env`
and sends only Whisper's transcription to `gemini-3.8-flash` using the existing
contract/catalog and JSON schema. It selects `thinking_level=low`, temperature
zero, one request per case and SDK retries disabled. No audio is sent to Gemini.
The six basic/habitual WAVs are transcribed again, without warm-up.

Outputs are saved under `reports/audio-stt-llm/gemini_TIMESTAMP/`. Local RAM is
measured separately for the Whisper worker and the Python API client process
(including SDK and orchestration). The remote Gemini model's RAM is unavailable
and must not be reported as zero or confused with the local API client RSS.
An earlier request for `gemini-3.8-flash-lite` returned 404 for all six cases;
those saved API errors do not constitute an accuracy evaluation.

## GPT OSS 20B via Groq

```bash
python scripts/benchmarks/audio_stt_groq_benchmark.py
```

Reads `GROQ_API_KEY` automatically and calls `openai/gpt-oss-20b` using the
existing strict Groq JSON schema, temperature zero, low reasoning effort and
1000 completion tokens. One request per prompt, no warm-up or automatic retries.
The complete audio is transcribed locally by Whisper Small Q5 before sending
text to Groq. Component RAM covers the local Whisper worker and Python API
client; remote model RAM is not measurable.

Results use `reports/audio-stt-llm/groq_gpt20b_TIMESTAMP/`. Requests include the
same User-Agent as the precision benchmark. The initial run without that header
returned HTTP 403 for all cases; those failures are retained separately and do
not represent model accuracy.
