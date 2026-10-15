# Speech-to-text engine evaluation

## Scope and recommendation

On 10 October 2026, the team selected **whisper.cpp with multilingual Whisper
Small Q5_1** as the primary STT candidate to validate on Raspberry Pi 3.
The planned initial interpreter is **GPT OSS 20B through Groq on the PC**.
[ADR-0005](../decisions/0005-use-whisper-small-q5-for-offline-stt.md) records the
STT proposal; [ADR-0004](../decisions/0004-use-api-provider-for-stock-interpretation.md)
records the LLM priority. Hardware viability remains unverified.

This work supports
[SpeechToText-01: Evaluate engines](https://app.clickup.com/t/86e3euvxd) and
[SpeechToText-02: Document the decision](https://app.clickup.com/t/86e3eux1z).
It does not complete the interface, production adapter or physical acceptance.

## Corpus and protocol

Ten recorded audios are preserved as M4A originals and canonical WAV PCM16,
mono, 16 kHz. The fixture manifest records hashes, duration, reference text and
level: two basic, four habitual and four demanding cases. The written reference
still needs confirmation by listening to the audio.

The STT comparison uses one warm-up per audio and three measured repetitions,
retaining models between requests. Runs are sequential experiments on the PC,
not Raspberry Pi acceptance. WER/CER preserve accents and numerical spelling:
«two» versus «2» in equivalent Spanish expressions still counts as an edit.
The qualitative review separately considers final action, quantity, correction,
negation and identity of active items; each prompt counts once per model.

[Full comparison and provenance](../../reports/stt-benchmark/comparison_20261010_173923/benchmark_report.md)
and [meaning by difficulty](../../reports/stt-benchmark/comparison_20261010_173923/level_analysis.md)
are the recorded evidence. Protocol details remain in
[the STT benchmark guide](../testing/speech-to-text-benchmark.md).

## Compared alternatives on PC

| Configuration | WER % | CER % | Mean inference s | Peak RSS MiB |
| --- | --- | --- | --- | --- |
| Vosk Spanish small, full input | 37.85 | 24.55 | 1.12 | 233 |
| Vosk Spanish small, 250 ms blocks | 38.15 | 24.85 | 1.13 | 229 |
| Whisper Tiny | 42.47 | 21.69 | 0.72 | 214 |
| Whisper Base | 31.33 | 15.93 | 1.53 | 299 |
| Whisper Small Q5_1 | 26.81 | 16.75 | 5.87 | 397 |
| Moonshine Tiny Spanish | 32.23 | 21.58 | 1.08 | 288 |
| Moonshine Small Spanish | 27.71 | 18.87 | 2.33 | 502 |
| Kroko Spanish | 30.42 | 20.99 | 0.75 | 323 |

Whisper used four threads. Moonshine used its internal defaults (approximately
12–13 cores); Kroko configured four threads but its internal sessions together
used approximately seven cores. Timing ranks do not use equal total parallelism.
RAM is sampled process RSS, not exclusive physical memory or model file size.

Whisper Small preserved unequivocal meaning for both basic and all four habitual
cases. The three leading candidates remain Whisper Small, Moonshine Small and
Kroko. Demanding cases expose critical errors: Whisper Small omitted the quantity
correction in the integral case; Moonshine Small lost a prohibition there; Kroko
preserved its instruction structure but left a name ambiguous and omitted an
action/quantity in another case. The choice prioritizes the basic/habitual scope,
not a claim of complete speech accuracy. Base remains a smaller alternative if
Small is unsuitable on the Pi; this requires another documented decision.

## Audio → STT → LLM evidence

Six basic/habitual WAVs were transcribed once per pipeline run, without warm-up,
then the transcription was sent through the existing experimental contract and
schema. No expected JSON was sent to the LLM and no inventory was modified.

| Interpreter after Whisper Small | Exact JSON | Request failures | Evidence |
| --- | --- | --- | --- |
| Local Qwen3 4B Instruct | 5/6 | 0 | [Run](../../reports/audio-stt-llm/run_20261010_175923/benchmark_report.md) |
| Gemini 3.8 Flash | 4/6 | 2 | [Run](../../reports/audio-stt-llm/gemini_20261010_182156/benchmark_report.md) |
| GPT OSS 20B via Groq | 6/6 | 0 | [Run](../../reports/audio-stt-llm/groq_gpt20b_20261010_182936/benchmark_report.md) |

Qwen selected regular Coca Cola from «Coca-Cola 0» instead of Zero. GPT OSS 20B
preserved the intended variant, correction and simple cancellations. Gemini's
four successful responses were exact; API failures are availability failures,
not observed interpretation errors. The initial GPT run returned six HTTP 403
errors before matching the existing benchmark's User-Agent; that failed run
remains separate. The unavailable Gemini 3.8 Flash Lite run also remains as
API-error evidence, not an accuracy result.

The GPT pipeline measured approximately 349 MiB Whisper RSS and 43 MiB local
Python API client RSS. Remote model RAM is not measurable from the PC. The Qwen
run observed approximately 3158 MiB for Ollama server plus runner, but missed the
first loading peak; its memory gap is retained in the report. None of these runs
establishes Raspberry Pi resources or the existing LLM latency limits.

## Validation still required

Before closing
[SpeechToText-06: Hardware evaluation](https://app.clickup.com/t/86e3euxwb):

1. Record actual Pi model, usable RAM, OS, architecture and microphone setup.
2. Freeze reference transcripts and thresholds for quality, load, inference,
   RSS and stability before measuring. The 40-second/3-GB limits of ADR-0004
   concern the local LLM on PC; they are not STT thresholds for the Pi.
3. Validate the newly implemented public STT interface and replaceable adapter
   on the Pi; automated contract tests also remain pending.
4. Measure model loading separately from transcription, with CPU and RAM,
   including at least one real PushToTalk recording and silent/non-speech audio.
5. Verify offline runtime and write a usable/not-usable verdict. Reopen the
   model choice if Small cannot meet the frozen criteria.

The small corpus was used to compare candidates and is not an independent
holdout. One pipeline pass per prompt does not establish repeatability. Units,
attributes and the official production operation contract remain outside this
experimental JSON result's validation scope.

## SSH integration follow-up

The next increment introduces a separate public STT port and Whisper adapter
under `src/pi/speech_to_text/`, with a new coordinator in `scripts/integration/`.
Existing benchmark tests remain unchanged. The SSH experiment transfers the
recorded prompts and invokes Groq from the PC; no actual Raspberry measurements
have been recorded yet. See [the execution guide](../testing/raspberry-stt-ssh.md).
