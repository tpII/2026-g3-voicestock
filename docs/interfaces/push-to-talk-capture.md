# Push-to-talk capture interface

## Purpose

This interface turns one button gesture on the Raspberry Pi into one WAV file
for a later consumer. It does not transcribe speech, interpret a command,
update inventory, or play a sound.

The stack decision is
[ADR-0003](../decisions/0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md).
How to wire the button and run a capture on the Pi is the
[setup and manual test](../setup/push-to-talk.md).

```text
physical button
      ↓
pi.input.PushToTalkButton
      ↓
PRESSED / RELEASED
      ↓
pi.push_to_talk.PushToTalkController
      ↓
pi.audio.AudioCapture
      ↓
AudioArtifact
      ↓
AudioCaptureResult
      ↓
on_capture_completed / future orchestrator
```

Code lives under `src/pi/input/`, `src/pi/audio/`, and `src/pi/push_to_talk/`.

## Responsibilities

| Module | Owns | Does not own |
|---|---|---|
| `PushToTalkButton` | The GPIO pin, press, release, and debounce. | Audio, files, speech-to-text. |
| `AudioCapture` | Opening the configured input, writing PCM, and publishing one WAV. | The button, the gesture, speech-to-text. |
| `PushToTalkController` | Turning press and release into one cycle, the maximum duration, and delivery of the result or the error. | Speech-to-text, retries, LEDs, what to do with the file afterwards. |

`PushToTalkButton` is constructed with a BCM pin, a debounce time in seconds,
and two callbacks. Wiring is fixed in code: `gpiozero.Button(..., pull_up=True)`.
The button connects the pin to ground. Released reads high; pressed reads low.
GPIO Zero then reports those edges as `when_pressed` and `when_released`.
There is no polarity setting. `close()` releases the pin.

Those callbacks must only call `PushToTalkController.notify_pressed` and
`notify_released`. Both methods enqueue an event. They do not call
`AudioCapture.start` or `stop`.

`AudioCapture` is constructed with an `AudioCaptureConfig` and an
`AudioInputBackend`. Construction does not open hardware.
`AudioCaptureConfig.input_device` is a descriptive query, not a PortAudio
index. `output_directory` is where the temporary file and the WAV are written.
`SoundDeviceBackend` is the backend that opens `sounddevice.RawInputStream`.
Importing `pi.audio` does not import `sounddevice`; that import happens when a
device is listed or a stream is opened.

The controller is constructed with the capture object, `on_capture_completed`,
`on_capture_error`, and `max_duration` (default `60.0` seconds). `start()`
starts its worker. `close()` stops the worker and cancels the timer. Closing
does not delete a file already handed to the consumer. If a recording is still
active, `close()` finishes it and delivers that result with
`TerminationReason.RELEASED`.

## Button

```text
Raspberry Pi GPIO (BCM pin, chosen at startup)
      │
      ├── internal pull-up, always on
      │
      ▼
    button
      │
      ▼
     GND
```

| Electrical level | GPIO Zero callback |
|---|---|
| High, button released | `on_released` |
| Low, button pressed | `on_pressed` |

`bounce_time` is passed through to GPIO Zero. The diagnostic command requires
it; `0.05` in examples is only an example. The product pin is not fixed.
GPIO 17 in examples is a BCM pin the operator chooses.

## Microphone selection

`SoundDeviceBackend` resolves `input_device` against input devices PortAudio
can see. The query is matched, case-insensitively, as ordered substrings of
`"<device name>, <host API name>"`.

| Situation | Error |
|---|---|
| Empty selector, or no device matches | `AudioDeviceNotFoundError` |
| Several devices match, and the query is not the exact name of exactly one of them | `AudioDeviceAmbiguousError` (`query`, `matches`) |
| The chosen device rejects 16 kHz, mono, `int16` | `AudioDeviceUnsupportedError` |

An exact match is the device name alone, or `name, host API`, ignoring case.
That is how one device is selected when a shorter query hits several names.
`list_input_devices()` returns `InputDeviceInfo` (`name`, `host_api`,
`max_input_channels`, `default_samplerate`) and omits the PortAudio index.

`check_input_settings` is the acceptance test. A device that fails it is not
opened, and nothing in this interface resamples or downmixes.

## Audio contract

`pi.audio.config` fixes the capture format. `AudioFormat` on the result
repeats it for the consumer. These are not runtime options.

| Field | Value |
|---|---|
| `container` | `WAV` |
| Encoding | signed linear PCM, no compression |
| `sample_rate_hz` | `16000` |
| `channels` | `1` |
| `sample_width_bytes` | `2` (16-bit) |

`AudioFormat` has only those four fields. The constant is
`CAPTURED_AUDIO_FORMAT`.

## AudioArtifact

```text
AudioArtifact
├── id      UUID string, chosen when the recording starts
├── path    published <id>.wav
└── cleanup()
```

