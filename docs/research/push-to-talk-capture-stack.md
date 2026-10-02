# Push-to-talk capture stack

Research record for task **PushToTalk-01**: evaluate the PTT capture stack (GPIO and USB microphone) on a Raspberry Pi 3.

**Status:** research closed. Physical validation on the project Raspberry Pi and USB microphone is still pending. This document is not an Architecture Decision Record. It keeps the evidence of the investigation. A later ADR is not required for these choices unless a future task changes them.

| Area | Status |
| --- | --- |
| GPIO (button input) | Decision recorded. Later implemented by `PushToTalkButton`. Hardware measurements pending. |
| Audio capture stack | Decision recorded below. Not implemented in this task. |
| Audio output contract | Target contract recorded below. Native 16 kHz support is a hardware assumption, not a confirmed fact. |

## Context

VoiceStock targets a Raspberry Pi 3 with **1 GB of RAM** and Python 3.11 (`requires-python` in `pyproject.toml`). The Raspberry Pi 3 Model B is specified by its manufacturer with 1 GB of RAM. The exact board, operating-system image, and kernel used by the project have not been observed yet; that check remains in the GPIO validation table.

The Pi may run without Internet access. Capture must therefore work completely offline. Installing libraries can happen earlier, while a network is available. At runtime, recording must not call a remote service.

Push-to-talk recordings are short utterances from one person, not continuous archival recording. The same board also has to run GPIO handling, local orchestration, SQLite, a local web application, and later speech-to-text. Audio capture is light compared with speech-to-text, but it still shares 1 GB with those components, so the capture path should not pull in libraries that the transport of PCM does not need.

Capture stays independent of:

- physical button handling;
- speech-to-text;
- interpretation of the words;
- inventory business logic.

Silence, noise, or speech that a later stage cannot interpret is not a capture failure when the recording is a technically valid audio artifact. Validity here means the agreed container, encoding, channel count, sample width, and output sample rate, with a duration that matches the time the stream was running. Deciding whether the utterance is useful belongs to later stages.

Development machines and CI may have no microphone, no ALSA device, and no Raspberry Pi. The capture design has to be testable in that environment. Hardware tests remain necessary; they are a different kind of test.

The architectural intent is unchanged: PushToTalk later produces an audio artifact that SpeechToText can consume, without coupling to one STT engine.

## GPIO requirements and comparison criteria

The following requirements are the comparison criteria for the GPIO options. No measurements have been taken against them.

- Compatible with Raspberry Pi 3.
- Compatible with Python 3.11 and Raspberry Pi OS.
- Fully offline operation.
- Detect button press and release.
- Keep the rest of the application running while the button stays pressed.
- Allow software debounce.
- Keep application logic decoupled from unnecessary electrical detail.
- Allow tests of that logic before the real hardware is available.

## Alternatives considered

### GPIO Zero

Identified advantages:

- High-level, device-oriented API.
- `Button` abstraction.
- Event and callback support for press and release.
- Software debounce support.
- Internal pull-up support.
- GPIO can be mocked so the logic can be tested without a physical Raspberry Pi.
- The application works with device-level actions instead of electrical edges.

### RPi.GPIO

RPi.GPIO was considered a valid and known alternative. It exposes an API closer to traditional GPIO handling, including pin setup and event detection.

For this case, no requirement was identified that would justify working at that level of abstraction instead of GPIO Zero.

### Lower-level GPIO APIs

Lower-level options such as lgpio, libgpiod, and equivalent backends were considered.

No current PushToTalk requirement was identified that would justify the application managing GPIO at that level.

The implementation GPIO Zero uses internally is separate from the API VoiceStock would call. Those layers stay distinct.

## Interaction model

Three models were compared conceptually:

- polling;
- blocking wait;
- callbacks / events.

**Decision:** an event-driven model.

The button changes state infrequently, and the application needs to keep doing other work while the button remains pressed.

GPIO Zero can represent the semantic events directly:

- `pressed`
- `released`

Application logic uses those events. It does not depend directly on rising or falling edges.

## Concurrency

GPIO callbacks must stay short. Full audio capture stays outside the button callback.

A callback only communicates the state change to another component or execution context.

How that hand-off is coordinated is still open. Threads, processes, or another concurrency primitive have not been chosen. That choice belongs to a later PushToTalk task. This research does not design it.

The boundary recorded for now is:

```text
GPIO event → notification / state change → audio capture outside the GPIO callback
```

