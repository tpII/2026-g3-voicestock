# Speech-to-text module interface

## Purpose and state

`src/pi/speech_to_text/` transcribes already captured audio offline. It contains
an engine-independent `SpeechToText` protocol, `TranscriptionError`, and a
sequential `WhisperAdapter`. Capture, GPIO, transport, LLM interpretation and
inventory updates remain outside this module.

The interface and adapter are implemented; hardware execution and automated
contract tests are still pending. This does not close
[SpeechToText-03: Public interface](https://app.clickup.com/t/86e3euw78) or
[SpeechToText-04: Real adapter](https://app.clickup.com/t/86e3euwhw).

## Input and output

```python
class SpeechToText(Protocol):
    def transcribe(self, audio_path: Path) -> str:
        ...
```

The path must identify a nonempty WAV containing uncompressed signed PCM16,
mono, at 16000 Hz, consistent with the PushToTalk capture boundary. The caller
owns the audio file; the adapter does not delete it. It converts samples to
float32 internally and removes its own temporary input when closed.

The result is a nonblank Spanish transcription. The adapter does not normalize
names, repair quantities or resolve corrections; these remain text for the
interpreter. Its success does not assert transcription accuracy.

## Concrete adapter and lifecycle

```python
from pathlib import Path

from pi.speech_to_text import SpeechToText, WhisperAdapter

with WhisperAdapter(
    worker_path=Path(".tools/stt/whisper-benchmark-worker"),
    model_path=Path("models/stt/whisper/ggml-small-q5_1.bin"),
    threads=4,
    timeout=600,
) as engine:
    stt: SpeechToText = engine
    text = stt.transcribe(Path("captured.wav"))
```

Construction starts a persistent native worker. `wait_until_loaded()` optionally
reads its startup event for instrumentation; `transcribe()` does this itself
before the first request. No context from previous recordings is retained.
An optional `prompt_path=Path(...)` constructor argument supplies a nonempty
UTF-8 vocabulary file to the integration worker. It uses Whisper initial
prompt conditioning for every request and window, independently of previous
recordings. Rebuild the integration worker before enabling this option.
The model remains loaded for sequential requests. Context exit or `close()`
terminates the worker and releases temporary files and logs.

Do not share an instance across concurrent requests. An application should use
one queue and one worker, and keep inference out of GPIO callbacks. To replace
the engine, inject another implementation of `SpeechToText`; engine paths and
parameters belong to composition, not the public `transcribe` signature.

## Errors and instrumentation

`TranscriptionError` reports invalid/empty audio, missing worker/model, worker
failure, timeout, invalid protocol response or empty transcription. Invalid
construction parameters (`threads < 1`, `timeout <= 0`) raise `ValueError`.
OS failures during worker startup can propagate; the composition layer must
handle installation/startup failures. No automatic retry or recording occurs.
A timeout closes the worker; construct a new adapter before retrying later.

`worker_pid` and the optional startup event support external measurement; they
are concrete adapter instrumentation, not members of the `SpeechToText` port.
The SSH fixture worker samples RSS/CPU externally. The subprocess's JSON-lines
format and float32 file paths are implementation details, not the module API.

## Integration experiment

[The SSH fixture guide](../testing/raspberry-stt-ssh.md) describes how the PC sends
six recorded WAVs, invokes this adapter on the Pi, receives text/resources and
calls Groq from the PC. This experiment does not exercise physical capture or
the HTTP application path. The official operation contract remains separate from
the benchmark JSON schema.
