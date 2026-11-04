# TC-AUD-001 — USB microphone detection

- Status: DESIGNED
- Executions: [EX-TC-AUD-001-20261027-01](../executions/EX-TC-AUD-001-20261027-01.md) (`PASSED_PENDING_DOCUMENTATION`, not closed)
- Procedure version: 1

## Objective

Show that the project USB microphone is visible to the same PortAudio
enumeration VoiceStock uses, and record the name the later cases must pass
as `--input-device`.

## Test level and type

Level: hardware validation.

Type: functional, plus a negative probe for an unknown name.

## Requirements and ClickUp traceability

- ClickUp: [PushToTalk-06](https://app.clickup.com/t/86e3euv9u).
- Requirement: capture selects a device by a name query, not by a
  PortAudio index (`SoundDeviceBackend`).

## Source modules and documentation

- `pi.audio.sounddevice_backend.list_input_devices`.
- [Push-to-talk setup](../../../setup/push-to-talk.md).
- [ADR-0003](../../../decisions/0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md).

## Preconditions and dependencies

- [TC-ENV-001](TC-ENV-001.md) recorded whether `import sounddevice` works.
- If that import failed, this case is **BLOCKED**. Installing
  `libportaudio2` or another PortAudio package is a new execution after the
  failure is recorded, not a silent step of this one.
- The button is not required.

## Required hardware and software

- Raspberry Pi 3.
- The project USB microphone, plugged into a Pi USB port. A hub, if used,
  is part of the inventory.
- Project environment with `sounddevice` importable.
- `arecord` is optional. Use it only when it is already installed. Its
  absence does not fail the case. The setup guide keeps `arecord` as a
  diagnostic, not as the VoiceStock backend.

## Preparation

1. Unplug the microphone. Run the list command once and save the transcript
   as the unplugged observation.
2. Plug the microphone into the port that will be used for the rest of the
   campaign. Wait until the shell can see USB settle (two seconds is
   enough; do not invent a longer gate).

## Execution

From the repository root, environment active:

```bash
python -c "from pi.audio.sounddevice_backend import list_input_devices; \
[print(repr(d.name), '|', repr(d.host_api), '|', d.max_input_channels, '|', d.default_samplerate) for d in list_input_devices()]"
```

Repeat the plugged-in command three times, unplugging nothing between them.

If `arecord` is installed:

```bash
arecord -l
```

Negative probe, once:

```bash
python - <<'PY'
from pi.audio.sounddevice_backend import SoundDeviceBackend
try:
    SoundDeviceBackend("voicestock-no-such-microphone").start()
except Exception as exc:
    print(type(exc).__name__)
    print(exc)
PY
```

The expected exception class is `AudioDeviceNotFoundError`. Do not leave a
stream open. `start` on a missing device raises before a stream exists.

Choose the query string from the printed name. The match is a sequence of
case-insensitive parts (`_query_matches`). If several devices match a short
query, a later capture raises `AudioDeviceAmbiguousError`. Record a query
that matches one device, preferably the exact name.

## Observations and evidence

- Unplugged list and three plugged lists.
- The chosen query string.
- `arecord -l` output if the command exists, otherwise "arecord absent".
- The exception class from the negative probe.

## Metrics

| Metric | Rule |
| --- | --- |
| Device present in 3 of 3 plugged lists | Functional |
| Default sample rate | Recorded. A rate other than 16000 Hz does not fail this case. TC-AUD-002 checks the contract. |
| Detection latency | **NOT MEASURED** |

## Acceptance criteria

1. The chosen microphone name appears in all three plugged-in listings,
   with `max_input_channels` at least 1.
2. The name is absent from the unplugged listing, or the execution explains
   why the same name remains (a device built into the board is not the USB
   microphone under test).
3. The negative probe prints `AudioDeviceNotFoundError`.
4. The execution records one query string for later cases and states that
   it is not a PortAudio index.

## Failure conditions

- The USB microphone never appears: **FAILED**.
- `import sounddevice` fails: **BLOCKED** when the baseline already reported
  the missing library and it was not installed in a recorded follow-up.
- More than one device matches the chosen query and the operator still
  writes that query down as unique: **FAILED**.

## Recovery and cleanup

Unplugging is allowed. Replug into the same port before TC-AUD-002. Do not
add a USB quirk or an ALSA config file during this execution.

## Limitations and exclusions

Enumeration does not open the capture contract and does not prove the
microphone can deliver 16 kHz mono PCM. That is TC-AUD-002. `arecord`
output is supporting evidence only.