The same boundary applies to audio callbacks. See [Audio callback constraints](#audio-callback-constraints).

## Electrical configuration

Wiring fixed by the button research and by the later `PushToTalkButton` implementation:

- internal pull-up;
- button connected between GPIO and GND;
- electrically active-low signal.

| Button state | GPIO level |
| --- | --- |
| released | HIGH |
| pressed | LOW |

Application logic uses the semantic `pressed` / `released` abstractions from the input component. It does not depend on this electrical inversion.

The concrete GPIO pin is not decided.

## Debounce

Software debounce uses the support provided by GPIO Zero.

A definitive `bounce_time` is not fixed. The initial value has to be validated on the real button and adjusted if needed.

## GPIO decision

The library choice below is closed. "Pending" applies to measurements on the physical Pi, not to a still-open choice of GPIO library.

| Topic | Choice |
| --- | --- |
| Library / API | GPIO Zero |
| Interaction model | Event-driven callbacks |
| Electrical configuration | Internal pull-up, button to GND, active-low |
| Application events | `pressed` / `released` |
| Callback responsibility | Notify state or event only. Long-running audio capture stays outside GPIO callbacks. |
| Debounce | Software debounce through GPIO Zero. Exact timing pending hardware validation. |
| GPIO pin | Pending hardware integration. |

`PushToTalkButton` implements that contract: `gpiozero.Button` with `pull_up=True`, `bounce_time` passed through, and external `on_pressed` / `on_released` callbacks. This research does not reopen that design.

## Linux and Raspberry Pi audio stack

`sounddevice` and PyAudio are not USB drivers. They do not talk to the microphone's USB descriptors. On the Pi the path is:

```text
VoiceStock application
        ↓
Python audio library          sounddevice or PyAudio
        ↓
PortAudio                     cross-platform audio I/O API
        ↓
ALSA                          Linux host API used by PortAudio
        ↓
Linux USB Audio driver        kernel module snd-usb-audio
        ↓
USB microphone                USB Audio Class device
```

| Layer | Responsibility | What it does not do |
| --- | --- | --- |
| VoiceStock | Start and stop a recording when PushToTalk asks, choose the configured input, and produce the audio artifact. | It does not parse USB packets or program the codec. |
| Python library | Expose devices, open a stream, and deliver PCM buffers to Python. | It is not a driver and it is not the WAV contract by itself. |
| PortAudio | One API over several native audio systems. On Linux the relevant host API is ALSA. It can also convert sample **format** and channel layout when the host API requires it. | It does not resample when the native API rejects the requested rate. See [Physical rate and output rate](#physical-rate-and-output-rate). |
| ALSA | PCM devices (`hw`, `plughw`, `default`, and others), mixer controls, and plugin conversions such as the `plug` plugin, which can convert rate, format, and channels. | A Python application does not need to call ALSA directly if PortAudio already does. |
| `snd-usb-audio` | Kernel driver for USB Audio Class devices. It creates the ALSA card that user space sees. | It is not selected or configured by VoiceStock's Python code. |
| USB microphone | Converts sound to digital samples and advertises the rates and channel counts it implements. | It does not know about WAV files or SpeechToText. |

PortAudio's own overview names ALSA as a Linux host API and states that PortAudio does not provide sample-rate conversion when the requested rate is not supported by the native API. ALSA, separately, can convert the rate if the PCM that gets opened is a plugin device (`plug` / `plughw` / often `default`) rather than the raw hardware device `hw:CARD,DEV`. Those are different layers. A successful open at 16 kHz through `default` can mean "ALSA resampled", not "the microphone enumerates 16 kHz".

Troubleshooting later should follow the same stack downward: Python exception from the library, then PortAudio error, then which ALSA device was opened, then whether the USB card exists (`arecord -l`) and whether the kernel driver bound it.

## Audio capture alternatives

### A. `sounddevice` and PortAudio

[`sounddevice`](https://python-sounddevice.readthedocs.io/) is a Python binding for PortAudio, available on Linux, macOS, and Windows. The import name is `sounddevice`. pip installs the distribution `sounddevice`. The conda-forge package name, from the project's installation page, is `python-sounddevice`. This document uses `sounddevice` for the import and `python-sounddevice` when naming the chosen stack.

Two stream families matter:

| API | Buffers | NumPy |
| --- | --- | --- |
| `InputStream` | `numpy.ndarray` in the callback and in `read()` | Required for that path |
| `RawInputStream` | Plain Python buffer objects. `read()` returns a buffer of interleaved samples. | Not required |

`RawInputStream` is the capture API recommended for VoiceStock. PushToTalk only has to move PCM from the device into an artifact. It does not run numerical signal processing in the capture path. The sounddevice installation notes say NumPy is unnecessary for `RawStream`, `RawInputStream`, and `RawOutputStream`. Avoiding NumPy here is an architectural choice about dependencies, not a claim that NumPy would be too heavy for a Raspberry Pi. A later STT engine may use NumPy for its own reasons. Capture should not require it only to hold samples.

Useful behavior, from the sounddevice stream and usage documentation:

- A stream is created inactive. `start()` begins processing and `stop()` ends it. `close()` releases the stream. A stream is also a context manager, which calls `start()` on entry and `stop()` / `close()` on exit.
- If no callback is passed, the stream is in blocking mode and the application reads with `read()`.
- If a callback is passed, PortAudio invokes it when input is available.
- `dtype` for raw streams includes `'int16'`, which is signed 16-bit PCM, interleaved when more than one channel is used.
- `query_devices()` lists devices. Each entry has `name`, `index`, `hostapi`, `max_input_channels`, `max_output_channels`, latency hints, and `default_samplerate`. On Linux the list mixes real hardware devices and virtual ALSA devices. The documented example shows names such as `hw:0,0` and `default`.
- `query_hostapis()` identifies the host API. On the Pi that should be ALSA.
- `check_input_settings()` asks PortAudio `Pa_IsFormatSupported`. If the combination is supported it returns normally. If not, it raises.
- `device` may be an integer index or a query string: space-separated, case-insensitive substrings of the device name and, if needed, the host API name. The implementation raises `ValueError` when nothing matches, and when several devices match and the string is not an exact name of exactly one of them.
- `python3 -m sounddevice` prints the same device list from a terminal. That is useful on the Pi before any VoiceStock UI exists.
- Callback exceptions are printed and are not propagated to the main thread. The callback must not be the place where VoiceStock handles application errors.

Installation, from the same project's installation page: any Python that can run CFFI is in scope, which includes Python 3.11. `pip install sounddevice` on Linux does **not** bundle PortAudio. The system package (commonly `libportaudio2` on Debian and Raspberry Pi OS) has to be present. That is a native dependency, still fully offline once installed. This research does not add the dependency to `pyproject.toml`.

Resource cost of the binding itself is the PortAudio process and the PCM buffers of the open stream. That is small next to speech-to-text. The cost that matters for the contract is the PCM data rate, calculated in [Resource constraints](#resource-constraints).

Hardware-independent tests do not come from mocking PortAudio's C library. They come from keeping stream lifecycle and artifact assembly behind a boundary that a test double can implement. `RawInputStream` is the production side of that boundary.

### B. ALSA `arecord`

`arecord`, from alsa-utils, records `.wav`, `.voc`, and `.au` files through ALSA. It is mature, small, and already the tool the ALSA project uses to test a sound card. A typical manual check is `arecord -vv -f dat foo.wav` (48 kHz, 16-bit, two channels in that preset) and stopping with Ctrl-C. Device, format, rate, and channels can be set explicitly (`-D`, `-f`, `-r`, `-c`). Opening the hardware device rather than `default` shows what the card itself accepts, which is the right check when separating native rate from plugin conversion.

That makes `arecord` the recommended **diagnostic**. On the Pi, a person can list cards, record a few seconds, and play the file back with `aplay` without VoiceStock running. Those checks belong in a later hardware procedure, not in this document as a script.

`arecord` is a weak **application backend** for VoiceStock:

- The Python process would own a child process: start, stop, signals, stdout/stderr, and exit status.
- Errors arrive as text and exit codes, not as a library exception tied to a device and a format.
- Start and stop are process lifetime. That is coarser than `start()` / `stop()` on a stream, and a hard kill can leave a file whose WAV header was never finalized.
- Automated tests would have to fake a process and a sound device, or run ALSA. CI would still need a stand-in, so the subprocess does not remove the need for a test double. It only moves the hardware problem into process management.
- Device names would be ALSA strings (`hw:1,0`, `plughw:1,0`) baked into command lines, which is a poorer fit for a later UI that lists PortAudio devices.

Use `arecord` to validate the microphone and to debug the ALSA layer. Do not use it as the production capture engine.

### C. PyAudio and PortAudio

PyAudio 0.2.14 is also a Python binding for PortAudio. Its documentation describes blocking `read` / `write` and a callback invoked on another thread. Sample formats include `paInt16`. Host APIs include `paALSA`. Unsupported rates surface as PortAudio errors such as `paInvalidSampleRate`. Audio payloads are byte strings, so PyAudio also captures PCM without NumPy.

It is a valid stack for the same USB microphone. It was not rejected as obsolete. The current documentation still presents both I/O styles and the ALSA host API.

Compared with `sounddevice` for this project:

| Point | `sounddevice` | PyAudio |
| --- | --- | --- |
| Native library | PortAudio, ALSA on Linux | PortAudio, ALSA on Linux |
| PCM without NumPy | `RawInputStream` is documented for that | `Stream.read` returns bytes |
| Start and stop | `start`, `stop`, `close`, and a context manager | `open` starts callback streams immediately; `stop_stream` / `close` and `terminate` on the `PyAudio` instance |
| Device list | `query_devices()`, including name, index, channel counts, default rate | `get_device_count()` and `get_device_info_by_index()` |
| Selecting a device | Index or a documented name query | Index. Matching a name is application code |
| Asking whether a format works | `check_input_settings()` | The application opens a stream or calls PortAudio itself |
| Style | Python buffers, exceptions, context manager | Closer to the C API: format constants, manual `terminate()` |

Both can implement explicit PTT capture. `sounddevice` matches the later needs (inspect a device, reject an unsupported format before opening, select by a stable description, test without NumPy) with less adapter code. That is the reason to prefer it, not a claim that PyAudio cannot record.

### D. Direct ALSA from Python

A binding such as pyalsaaudio calls ALSA from Python and skips PortAudio. That is viable on Linux and still offline. It was not given a full column because it does not solve a VoiceStock problem that PortAudio leaves open: the application would depend on ALSA device strings, the same stack would not be what a developer exercises on Windows CI except through a double, and `arecord` already covers manual ALSA checks. PortAudio is the extra layer that keeps device enumeration and format checks in one place for the application.

GStreamer, ffmpeg, or a compressed-audio library would add a media pipeline VoiceStock does not need in order to store a few seconds of PCM.

## Evaluation criteria

| Criterion | `sounddevice` + `RawInputStream` | `arecord` as backend | PyAudio |
| --- | --- | --- | --- |
| Raspberry Pi 3 | PortAudio's ALSA host API is the Linux path. Not yet run on the project board. | Native ALSA. Appropriate on the Pi. | Same PortAudio ALSA path. Not yet run on the project board. |
| Python 3.11 | Supported wherever CFFI runs. No documented exclusion of 3.11. | Subprocess, independent of the Python version. | Current bindings target Python 3. Confirm the wheel or system package when deploying. |
| Offline runtime | Yes, after PortAudio is installed. | Yes. It is part of alsa-utils. | Yes, after PortAudio is installed. |
| CPU and RAM | Stream buffers plus PCM. No NumPy on the raw path. | One extra process and a file. Small. | Comparable to sounddevice. |
| Deploy | `sounddevice` plus the system PortAudio package on Linux. | Usually already present with ALSA. Heavier to supervise from Python. | `pyaudio` plus PortAudio. |
| Enumerate USB inputs | `query_devices()` / `query_hostapis()`. | `arecord -l` and ALSA names. | Device index loop. |
| Configurable device | Index or name query. Index alone is a poor long-term setting. | ALSA device string. | Index, unless the application adds name matching. |
| Explicit start/stop | `start()` / `stop()`. | Process start and signal. | `stop_stream()` / `close()`. Callback streams start at `open()`. |
| PCM and WAV | Delivers PCM. WAV is written by the application, for example with the standard-library `wave` module. | Writes WAV itself. | Delivers PCM bytes. WAV is again application code. |
| Errors | `PortAudioError`, `ValueError` for device queries. | Exit code and stderr. | PortAudio error codes via the binding. |
| Tests without hardware | Feasible if capture talks to a backend interface. Importing PortAudio still needs the library where the production class is constructed. | Requires a fake process or ALSA. | Same testing shape as sounddevice. |
| Maintainability | Small Python surface for PTT. | Process supervision stays in the application forever. | More C-shaped code for the same PortAudio features. |
| Dependency footprint | CFFI, sounddevice, libportaudio. NumPy not required for raw capture. | alsa-utils. No extra Python audio package. | PyAudio and libportaudio. |
| Later PTT orchestration | Stream lifetime maps onto press and release. | Process lifetime maps poorly onto press and release. | Possible, with more manual session handling. |

The recommendation follows from that table: use sounddevice in the application, keep `arecord` as a manual tool, and do not adopt PyAudio unless a later deployment problem blocks sounddevice on the Pi. No such blocker appears in the documentation reviewed here.

## Recommended capture stack

```text
Application API:          python-sounddevice  (import sounddevice)
Capture API:              sounddevice.RawInputStream
Cross-platform audio API: PortAudio
Linux host API:           ALSA
Kernel driver:            snd-usb-audio
Device:                   USB microphone
```

Why this fits VoiceStock:

- Press and release need an explicit start and stop. `RawInputStream` provides that without a child process.
- Device enumeration exposes name, channel count, and default rate, so the application can validate a configuration instead of assuming the only microphone on the board.
- The library sits on PortAudio, and PortAudio sits on ALSA. VoiceStock does not reimplement either.
- Raw buffers are interleaved PCM. Signed 16-bit (`dtype='int16'`) matches the artifact contract without a conversion to floating-point arrays inside the capture callback.
- NumPy is optional for this class. Capture stays a transport.
- Tests of lifecycle and artifact assembly can use another backend. They do not require the Pi, a USB microphone, or the Internet.
- The memory and CPU of reading PCM are minor beside speech-to-text on a 1 GB machine, provided recordings stay short and are handled in chunks. See [Resource constraints](#resource-constraints).

This task does not implement the stream, add the dependency, or write setup scripts.

Blocking `read()` and a callback are both available. For a push-to-talk utterance, a callback (or a read loop that only copies blocks out of the audio thread) fits the rule that the audio thread stays small. The later orchestration task chooses the concrete hand-off. This research only forbids putting application work inside the callback.

## Audio callback constraints

PortAudio runs the stream callback at high or real-time priority. Its documentation forbids, in that callback, memory allocation and deallocation, file and console I/O, context switches, mutexes, and other calls that can block or take an unpredictable time. With few exceptions, PortAudio API functions must not be called from the callback. sounddevice repeats that rule: do not allocate, touch the file system, or call other blocking or unpredictable functions from the callback. An exception raised there is printed and is not delivered to the main thread, so it is also a poor error channel.

The callback may copy the input buffer into storage that was prepared beforehand, or push a chunk toward another context, and then return. It must not:

- decide application state or orchestrate PushToTalk;
- run speech-to-text;
- write the WAV file;
- talk to SQLite or the web application;
- interpret silence or words.

That is the same rule already adopted for GPIO:

```text
event or callback
        ↓
minimal work
        ↓
hand off the event or the bytes
        ↓
ordinary application code does the work
```

PortAudio also offers blocking `Pa_ReadStream`, exposed as `RawInputStream.read()`. Blocking reads are allowed to wait, and they run in the caller's thread, so they are a reasonable way to fill an artifact if that caller is already a worker rather than the GPIO callback. They do not remove the need to keep the GPIO callback and any real-time audio callback short. Choosing between a PortAudio callback plus a queue, and a blocking read on a worker, is an implementation decision for the later orchestration task. Both can respect this constraint. Designing the thread, the queue, or the timeout is out of scope here.

## Audio format contract

The artifact later stages should be able to rely on is:

```text
Container:             WAV (WAVE_FORMAT_PCM)
Encoding:              signed linear PCM, little-endian in the file
Channels:              1 (mono)
Sample width:          16 bit (2 bytes)
Output sample rate:    16 kHz
```

Python's `wave` module in 3.11 reads and writes only uncompressed `WAVE_FORMAT_PCM`. `setsampwidth(2)`, `setnchannels(1)`, and `setframerate(16000)` match this contract. Compression type `NONE` is the only one the module accepts. That standard-library writer is a sufficient way for a later task to store the artifact. It is not implemented here.

### WAV

WAV is a simple container around PCM. Short files can be opened with ordinary players and with `aplay`, and speech tools commonly accept them. A push-to-talk utterance does not need a streaming container or a compressed bitstream. The header records rate, channels, and sample width, so a later stage can reject a file that does not match the contract without guessing.

### Linear PCM

Lossy codecs (Opus, MP3, AAC) exist to save bandwidth or long-term storage. These recordings stay on the Pi, last on the order of seconds, and may be transcribed locally. Compression would spend CPU to shrink a payload that is already small, and it would add a decoder in front of speech-to-text. Uncompressed signed PCM keeps the samples that the microphone path produced, aside from an explicit resample or downmix when the hardware cannot emit the contract format directly.

### Mono

One person speaks into one microphone. A second channel does not add linguistic information for this product. Stereo would double the data rate and force every later stage to define a downmix. The contract is one channel. If a given USB device refuses mono, the capture path may read the channel count the device does support and reduce it to one channel **before** the artifact is published. The published file is still mono. That reduction is part of normalization in a later task, not part of this research's implementation.

### 16-bit samples

16-bit signed PCM is the usual spoken-word width: enough dynamic range for a close microphone, one of PortAudio's native integer formats (`int16` / `paInt16`), and the width `wave` stores as two bytes. 8-bit is coarser and, in WAV, often unsigned. 24-bit and 32-bit float increase the data rate and are not required to move speech into a recognizer that will itself resample and quantize. 16-bit is the compatibility point, not a claim about the microphone's internal converter.

### Output rate of 16 kHz

16 kHz covers the band used for speech intelligibility and is a common input rate for speech-to-text. It is the **output contract**, not a promise that the USB device's hardware rate is 16 kHz. The distinction is the next section.

## Physical rate and output rate

```text
physical capture format          what the opened device can deliver
        ≠
VoiceStock output contract       WAV, signed 16-bit PCM, mono, 16 kHz
```

Many USB microphones expose 44.1 kHz or 48 kHz as a hardware rate, and some also expose 16 kHz. This research did not inspect the project microphone. No rate is claimed as native.

What the stack can tell a later implementation:

- `query_devices()` reports `default_samplerate` for each device. That is the device's default, not the full set of legal rates. PortAudio's device-query documentation says a single advertised rate is not enough, because devices differ in whether they support a range, a list, or only some combinations of rate and channel count.
- `check_input_settings(device=..., channels=1, dtype='int16', samplerate=16000)` calls `Pa_IsFormatSupported`. Success means PortAudio believes that device can be opened with those parameters. Failure raises. `paInvalidSampleRate` is the PortAudio code for a rejected rate.
- PortAudio will convert sample **format** (for example to the integer width the host needs). It will not invent a sample rate the host API refuses.
- ALSA's `plug` plugin can convert rate, format, and channels. If the opened PortAudio device is a virtual device such as `default` or `plughw`, a successful 16 kHz check can be ALSA resampling under the requested rate. If the opened device is the raw `hw` PCM, a failed check means that hardware interface rejected the combination.

Policy for the later capture implementation (not built here):

```text
Can the selected device be opened at
16 kHz / mono / signed 16-bit?
              │
        ┌─────┴─────┐
       yes          no
        │            │
        ▼            ▼
capture directly   capture at a rate and channel
at 16 kHz mono     count the device accepts
                   (the reported default rate is
                   the first candidate, not a guess
                   that every microphone is 48 kHz)
                         │
                         ▼
                  normalize: resample to 16 kHz
                  and downmix to mono if needed
                         │
                         ▼
                 contractual 16 kHz mono artifact
```

A "yes" from `check_input_settings` is permission to open that PortAudio device at the contract rate. It is not, by itself, proof that the USB hardware lists 16 kHz. The hardware procedure should also try the `hw` device with `arecord` so the report can say whether 16 kHz was native or converted. Until that procedure is run on the project microphone, direct 16 kHz capture stays an assumption.

Resampling algorithms are not chosen or implemented in this task.

## Input device selection

PortAudio numbers devices. `query_devices()` shows those indexes. The numbers are an enumeration order, not a hardware identity. Plugging another USB device, changing ALSA's card order, or moving from a developer laptop to the Pi can assign the microphone a different index. A setting of `device = 2` would then open whatever now sits at index 2, including an output-only virtual device.

The capture component should receive an already chosen input identity and resolve it:

```text
configuration (input device)
        ↓
resolution against query_devices()
        ↓
check_input_settings() for the requested format
        ↓
RawInputStream
```

Reasonable configuration values, using information the stack already exposes:

- a name query in the sense sounddevice documents (substrings of the device name, plus the host API name when needed);
- a saved exact `name` from `query_devices()`, which the library treats as a single exact match when several substring hits exist;
- an index only as a diagnostic override, not as the stored deployment setting.

Observed failure cases the later implementation should surface, matching sounddevice's query behavior and PortAudio's format check:

| Situation | What the stack does | What VoiceStock should report |
| --- | --- | --- |
| No device matches the configured name | `ValueError`: no input device matching the query | No matching input device |
| Several devices match and the string is not an exact name of one of them | `ValueError`: multiple devices found, with indexes and names | Ambiguous input device |
| The device exists but rejects the requested rate, channel count, or sample format | `check_input_settings` / stream open raises a PortAudio error | Selected device is incompatible with the requested settings. The caller then applies the normalize path in the previous section, or fails if no supported capture format can be opened. |
| The resolved device has `max_input_channels` less than 1 | Not an input device | Same as no matching input |

The production exception types and the settings object are part of the later capture task. They are not defined here.

## Future microphone selection in the web interface

Because the device is configuration, a later local UI can list inputs and store a choice without changing the capture code:

```text
sounddevice / PortAudio
        ↓
available input devices
        ↓
application
        ↓
local web interface
        ↓
user selects a microphone
        ↓
stored configuration
        ↓
AudioCapture reads that configuration
```

The UI is not part of this task and is not a prerequisite for implementing capture. Capture should accept the selected device without knowing whether the value came from a file, a deployment setting, a command-line argument, a database, or that future page.

`query_devices()` is the source of the list a UI would show (name, input channel count, default rate, host API). Building that page is out of scope.

## Testing implications

CI and developer machines may have no microphone. The production class that opens `RawInputStream` cannot be the only way to test "start, receive chunks, stop, emit a WAV that meets the contract".

The intended split is conceptual. Class names are not frozen:

```text
capture lifecycle and artifact assembly
        ↓
audio input backend
        │
        ├── production backend
        │     sounddevice.RawInputStream
        │     PortAudio → ALSA → USB microphone
        │
        └── test double
              yields scripted PCM chunks
              no Pi, no microphone, no ALSA device, no network
```

Automated tests should cover the behavior that does not need hardware: start/stop lifecycle, chunk assembly, WAV header fields, mono 16-bit 16 kHz output after a fake source, and the failure reports for a missing, ambiguous, or incompatible device when those checks are given a fake device list. They do not prove that a USB microphone works.

Hardware integration tests, or a documented manual procedure, still have to run on the Raspberry Pi with the project microphone: the device is listed, press-to-stop duration matches, the file plays, the contract fields are present, and the native-versus-converted 16 kHz question is answered. `arecord` and `aplay` are the manual tools for the ALSA portion of that procedure.

Importing `sounddevice` loads PortAudio. A test double should allow the lifecycle tests to run without opening a hardware device. Whether CI installs the PortAudio shared library is a deployment detail for the later implementation, not a reason to call the network during a test.

## Resource constraints

The Raspberry Pi 3 class of board used as the project target has 1 GB of RAM. VoiceStock shares that memory with GPIO, orchestration, SQLite, a local web application, and speech-to-text. Capture should stay small and predictable.

Signed 16-bit mono PCM:

```text
bytes per second = sample rate × 2 bytes × 1 channel
```

| Format | Bytes per second | Per minute |
| --- | --- | --- |
| 16 kHz, 16-bit, mono | 16 000 × 2 = 32 000 bytes/s (32 kB/s) | 32 000 × 60 = 1 920 000 bytes ≈ 1.9 MB |
| 48 kHz, 16-bit, mono | 48 000 × 2 = 96 000 bytes/s (96 kB/s) | 96 000 × 60 = 5 760 000 bytes ≈ 5.8 MB |

Figures use decimal MB (1 MB = 10^6 bytes). A 10-second utterance at the contract rate is about 320 kB. A 10-second utterance captured at 48 kHz mono 16-bit, before resampling, is about 960 kB. Both are small beside 1 GB, including a temporary copy of the same bytes.

That is not a reason to buffer arbitrarily long audio in RAM. The stream API already delivers blocks (`blocksize`, callback buffers, or `read(frames)`). The later implementation should be able to write or forward those blocks as they arrive. The contract rate of 16 kHz also keeps the artifact smaller than leaving 48 kHz PCM for every downstream stage. Speech-to-text and the rest of the application are expected to dominate CPU and RAM. This research has no measurement of an STT engine on the project Pi.

No capture benchmark was run on the board.

## Research conclusion

### What was chosen

| Topic | Decision |
| --- | --- |
| Button library | GPIO Zero, event callbacks, pull-up, active-low. Implemented by `PushToTalkButton`. |
| Capture library | `sounddevice` (`python-sounddevice`) |
| Stream API | `RawInputStream` |
| Underlying API | PortAudio |
| Linux backend | ALSA, over the kernel USB audio driver |
| Container | WAV |
| Encoding | Signed linear PCM |
| Channels | Mono in the artifact |
| Sample width | 16 bit |
| Output rate | 16 kHz |
| Physical 16 kHz | Not confirmed. Open the contract rate when the device allows it; otherwise capture a supported format and normalize. |
| Device selection | Configurable identity resolved by name. Not a hardcoded index. |
| Capture model | Chunked stream. The audio callback, if used, only moves bytes. |
| Internet at runtime | Not required |
| Automated tests | Hardware-independent backend or test double for lifecycle and artifacts |
| Manual checks | `arecord` / `aplay` on the Pi |
| Production `arecord` | Not selected |

### Why

GPIO Zero already matched the button: semantic press and release, debounce, pull-up, and tests without a Pi. Lower-level GPIO APIs added electrical detail the application does not need.

For audio, `RawInputStream` is a small PortAudio binding with explicit start and stop, device queries, a format check, and PCM buffers that do not require NumPy. PyAudio can do the same job with a more manual API and weaker built-in name selection, so it is the fallback if the Pi deployment blocks sounddevice, not the default. `arecord` is the right ALSA probe and the wrong process to supervise inside the application. Direct ALSA bindings and compressed pipelines do not improve the offline, short-utterance, testable capture path.

WAV, 16-bit mono PCM at 16 kHz is a widely readable speech artifact, small at PTT durations, and independent of the recognizer. The microphone is allowed to capture at another rate or channel count; the artifact is not.

### What was evaluated and set aside

| Alternative | Why it was not the application choice |
| --- | --- |
| RPi.GPIO and lower-level GPIO | More electrical detail than the button requirements need. |
| `arecord` as the capture engine | Subprocess control, weaker errors, awkward tests. Kept as a diagnostic. |
| PyAudio | Valid PortAudio binding. More C-shaped API and index-oriented devices for the same ALSA path. |
| Direct ALSA Python bindings | Linux-only device strings without a benefit over PortAudio for this application. |
| Compressed or multimedia pipelines | Extra CPU and dependencies for files that are already small. |
| Hardcoded device index | Enumeration order is not identity. |
| Assuming every microphone opens at 16 kHz | PortAudio and ALSA do not guarantee that. |

### Assumptions still open

- The project board is a 1 GB Raspberry Pi 3, running a Raspberry Pi OS kernel that binds the project USB microphone with `snd-usb-audio`.
- PortAudio's ALSA host API on that image can open the microphone through `sounddevice`.
- The microphone's native rates and channel counts are unknown until the hardware procedure runs.
- `bounce_time`, the GPIO pin, and the concurrency primitive used to leave the GPIO callback are still undecided.
- No latency, CPU, or recognition measurement exists yet.

### What has to be validated on hardware

GPIO checks:

| Check | Status |
| --- | --- |
| Exact Raspberry Pi model | Pending |
| Raspberry Pi OS in use | Pending |
| Kernel | Pending |
| Python version on the device | Pending |
| GPIO Zero version and effective backend | Pending |
| Correct press detection | Pending |
| Correct release detection | Pending |
| No duplicate events caused by bounce | Pending |
| No lost events | Pending |
| Behavior under rapid presses | Pending |
| Multiple press / hold / release cycles | Pending |
| Holding the button does not block other concurrent work | Pending |
| `bounce_time` adjustment, if needed | Pending |
| GPIO pin finally used | Pending |

Audio checks:

| Check | Status |
| --- | --- |
| USB microphone present as an ALSA card (`arecord -l`) | Pending |
| Which PortAudio device name and host API it appears as | Pending |
| `default_samplerate` and `max_input_channels` | Pending |
| Whether `hw` accepts 16 kHz, mono, S16_LE | Pending |
| Whether PortAudio `check_input_settings` accepts 16 kHz mono `int16` on the device VoiceStock will open | Pending |
| If not, which rate and channel count are used before normalization | Pending |
| A short WAV plays back and matches the contract after normalization | Pending |
| `sounddevice` and `libportaudio` install cleanly on the project image | Pending |

### Effect on later tasks

- Button detection can keep using `PushToTalkButton`. This document does not change it.
- A later capture task implements `RawInputStream`, device resolution, the format check, chunked reading, and the WAV contract, including normalization only when the opened device cannot produce 16 kHz mono 16-bit directly.
- A later orchestration task starts and stops that capture from button activity and chooses the hand-off out of the callback. It should keep both the GPIO callback and any PortAudio callback free of transcription and business logic.
- Speech-to-text consumes the artifact and does not open the microphone.
- A microphone picker in the web UI, if it is built, writes configuration. It is not required to implement capture.
- Interface documentation and an ADR were intentionally not added here.

## Sources

Primary documentation used for the audio conclusions:

- python-sounddevice 0.5.2, *Play and Record Sound with Python*, *Installation*, *Usage*, *Streams*, *Raw Streams*, and *Checking Available Hardware*: <https://python-sounddevice.readthedocs.io/en/0.5.2/>. Device-query errors for no match and multiple matches are the `ValueError` paths in `_get_device_id` in that version's `sounddevice.py` (also published with the API sources).
- PortAudio, *API Overview* (host APIs including ALSA; no sample-rate conversion when the native API does not support the rate; format conversion is separate): <https://www.portaudio.com/docs/v19-doxydocs/api_overview.html>.
- PortAudio, *Writing a Callback Function* and the stream-callback contract in `portaudio.h`: <https://www.portaudio.com/docs/v19-doxydocs/writing_a_callback.html>.
- PortAudio, *Enumerating and Querying PortAudio Devices* (`Pa_IsFormatSupported`): <https://www.portaudio.com/docs/v19-doxydocs/querying_devices.html>.
- ALSA library, *PCM (digital audio) plugins* (`plug` converts channels, rate, and format): <https://www.alsa-project.org/alsa-doc/alsa-lib/pcm_plugins.html>.
- ALSA project wiki, *Matrix:Module-usb-audio* (`snd-usb-audio`) and *SoundcardTesting* (`arecord` as the recording check): <https://www.alsa-project.org/wiki/Matrix:Module-usb-audio>, <https://www.alsa-project.org/wiki/SoundcardTesting>.
- alsa-utils README: `arecord` captures `.wav`, `.voc`, and `.au`: <https://git.alsa-project.org/?p=alsa-utils.git;a=blob_plain;f=README.md;hb=HEAD>.
- PyAudio 0.2.14 documentation (PortAudio bindings, blocking and callback I/O, `paInt16`, `paALSA`, `paInvalidSampleRate`): <https://people.csail.mit.edu/hubert/pyaudio/docs/>.
- Python 3.11, `wave` (WAVE PCM only): <https://docs.python.org/3.11/library/wave.html>.
- Raspberry Pi 3 Model B product page (1 GB RAM on that model): <https://www.raspberrypi.com/products/raspberry-pi-3-model-b/>. The project board itself has not been identified on the bench; see the pending hardware table.
- pyalsaaudio, a Python binding to ALSA, considered only as the direct-ALSA alternative: <https://larsimmisch.github.io/pyalsaaudio/>.
