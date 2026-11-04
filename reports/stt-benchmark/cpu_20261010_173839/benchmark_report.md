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
| kroko_es | 30/30 | 30.42 | 20.99 | 0.00 | 0.75 | 0.05 | 323.43 | 5.59 |

[Análisis por prompt](prompt_analysis.md)

[Revisión del sentido por prompt](semantic_review.md)
