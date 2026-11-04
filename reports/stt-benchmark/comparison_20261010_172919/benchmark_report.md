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
| moonshine_tiny_es | 30/30 | 32.23 | 21.58 | 0.00 | 1.08 | 0.07 | 288.47 | 0.20 |
| moonshine_small_es | 30/30 | 27.71 | 18.87 | 0.00 | 2.33 | 0.15 | 501.81 | 0.38 |

[Análisis por prompt](prompt_analysis.md)

## Source runs

- `reports/stt-benchmark/cpu_20261010_170025`
- `reports/stt-benchmark/cpu_20261010_171302`
- `reports/stt-benchmark/cpu_20261010_172652`

Executed at different times; timings may reflect machine load.

[Revisión del sentido de Moonshine por prompt](semantic_review.md)

Moonshine uses default internal ONNX threading (approximately 12–13 CPU cores used), while Whisper used four threads. Timings do not use equal parallelism.
