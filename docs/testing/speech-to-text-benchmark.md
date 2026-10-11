# Speech-to-text CPU benchmark

## Purpose

Compare Vosk Spanish small 0.42 (complete PCM versus 250 ms input blocks),
Whisper multilingual tiny and base on the same recordings. This is preliminary
PC evidence for SpeechToText-01, not acceptance on the Raspberry Pi 3.

## Inputs

Original M4A recordings are preserved in
`tests/fixtures/speech_to_text/originals/{basico,habitual,exigente}/`. Canonical WAV copies are stored in
`tests/fixtures/speech_to_text/wav/{basico,habitual,exigente}/`: mono, 16 kHz, signed 16-bit PCM.
`manifest.json` records duration, source format, SHA-256 hashes and reference text.
References are copied from the precision prompts and need human confirmation
against the actual speech. Do not interpret transcription error rates as verified
accuracy until this confirmation is complete.

[prepare_stt_audio.py](../../scripts/benchmarks/prepare_stt_audio.py) converts
recordings with PyAV, preserving originals. Initially it relocates files from
`audio-prompts/`; later it can regenerate WAV copies from the preserved originals.
No recording, microphone access or production adapter is implemented here.

## Preparation

Install optional benchmark dependencies into the active Conda environment,
or use the project virtual environment:

```bash
conda activate voicestock
python -m pip install ".[stt-benchmark]"
python scripts/benchmarks/prepare_stt_audio.py
```

See [model and engine setup](../setup/speech-to-text-models.md) for the downloaded
weights and pinned whisper.cpp CPU build. Build the persistent Whisper worker
on Linux from the repository root:

```bash
g++ -O2 -std=c++17 scripts/benchmarks/native/whisper_worker.cpp -I .tools/stt/whisper.cpp/include -I .tools/stt/whisper.cpp/ggml/include -L .tools/stt/whisper.cpp/build/bin -Wl,-rpath,'$ORIGIN/whisper.cpp/build/bin' -lwhisper -o .tools/stt/whisper-benchmark-worker
```

Unlike launching whisper-cli once per repetition, this worker loads the model
once and reuses it for warm-up and measured requests. The worker API is internal
to this experiment. It is compiled for the local machine, not transferable to ARM.

## Execution

```bash
python scripts/benchmarks/stt_benchmark.py --runs 3 --threads 4 --timeout 600
```

One configuration runs at a time, with one unmeasured warm-up for each audio and
three measured repetitions. Models remain loaded. Vosk creates a new recognizer
per audio, preserves its state across chunks and collects segment results plus
the final remainder. Full mode passes complete PCM in one call. No waiting
simulates live recording: this measures final transcription after PTT release.

Whisper receives full float32 PCM, language `es`, CPU only, four threads,
greedy decoding (`best_of=1`), temperature zero without fallback, no context
from previous requests, and no VAD. Its native implementation handles internal
windows; no custom overlapping segmentation is added.

## Metrics and artifacts

Output goes into a new `reports/stt-benchmark/cpu_<timestamp>/` directory:

- `benchmark_runs.csv`: per-request transcriptions, status and all metrics;
- `benchmark_summary.csv`: measured configuration averages and error counts;
- `benchmark_cases.csv`: per-audio summaries;
- `prompt_analysis.md`: expected/returned text, WER matrix and worst cases;
- `prompt_errors.csv` and `prompt_errors.json`: word substitutions, omissions
  and insertions per measured repetition;
- `raw_transcriptions.json`: full reference and returned text, including warm-ups;
- `environment.json`: hardware, settings and available reproducibility metadata;
- `benchmark_report.md`: comparison and interpretation limitations;
- engine logs: diagnostics, locally retained and excluded from Git.

Metrics:

| Metric | Definition |
| --- | --- |
| WER | Word edit distance / reference word count; may exceed 100%. |
| CER | Character edit distance / reference character count, including normalized spaces. |
| Exact match | Equality after NFC, lowercase, punctuation removal and whitespace normalization. |
| Model load | Engine model initialization wall time, once per configuration. |
| Inference | Recognizer initialization and inference/finalization; excludes input file reading and conversion. |
| Request wall | Parent round trip including input I/O, IPC and inference. |
| RTF | Inference time / audio duration; below 1 means faster than the recorded audio. |
| RAM base/peak | Worker RSS in MiB, before the request and sampled maximum every 10 ms. |
| CPU | Worker user+system CPU seconds; utilization uses request wall time, 100% per fully used core. |
| Status | Successful, empty or failed request with diagnostic detail. |

