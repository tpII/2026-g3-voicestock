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
| moonshine_tiny_es | 30/30 | 32.23 | 21.58 | 0.00 | 1.08 | 0.07 | 288.47 | 0.20 |
| moonshine_small_es | 30/30 | 27.71 | 18.87 | 0.00 | 2.33 | 0.15 | 501.81 | 0.38 |

[Análisis por prompt](prompt_analysis.md)

[Revisión del sentido por prompt](semantic_review.md)
