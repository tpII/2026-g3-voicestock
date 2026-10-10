# ADR-0005: Use Whisper Small Q5 as the initial offline STT candidate

## Status

Proposed — 10 October 2026. Selected for the next hardware validation; acceptance
on Raspberry Pi 3 and team review remain pending. A separate STT interface
and adapter are now implemented; the exploration scripts themselves do not
constitute hardware acceptance.

## Context

The Raspberry Pi must transcribe captured Spanish audio locally without Internet.
The caller must not depend on whisper.cpp types or model configuration. PC
experiments compared Vosk, Whisper Tiny/Base/Small Q5_1, Moonshine and Kroko.
Whisper Small preserved meaning in the two basic and four habitual corpus cases,
and its six-case pipeline with GPT OSS 20B through Groq returned the expected
experimental JSON in all cases. See
[the evaluation](../research/speech-to-text-engine-evaluation.md).

## Decision

Use **whisper.cpp and multilingual `ggml-small-q5_1.bin`** as the initial candidate
for a replaceable STT adapter under `src/pi/speech_to_text/`. Download/build during
installation; transcription must run offline. The explored CPU configuration is
Spanish, greedy decoding, temperature zero, no context between requests and no
VAD; feed the captured complete recording and return its final text.

Preserve WAV PCM16, mono, 16 kHz as the capture boundary. Internal sample conversion
belongs to the STT adapter. The module consumes audio; it does not capture audio,
access GPIO, interpret commands, send network requests or modify inventory.
The benchmark worker is exploration tooling, not the proposed public interface.

Do not declare the candidate suitable for the Pi until its actual CPU, RAM,
quality and stability are measured with the integrated module and real PTT audio.
Freeze hardware-specific acceptance thresholds before that run.

## Alternatives considered

- Whisper Base: lower PC RSS and lower CER, but less reliable meaning on habitual
  cases; retain as a smaller alternative if hardware validation rejects Small.
- Moonshine Small: strong habitual results, but ambiguous basic names and a lost
  prohibition in the integral case; keep as a comparison candidate.
- Kroko Spanish: fast PC exploration and good integral structure, but missing
  action/quantity elsewhere and ambiguous names; keep as a comparison candidate.
- Vosk and Whisper Tiny: lower resources but more critical errors in this corpus.

## Consequences

- Small Q5_1 weights occupy approximately 181 MiB; PC RSS ranged around
  349–397 MiB across the recorded suites. Neither number predicts Pi RSS.
- The engine/build and model must be reproducibly prepared for the actual Pi OS
  and architecture. The current documented build was exercised on the PC.
- Basic/habitual commands are the initial evidence scope; complex corrections
  and cancellations can still produce incorrect transcription.
- Capture/orchestration remain independent of the chosen engine.
- Revisit this ADR if hardware quality, memory, latency or offline installation
  fails. The interface and adapter now exist; their automated contract tests,
  physical validation and formal acceptance remain pending.

## Related work

- [SpeechToText-01: Evaluate engines](https://app.clickup.com/t/86e3euvxd)
- [SpeechToText-02: Document the decision](https://app.clickup.com/t/86e3eux1z)
- [SpeechToText-03: Public interface](https://app.clickup.com/t/86e3euw78)
- [SpeechToText-04: Production adapter](https://app.clickup.com/t/86e3euwhw)
- [SpeechToText-05: Operation documentation](https://app.clickup.com/t/86e3eux74)
- [SpeechToText-06: Raspberry Pi validation](https://app.clickup.com/t/86e3euxwb)

## Implementation follow-up

The next increment introduces `SpeechToText`, `TranscriptionError` and
`WhisperAdapter` in `src/pi/speech_to_text/`, plus a new SSH fixture coordinator.
The public input is a WAV path; engine configuration stays in adapter construction.
Existing benchmark tests are unchanged. The implementation has not yet run on
the Pi or been covered by new automated contract tests. This ADR remains Proposed
until the hardware and acceptance work is completed. See
[SSH fixture procedure](../testing/raspberry-stt-ssh.md).

[The public module interface](../interfaces/speech-to-text.md) records inputs,
outputs, lifecycle, errors and replaceability.