`id` does not get recomputed from `path`. `cleanup()` deletes that WAV if it
is still there (`unlink(missing_ok=True)`). The artifact has no gesture, no
duration, and no format fields.

## File lifecycle

```text
AudioCapture.start()
      ↓
<uuid>.recording          AudioCapture owns this file
      ↓
PCM appended as it arrives
      ↓
AudioCapture.stop()
      ↓
WAV header closed
      ↓
channels, sample width, and rate checked
      ↓
os.replace → <uuid>.wav
      ↓
the published file is checked again
      ↓
AudioArtifact
```

A path ending in `.wav` is a file that passed that check. If start or stop
fails before that, `AudioCapture` deletes the temporary file and any partial
publish, raises `AudioCaptureError`, and does not return an artifact.

## Ownership

While `start()` has succeeded and `stop()` has not returned, `AudioCapture`
owns the `.recording` file.

`stop()` transfers the published WAV to the caller inside `AudioArtifact`.
The controller wraps that artifact in `AudioCaptureResult` and calls
`on_capture_completed(result)`. After that call, the controller does not call
`cleanup()`.

The consumer decides whether to keep the file, pass it on, or delete it.
Speech-to-text is not that owner until a later feature says so.

If `on_capture_completed` raises, the worker logs the exception and keeps
running. The artifact is not deleted. The controller state has already moved
on, as in the table below.

## AudioCaptureResult

```text
AudioCaptureResult
├── artifact             AudioArtifact
├── duration             seconds, frames / sample rate of the published WAV
├── format               AudioFormat
└── termination_reason   TerminationReason
```

`duration` is the length of the WAV, not the wall-clock time between press and
release. `duration_of()` reads `wave.getnframes()` and `wave.getframerate()`.
A file that is not a valid WAV, or that reports a sample rate of zero, raises
`AudioStreamError` instead of producing a result.

### TerminationReason

| Member | Meaning |
|---|---|
| `RELEASED` | The button was released and `stop()` published a WAV. |
| `MAX_DURATION` | The configured limit was reached and `stop()` published a WAV. |

`MAX_DURATION` is still a successful result. The partial file is a normal WAV.
A capture error is not a termination reason: there is no `AudioCaptureResult`.

## States

`PushToTalkState` is the controller, not the private state inside
`AudioCapture`.

```text
IDLE
 │ PRESSED
 ▼
RECORDING
 │
 ├── RELEASED ──────────────→ IDLE
 │
 └── MAX_DURATION
          ↓
 WAITING_FOR_RELEASE
          │
          RELEASED
          ↓
         IDLE
```

`WAITING_FOR_RELEASE` means the file already exists and the button is still
down. Another `PRESSED` in that state is ignored. The next cycle starts only
after `RELEASED` returns the controller to `IDLE`.

Also ignored, with no extra file and no extra result:

| State | Event |
|---|---|
| `IDLE` | `RELEASED` |
| `RECORDING` | `PRESSED` |
| `WAITING_FOR_RELEASE` | `PRESSED` |

`max_duration` is a controller argument, default 60 seconds, and must be
greater than zero. It limits a hold that never releases. It is not a product
decision about how long a person may speak. The diagnostic command exposes it
as `--max-duration`.

When recording starts, the controller arms a timer for that generation. The
timer enqueues `MAX_DURATION`; it does not call `stop()` itself. A release
cancels the timer and then stops the capture. A timeout whose generation is
not the recording in progress is ignored, so a late timer cannot stop the next
take. One press produces at most one `stop()` and at most one result.

## Errors

Success calls `on_capture_completed(result)`. Failure calls
`on_capture_error(error)` and does not call the success callback.

| Error | When |
|---|---|
| `AudioDeviceNotFoundError` | The selector is empty or matches nothing. |
| `AudioDeviceAmbiguousError` | More than one device matches and none is the single exact name. |
| `AudioDeviceUnsupportedError` | The device cannot be opened at 16 kHz, mono, `int16`. |
| `AudioStreamError` | Listing devices, opening, reading, stopping, or publishing the WAV failed. |
| `AudioCaptureStateError` | `start()` or `stop()` was used out of order on `AudioCapture`. |

All of them subclass `AudioCaptureError`.

| Failure | Result | Next state |
|---|---|---|
| `start()` fails | none | `IDLE` |
| `stop()` fails after release | none | `IDLE` |
| `stop()` fails after the maximum duration | none | `WAITING_FOR_RELEASE` until release |

The controller does not look for a leftover `.recording` file. `AudioCapture`
removes it.

## Diagnostic command

`voicestock-pi-ptt` runs `pi.push_to_talk.manual:main`. It prints one result
or one error and leaves a successful WAV in `--output-directory`. Arguments
and the expected printout are in the
[setup and manual test](../setup/push-to-talk.md).
