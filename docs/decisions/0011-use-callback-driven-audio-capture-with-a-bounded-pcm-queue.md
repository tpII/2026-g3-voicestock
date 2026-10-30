# ADR-0011: Use callback-driven audio capture with a bounded PCM queue

## Status

Accepted. Accepted because `SoundDeviceBackend` in this branch implements the
decision and `AudioCapture` keeps the same public lifecycle. Acceptance is an
architecture and implementation decision. It is not a claim that this code
has passed `TC-AUD-002` on the Raspberry Pi. That procedure has to be run
again, from the validation workflow, after the change is integrated. The
original failure record stays valid.

## Context

VoiceStock records a push-to-talk utterance on the Raspberry Pi and publishes
one WAV: signed 16-bit mono PCM at 16000 Hz. `AudioCapture` owns that file
and a worker thread. `AudioInputBackend` is the PCM source: `start`, `read`,
`stop`, and `close`. `SoundDeviceBackend` is the production source. It uses
`sounddevice` and PortAudio. ALSA sits under PortAudio. The stack choice is
[ADR-0003](0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md).
The module split and the WAV contract are the
[capture interface](../interfaces/push-to-talk-capture.md).

The first backend opened `sounddevice.RawInputStream` without a callback and
called blocking `read` on the capture worker. `AudioCapture.stop` signaled
shutdown, called `abort` on the stream, and joined the worker for five
seconds.

During Raspberry Pi validation with a Logitech G435, the raw hardware device
rejected 16000 Hz. An ALSA `plug` device named `voicestock_mic` accepted the
VoiceStock contract because ALSA converted from the headset's 48000 Hz
hardware rate. That profile is a deployment file, documented in
[the ALSA microphone profile](../setup/alsa-microphone.md). It is not this
decision. This decision is how the process stops reading once a device is
already open.

On `voicestock_mic`, `AudioCapture.stop` raised `AudioStreamError: audio
capture worker did not stop`. An isolated PortAudio test on the same board
then showed a reader blocked in `RawInputStream.read(1024)`. `stream.abort()`
returned in about 0.000166 seconds and the reader was still alive after a
five-second join. `stream.stop()` also returned immediately, and that reader
was still alive after its join. No capture process was left behind after the
diagnostic process itself exited. Those observations are about that hardware
and software combination. They are not a claim about every device or every
PortAudio version.

A later standalone diagnostic on the same Pi used `RawInputStream` with a
callback, a bounded `queue.Queue`, a consumer thread, and an explicit
shutdown event. The run used `voicestock_mic`, 16000 Hz, mono, `int16`,
1024-frame blocks, and 32 queue slots. It recorded 46 callback blocks, 46
blocks consumed, no queue overflow, no PortAudio status, a consumer that was
not alive after shutdown, a shutdown of about 0.144808 seconds, and a stream
that closed. The notes from that run were left on the Pi at
`~/voicestock-test-evidence/TC-AUD-002-callback-diagnostic.log`. They are
evidence that this shape can run on that board. They are not an execution of
the formal `TC-AUD-002` procedure, and they were not produced by the
production module.

## Decision

`SoundDeviceBackend` opens `RawInputStream` with a callback. The callback
copies each PCM block into a bounded queue and returns. `read` blocks on that
queue. `stop` closes the queue before it aborts the stream, so a waiting
`read` is released even if `abort` does not unblock a PortAudio read. One
queue slot is reserved for a shutdown sentinel so a full data queue can still
be woken. A data block that does not fit is a capture error, not a dropped
frame inside a successful WAV.

`AudioInputBackend` is unchanged. `AudioCapture` still starts the worker,
writes PCM, and publishes the WAV only after a valid header. It now reads
until `read` returns empty bytes, so audio queued before `stop` is written,
and it will not let a worker that missed the join write a file that has
already been closed or replaced.

The PCM contract stays 16000 Hz, one channel, signed 16-bit. The backend does
not resample. Device selection stays a name query. The G435 plug device is
one possible name after that profile is installed, not a device hard-coded
into the backend.

The behavior is described in
[audio capture](../architecture/audio-capture.md).

## Alternatives considered

### 1. Keep blocking reads and increase the join timeout

Rejected. The failure was not a worker that needed more than five seconds to
notice `abort`. The isolated test left the reader blocked after `abort` had
already returned. A longer join would still report `audio capture worker did
not stop` and would still risk the worker writing after the file was closed.
No measurement in the diagnostic showed a blocking read resuming later.

### 2. Keep blocking reads and call `abort()` or `stop()`

Rejected for this backend, on the evidence above. Both calls returned
quickly and neither released the blocked `read` in that test. The production
code had already called `abort`. Repeating it, or switching the call to
`stop`, does not follow from the observation. This alternative would be worth
reopening if a different device or PortAudio build showed that `abort`
unblocks `read` and the callback design proved unsuitable. That evidence is
not what the Pi test showed.

### 3. Callback stream and a bounded queue

Chosen. The callback returns without waiting for the WAV writer. `read` waits
on a queue the process controls, so shutdown does not depend on PortAudio
unblocking `read`. The standalone diagnostic showed that shape stopping in
well under a second on the same virtual device. The production queue matches
that capacity: 32 data blocks, plus one slot that only shutdown uses.

This alternative costs a second concurrency domain. The callback must not do
file I/O, and a full queue must become an explicit error or the recording
could be published with a gap. Those rules are part of the implementation.

### 4. Replace `sounddevice`

Not chosen. [ADR-0003](0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md)
already compared `sounddevice`, `arecord`, and PyAudio. `arecord` would move
lifetime and shutdown into a child process. PyAudio can record with a
callback, which is the same shape as this decision, but it would replace a
dependency the project already uses. The observed defect was the blocking
read, not an inability of `sounddevice` to open the device. `RawInputStream`
already accepts a callback and does not require NumPy.

## Consequences

### Positive

- A consumer blocked in `read` is woken by the queue, including when the
  queue is full and including when `abort` does not unblock a PortAudio read.
- PortAudio delivery is separated from WAV writing. The callback does not
  publish the artifact.
- `AudioCapture`, `AudioInputBackend`, and the 16000 Hz mono int16 contract
  stay in place. Callers and the scripted test backend do not change their
  methods.
- A microphone that already accepts the contract is still selected by name.
  The G435 profile remains optional deployment configuration.

### Negative

- The backend now has a callback thread, a queue, and a sentinel. Shutdown,
  overflow, and callback errors need tests that do not use a microphone.
- The callback copies each block. That allocates on the audio thread. The
  implementation does not add file or network work there, but it also does
  not meet a strict "no allocation in the callback" reading.
- A full queue fails the take. A slow writer loses the recording instead of
  publishing a shorter file that looks valid.
- Callback failures and PortAudio status flags have to be stored for `read`
  to raise. An exception that escaped the callback would not reach the worker.
- Automated tests do not replace a new hardware run. `TC-AUD-002` is still
  outstanding for this implementation.

## Validation

Supporting evidence is the standalone callback diagnostic on the Raspberry Pi,
summarized in Context, including the log path on that machine. It used
PortAudio callbacks and a bounded queue. It did not import `AudioCapture` or
`SoundDeviceBackend` from this branch.

The checks that run in CI and on a development machine are the audio unit
tests. They fake the stream. They do not open ALSA.

No result in this record, and no test added with this change, is a passed
`TC-AUD-002`. After integration, that case has to be executed again and
recorded on the validation branch. Until then the previous failure stands.
