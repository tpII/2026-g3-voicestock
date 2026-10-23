# TC-AUD-002 — VoiceStock audio capture and WAV integrity

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that `AudioCapture` and `SoundDeviceBackend` on the Pi publish a WAV
at 16 kHz, mono, signed 16-bit, and record how the header duration compares
with the hold.

## Test level and type

Level: software component on the Raspberry Pi, using the real microphone.

Type: functional and measurement. The button is intentionally not used, so
a GPIO fault cannot hide an audio fault.

## Requirements and ClickUp traceability

- ClickUp: [PushToTalk-06](https://app.clickup.com/t/86e3euv9u).
- Requirement: the capture contract in `pi.audio.config` (16000 Hz, 1
  channel, 2 bytes, `int16`).

## Source modules and documentation

- `pi.audio.capture.AudioCapture`.
- `pi.audio.sounddevice_backend.SoundDeviceBackend`.
- `pi.audio.config`.
- [Push-to-talk capture](../../../interfaces/push-to-talk-capture.md).

## Preconditions and dependencies

- [TC-AUD-001](TC-AUD-001.md) selected a unique device query.
- The output directory is writable.
- No other process holds the microphone.

## Required hardware and software

- Raspberry Pi 3 and the USB microphone on the port recorded in TC-AUD-001.
- Project environment.
- `sha256sum` and Python's `wave` module (standard library).

## Preparation

```bash
mkdir -p recordings/tc-aud-002
```

Keep this directory out of git. The WAV files are external evidence.

The scratch script below is not a product command. `voicestock-pi-ptt`
needs a GPIO pin, and this case must run without one.

## Execution

Set `QUERY` to the string from TC-AUD-001.

```bash
python - <<'PY'
import time
import wave
from pathlib import Path
from pi.audio.capture import AudioCapture
from pi.audio.config import AudioCaptureConfig
from pi.audio.sounddevice_backend import SoundDeviceBackend

query = "<QUERY>"
directory = Path("recordings/tc-aud-002")
hold_s = 3.0
config = AudioCaptureConfig(input_device=query, output_directory=directory)
backend = SoundDeviceBackend(config.input_device)
capture = AudioCapture(config, backend)
t0 = time.monotonic()
capture.start()
t1 = time.monotonic()
print(f"start_returned {t1 - t0:.6f}", flush=True)
time.sleep(hold_s)
t2 = time.monotonic()
artifact = capture.stop()
t3 = time.monotonic()
print(f"hold {t3 - t1:.6f}", flush=True)
print(f"stop {t3 - t2:.6f}", flush=True)
print(f"path {artifact.path}", flush=True)
with wave.open(str(artifact.path), "rb") as wav:
    print(f"channels {wav.getnchannels()}")
    print(f"sample_width {wav.getsampwidth()}")
    print(f"rate {wav.getframerate()}")
    frames = wav.getnframes()
    print(f"frames {frames}")
    print(f"header_duration {frames / wav.getframerate():.6f}")
PY
sha256sum recordings/tc-aud-002/*.wav
```

The sleep is inside the measured hold. Speak or tap the microphone so the
file is not an unexamined silence; silence does not fail the format
criteria. Note whether any sound was present.

Run one labeled warm-up, then five measured holds. Delete nothing until the
checksums are in the execution record.

Negative probe, once, with an output directory that cannot be created
because its parent is a file, or skip it if preparing that safely is
unclear and record **NOT MEASURED** for the negative probe only. Do not
point the probe at `/` or at the repository.

A second negative probe uses a query that TC-AUD-001 showed is ambiguous,
if one exists. Expect `AudioDeviceAmbiguousError` from `start`. If no
ambiguous query exists, record "not applicable".

## Observations and evidence

- For each run: `start_returned`, `hold`, `stop`, header fields, path,
  SHA-256.
- Exceptions, including `AudioDeviceUnsupportedError` if the device cannot
  open 16 kHz mono `int16`.
- The implementation waits up to 5 seconds for the capture worker
  (`_WORKER_JOIN_TIMEOUT_SECONDS`). A hang past that, surfaced as
  `AudioStreamError`, is a failure observation. Do not raise the constant
  in the product during the test.

## Metrics

| Metric | Unit | Limit |
| --- | --- | --- |
| Stream initialization (`start_returned`) | seconds | Recorded. A pass limit is **TO BE DEFINED**. Raising is a functional fail. |
| Header duration minus monotonic hold | seconds | Recorded. A numeric tolerance is **TO BE DEFINED** from the first valid baseline. |
| Format | channels, bytes, Hz | Must be 1, 2, 16000 |
| File size | bytes | Recorded. Expected shape is header plus `frames * 2`. A mismatch fails. |
| Discontinuities | none | Observation only. **NOT** a numeric gate. The backend discards PortAudio overflow. |

`time.sleep(3.0)` is the operator's requested hold for this procedure. It
is not a product requirement that recordings last 3 seconds.

## Acceptance criteria

1. All five measured runs publish a readable WAV.
2. Each file reports 1 channel, sample width 2, and rate 16000.
3. `frames` is greater than 0 in each measured run.
4. File size equals the size reported by the filesystem and matches
   `44 + frames * 2` when the Python `wave` header is 44 bytes. If a run
   produces a different header length, record the actual header length and
   fail this criterion only when `size != header_length + frames * channels * sample_width`.
5. SHA-256 is stored for each file. The file stays out of git.
6. Duration error is in the raw table and is not compared with an invented
   limit. The criterion is "recorded", not "below X".
7. An unsupported device fails the case with the VoiceStock exception, not
   with a substituted recorder such as `arecord`.

## Failure conditions

- Any measured run raises or writes a non-contract WAV: **FAILED**.
- The device cannot be opened at the contract: **FAILED** for this
  microphone. Do not enable resampling; the backend does not resample.
- Checksums missing: **PASSED_PENDING_DOCUMENTATION** at best.

## Recovery and cleanup

Leave the WAV files in the external archive location named by the execution
record, then remove the local copies from the Pi working tree if they would
otherwise be committed. Do not add `recordings/` to the commit.

## Limitations and exclusions

This case does not use the button, does not send the file, and does not
judge speech intelligibility. A later push-to-talk case must still be run.
Overflow ticks are invisible to this procedure.