Normalization preserves accents and digits. Spoken number words versus digits,
units and brand spellings can affect WER even when meaning is similar. References
are never supplied to a decoder. Accuracy summaries cover successful requests;
check failure counts and complete corpus coverage separately. Load-time RAM is
reported separately; sampling may miss brief peaks. Vosk thread settings remain
engine defaults (the OpenMP environment is recorded); Whisper uses explicit threads.

The thresholds previously agreed for LLM inference do not define STT acceptance.
Final selection requires quality/resource thresholds and measurement on Pi 3,
including real PTT audio, silence/non-speech and separate cold load versus inference.


## First recorded PC experiment

[CPU experiment, 10 October 2026](../../reports/stt-benchmark/cpu_20261010_170025/benchmark_report.md)
completed 120 measured requests (30 per configuration) and 40 warm-ups, with
no request failures. This describes execution success, not exact transcription.
Whisper tiny had the lowest mean inference time; Whisper base had the lowest
strict WER. Vosk complete PCM and 250 ms blocks differed by less than 0.01 s
in mean inference. The experiment does not establish a meaningful speed advantage
for complete PCM. Whisper used approximately four cores versus approximately
one for Vosk, so timings do not imply the same ranking on Raspberry Pi.
Human verification of reference texts and real Pi measurements remain pending.


## Analyze existing transcriptions

The benchmark generates prompt-level analysis automatically. To regenerate it
without loading models or running inference again:

```bash
python scripts/benchmarks/analyze_stt_benchmark.py --results-directory reports/stt-benchmark/cpu_20261010_170025
```

The report displays every distinct raw transcript with its repetition numbers,
per-prompt WER/CER means and WER range, and word edit alignments. Identical
transcripts are grouped for readability; no measured repetition is discarded.
Minimum edit alignments may have equivalent alternatives; they identify lexical
differences, not the semantic correctness of an inventory command.


## Additional small Q5_1 candidate

Whisper multilingual small Q5_1 uses the same CPU worker and greedy settings.
To evaluate only this model with the same corpus, warm-ups and repetitions:

```bash
python scripts/benchmarks/stt_benchmark.py --configurations whisper_small_q5_1 --runs 3 --threads 4 --timeout 600
```

`--configurations` also accepts `vosk_full`, `vosk_chunks`, `whisper_tiny`
and `whisper_base`; the original four configurations remain the default.
Model quantization changes the weights representation, not the audio format.
Compare accuracy and resources from this run against the saved baseline,
checking audio hashes and decoding settings. Runs performed at different times
are exploratory comparisons and may reflect different machine load.


## Combine saved runs

Use `compare_stt_runs.py` with two or more result directories to build a
comparison and per-prompt error analysis without repeating inference:

```bash
python scripts/benchmarks/compare_stt_runs.py --results-directories reports/stt-benchmark/cpu_20261010_170025 reports/stt-benchmark/NEW_RUN
```

The tool checks corpus hash, platform, Python, repetition count, warm-ups,
Whisper revision and decoding settings. Duplicate configurations are rejected.
Each request retains its source run and the comparison records source environments.
Experiments at different times may have different machine load, even when their
settings match; this limitation is explicitly retained in the comparison.


## Small Q5_1 comparison results

[Combined comparison](../../reports/stt-benchmark/comparison_20261010_171706/benchmark_report.md)
retains the initial baseline and
[small Q5_1 run](../../reports/stt-benchmark/cpu_20261010_171302/benchmark_report.md).
Small completed 30 measured requests and 10 warm-ups without execution failures.
Its strict WER was 26.81% versus 31.33% for base, while CER was 16.75% versus
15.93%. Mean inference increased from 1.53 s to 5.87 s and worker RSS peak
from 299 MiB to 397 MiB on this PC.

Despite lower WER, small omitted the initial quantity correction in
`caso_integral` (three corrected to two), which base preserved. It also omitted
the initial add verb in `negar_varias_agregaciones`. A lower edit rate does not
establish better preservation of command meaning. Reference audio verification
and real Raspberry Pi timing/resources remain necessary before engine selection.

## Moonshine Spanish comparison

The optional `stt-moonshine` extra installs `moonshine-voice==0.1.5`.
Activate the intended Conda environment, or the existing venv, then run:

```bash
python -m pip install -e '.[stt-benchmark,stt-moonshine]'
python scripts/benchmarks/download_moonshine_models.py
python scripts/benchmarks/stt_benchmark.py --configurations moonshine_tiny_es moonshine_small_es --runs 3 --threads 4
```

Downloads use the engine catalog for Spanish Tiny Streaming and Small Streaming
and remain under ignored `models/stt/moonshine/`. Each run records catalog URLs,
architecture, file sizes and SHA-256 hashes. No model or audio is committed by
these commands.

