# ADR-0003: Use event-driven GPIO Zero and sounddevice for push-to-talk capture

## Status

Accepted

## Context

VoiceStock needs a local push-to-talk capture path on the Raspberry Pi 3.
The operator presses a button, speaks, and releases it. The Pi must detect
that gesture, record from a USB microphone, and hand one audio file to a later
stage. Capture has to work without Internet, stay separate from speech-to-text,
and keep the logic testable on a machine that has neither a GPIO pin nor a
microphone.

The button comparison and the audio comparison are in
[the push-to-talk capture research](../research/push-to-talk-capture-stack.md).
This record states the decision that the implementation follows. The executable
contract is
[the push-to-talk capture interface](../interfaces/push-to-talk-capture.md).

## Decision

Detect the button with GPIO Zero and capture audio with `python-sounddevice`
over PortAudio and ALSA.

```text
GPIO Zero
    → press / release callbacks
    → queue
    → PushToTalkController worker

python-sounddevice RawInputStream
    → PortAudio
    → ALSA
    → USB microphone
```

GPIO callbacks only enqueue a press or a release. They do not open the
microphone or write the file. One worker in `pi.push_to_talk.PushToTalkController`
runs `pi.audio.AudioCapture`. The same queue carries the maximum-duration
timeout, so one recording is finished by only one event.

The published file is uncompressed WAV: signed linear PCM, 16 kHz, mono,
16-bit. The capture path asks the selected device for that format and rejects
the device when PortAudio reports that the combination is not accepted. There
is no resampling stage.

`arecord` stays a manual ALSA check. It is not the application backend.

## Alternatives considered

### GPIO

- **GPIO Zero, event callbacks.** Chosen. `gpiozero.Button` already means
  press and release, passes debounce through, enables the internal pull-up,
  and can be exercised with mock pins. The application does not poll the pin.
- **RPi.GPIO and lower-level pin APIs.** Valid, and closer to raw electrical
  setup. They add pin handling the button contract does not need.
- **Polling.** Rejected. Press and release are edges, and a poll loop would
  keep a thread busy for a gesture that is already an event.

### Audio

- **`sounddevice.RawInputStream`.** Chosen. Start and stop are explicit, the
  buffers are raw PCM, device listing and `check_input_settings` are available,
  and the capture code does not depend on NumPy. A backend interface lets tests
  supply PCM without PortAudio.
- **`arecord`.** Appropriate for listing a card and recording a sample by hand.
  Rejected as the application engine because the process would own subprocess
  lifetime, signals, exit codes, and checking the file it wrote.
- **PyAudio.** Also a PortAudio binding and able to record. Not chosen:
  `sounddevice` matches the start/stop and device-query surface this capture
  path uses. PyAudio is not treated as incapable.

### Format

WAV signed 16-bit mono PCM at 16 kHz was chosen because it is simple to
validate, widely readable, small for a few seconds of speech, and independent
of any particular recognizer. A compressed codec would add encode and decode
cost for files that stay on the Pi only long enough for the next stage.

16 kHz mono `int16` is the format VoiceStock requires today. It is not a claim
that every USB microphone enumerates 16 kHz in hardware, and it is not a claim
that PortAudio resamples when the device rejects that rate. A successful open
can still be ALSA converting behind a plugin device such as `default`. The
research records that distinction; this implementation does not add a fallback
capture rate.

## Consequences

### Positive

- The button path and the microphone path have separate modules.
- GPIO callbacks stay short: they enqueue, and audio I/O runs on the worker.
- Tests cover the gesture, the file lifecycle, and the controller without a Pi.
- Every successful capture has the same WAV contract.
- Speech-to-text can consume `AudioCaptureResult` later without knowing GPIO
  or PortAudio.

### Negative

- Runtime capture depends on GPIO Zero and on PortAudio, ALSA, and
  `sounddevice`. `pip install sounddevice` does not bundle PortAudio.
- A microphone that cannot be opened at 16 kHz mono signed 16-bit fails with
  `AudioDeviceUnsupportedError`. Supporting it needs a later decision; this
  path will not resample.
- The input selector has to match one PortAudio device. An index is not stored,
  because indexes change between boots.
- The native PortAudio package on the project Raspberry Pi image has not been
  confirmed yet. See the
  [setup and manual test](../setup/push-to-talk.md).
