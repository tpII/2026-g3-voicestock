# STT CPU benchmark

PC exploration; not Raspberry Pi acceptance.
Reference texts are copied from the prompts and require human audio verification.
WER/CER ignore case, punctuation and whitespace, but preserve accents and digits.
Numeric words versus digits count as errors under this normalization.
Models remain loaded; one warm-up per audio is excluded from summaries.
RAM is sampled worker RSS (MiB, 10 ms); short peaks may be missed.
CPU uses process user+system time; 100% equals one fully used core.
WAV reading/conversion is excluded from inference_s; request_wall_s includes I/O.
Errors are reported separately; accuracy summaries cover successful requests only.

| Configuration | OK/total | WER % | CER % | Exact % | Mean s | RTF | RAM MiB | Load s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 30/30 | 37.85 | 24.55 | 0.00 | 1.12 | 0.08 | 233.33 | 0.29 |
| vosk_250ms | 30/30 | 38.15 | 24.85 | 0.00 | 1.13 | 0.08 | 228.73 | 0.28 |
| whisper_tiny | 30/30 | 42.47 | 21.69 | 0.00 | 0.72 | 0.06 | 213.92 | 0.10 |
| whisper_base | 30/30 | 31.33 | 15.93 | 0.00 | 1.53 | 0.12 | 298.98 | 0.14 |
| whisper_small_q5_1 | 30/30 | 26.81 | 16.75 | 0.00 | 5.87 | 0.49 | 397.23 | 0.19 |

[Análisis por prompt](prompt_analysis.md)

## Source runs

- `reports/stt-benchmark/cpu_20261010_170025`
- `reports/stt-benchmark/cpu_20261010_171302`

Executed at different times; timings may reflect machine load.

## Important qualitative finding

Small Q5_1 lowers aggregate strict WER, but in `caso_integral` it omits the
initial correction from three to two, which base preserved. It also omits the
initial add verb in `negar_varias_agregaciones`. Aggregate edit rates do not
establish semantic safety. See the full per-prompt transcriptions and confirm
reference texts against the recordings before selecting an engine.