The worker uses CPUExecutionProvider and `transcribe_without_streaming` with a
complete float32 recording, no vocabulary hints and default flags. Models remain
loaded between requests. Inference includes the binding's Python-to-ctypes copy
and engine processing, but excludes file loading and float preparation. Internal
segmentation and decoding remain engine defaults. Moonshine uses its default
thread policy; `--threads` sets OMP_NUM_THREADS but does not guarantee four ONNX
threads. CPU utilization is measured rather than assumed. These differences must
be considered when comparing timings with the four-thread Whisper worker.

[Moonshine results](../../reports/stt-benchmark/cpu_20261010_172652/benchmark_report.md)
and [semantic review](../../reports/stt-benchmark/cpu_20261010_172652/semantic_review.md)
record 60 successful measured requests and 20 warm-ups.
[Seven-configuration comparison](../../reports/stt-benchmark/comparison_20261010_172919/benchmark_report.md)
retains the saved earlier runs. Moonshine used approximately 12–13 CPU cores with
engine defaults, versus four Whisper threads; timing rankings do not establish
superiority with equal parallelism or Raspberry Pi 3 feasibility.

## Ready-to-run Spanish Kroko

The `stt-sherpa` extra installs `sherpa-onnx==1.13.8`. With the intended Conda
or venv activated:

```bash
python -m pip install -e '.[stt-benchmark,stt-sherpa]'
python scripts/benchmarks/download_kroko_model.py
python scripts/benchmarks/stt_benchmark.py --configurations kroko_es --runs 3 --threads 4
```

The downloader pins revision `20cf7a4` of
[Spanish Kroko](https://huggingface.co/csukuangfj/sherpa-onnx-streaming-zipformer-es-kroko-2025-08-06).
No weight conversion, retraining or phoneme-to-text stage is required.
The worker uses CPU, four inference threads, greedy decoding, no hints and
endpoint detection disabled. Each request creates a fresh stream, feeds the
complete recording, adds 300 ms of zero padding to flush model right context,
marks input finished, and decodes until no frames remain ready. Padding is
included in measured inference, but excluded from the original audio duration
used for RTF. Model load is measured separately. All model files are hashed.

Canary is excluded from this simple full-file exploration because its documented
long-audio protocol requires segmenting the 51-second integral case. Parakeet and
Wav2Vec2 are excluded from this round to avoid introducing heavier runtimes.

[Kroko results](../../reports/stt-benchmark/cpu_20261010_173839/benchmark_report.md)
and [semantic review](../../reports/stt-benchmark/cpu_20261010_173839/semantic_review.md)
record 30 successful measured requests. Four threads were configured, but combined
internal sessions used approximately seven cores: this is not a global four-core
limit. [Combined comparison](../../reports/stt-benchmark/comparison_20261010_173923/benchmark_report.md)
retains all source runs. No runtime feasibility on Raspberry Pi 3 is established.

## Difficulty levels and meaning review

Text prompts live in `scripts/benchmarks/prompts/precision/{basico,habitual,exigente}/`;
`contract.txt` stays at the root as the common LLM contract. Original recordings
and canonical WAVs use the same three level subdirectories. `prompt_levels.py`
is the shared mapping; the fixture manifest records each level and text path.

| Level | Cases |
| --- | --- |
| basico | solo_agregar, solo_restar |
| habitual | restar_ambos, corregir_cantidad, negar_agregacion, negar_restacion |
| exigente | negar_varias_agregaciones, negar_varias_restaciones, negar_agregacion_y_restacion, caso_integral |

The meaning review evaluates final operations, quantities, corrections, explicit
prohibitions and identity of active items. Clear cancellation of all operations
can remain coherent despite a cancelled item name error. Ambiguous active names
are not counted as unequivocal success. Statuses are `coherente`, `ambigua` and
`sentido_comprometido`. Each case counts once per model, reviewing every measured
repetition and conservatively retaining the problematic variant. This manual
review is not a validated parser metric and references still need audio checking.

```bash
python scripts/benchmarks/analyze_stt_levels.py
```

The script aggregates explicit decisions from
`scripts/benchmarks/reviews/stt_semantic_levels.json` and checks the saved
transcription file hash before generating the level report, CSV and JSON. It
does not infer semantic judgments automatically or perform inference. The
original report metadata retains historical input paths/hashes; moved audio and
text contents are unchanged. New runs use the organized manifest and its new hash.

[Results by difficulty](../../reports/stt-benchmark/comparison_20261010_173923/level_analysis.md)
include all model outputs and the reason behind each classification.
