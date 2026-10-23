# TC-PTT-001 — Integrated physical push-to-talk

- Status: DESIGNED
- Executions: none
- Procedure version: 2

## Objective

Show that `voicestock-pi-ptt` records a WAV when the physical button is
pressed and released, using the GPIO adapter and the USB microphone
together, and that a person can hear the predetermined phrase in that
file. The PC is not contacted.

## Test level and type

Level: integration.

Type: functional.

## Requirements and ClickUp traceability

- ClickUp: [PushToTalk-06](https://app.clickup.com/t/86e3euv9u).
- Requirement: the manual command wires `PushToTalkButton`,
  `PushToTalkController`, and `AudioCapture`.

## Source modules and documentation

- `pi.push_to_talk.manual`.
- `pi.push_to_talk.controller.PushToTalkController`.
- [Push-to-talk setup](../../../setup/push-to-talk.md).
- [Integrated runtime](../../../setup/pi-runtime.md) describes the separate
  `voicestock-pi` command. This case does not start that command.

## Preconditions and dependencies

- [TC-GPIO-001](TC-GPIO-001.md) and [TC-AUD-002](TC-AUD-002.md) have
  executions that are not **FAILED** or **BLOCKED**.
- The GPIO pin is free and the microphone query is the one from TC-AUD-001.

## Required hardware and software

- Raspberry Pi 3, button, USB microphone.
- `voicestock-pi-ptt` on `PATH` inside the project environment.
- A playback path for the WAV files. Headphones or a speaker, on the Pi or
  on another machine that only plays the file. Record the host, the
  program (`aplay`, a desktop player, or another named program), and the
  output device. If the device has no readable name, write UNKNOWN. Do not
  send the file to the VoiceStock PC server in order to play it.

## Preparation

```bash
mkdir -p recordings/tc-ptt-001
```

Do not pass `--send-to-pc`. Do not pass `--delete-after-send`.

## Execution

```bash
voicestock-pi-ptt \
  --pin <BCM_PIN> \
  --bounce-time 0.05 \
  --input-device "<QUERY>" \
  --output-directory recordings/tc-ptt-001 \
  --max-duration 60
```

`<BCM_PIN>` and `<QUERY>` come from the earlier executions. `60` is the
product default (`DEFAULT_MAX_DURATION_SECONDS`), not a measured limit of
the microphone. This case must release the button before 60 seconds so the
termination reason is `RELEASED`.

Wait until the process prints:

```text
Waiting for the push-to-talk button. Press Ctrl+C to quit.
```

That line is from `pi.push_to_talk.manual`. The setup guide quotes only the
first sentence. The functional criteria use the full line.

The spoken text is fixed so the listener knows which phrase belongs to
which file. Say only that phrase during the hold. The practice phrase is
excluded from the listening result.

| Hold | Phrase | Counts toward acceptance |
| --- | --- | --- |
| Practice | `práctica` | No |
| Measured 1 | `prueba de voz uno` | Yes |
| Measured 2 | `prueba de voz dos` | Yes |
| Measured 3 | `prueba de voz tres` | Yes |

One practice hold, then the three measured holds. For each hold:

1. Press, say the phrase for that row, and release before 60 seconds.
2. Read the printed artifact id, path, duration, termination, and format.
3. Write the path next to the phrase in the notes before the next press.
4. Wait until the shell is idle of new output.

After the three measured holds, press Ctrl+C. Play each measured WAV once
and fill the listening table in
[Observations and evidence](#observations-and-evidence). The listener is
the operator, or a second person in the same session. The judgment is
subjective. It is not a sound-pressure level, a distortion figure, or a
word error rate. Do not run speech-to-text on these files for this case.

```bash
sha256sum recordings/tc-ptt-001/*.wav
python - <<'PY'
import wave
from pathlib import Path
for path in sorted(Path("recordings/tc-ptt-001").glob("*.wav")):
    with wave.open(str(path), "rb") as wav:
        print(path.name, wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes())
PY
```

## Observations and evidence

- The command transcript for each hold, with the phrase written beside the
  path.
- SHA-256 and `wave` fields. These are the objective metadata.
- Playback host, program, and output device.
- A separate listening table, one row per measured file. This table is the
  subjective assessment. Do not merge it into the `wave` numbers.

| File | Expected phrase | Intelligible | Matches the phrase | Only silence | Severe distortion | Obvious truncation |
| --- | --- | --- | --- | --- | --- | --- |
| | `prueba de voz uno` | yes or no | yes or no | yes or no | yes or no | yes or no |
| | `prueba de voz dos` | yes or no | yes or no | yes or no | yes or no | yes or no |
| | `prueba de voz tres` | yes or no | yes or no | yes or no | yes or no | yes or no |

The listener may look at the assigned phrase. "Intelligible" means those
words can be made out in the audio. A file that is silence or noise, and
that only "matches" because the listener read the script, is not
intelligible. "Matches the phrase" means the words heard are that phrase
and not a different sentence. "Only silence", "severe
distortion", and "obvious truncation" are yes when that defect is what the
listener hears. A yes in any of those three columns fails the file. A no
in "intelligible" or in "matches the phrase" also fails the file.

- Whether Ctrl+C returned the shell.

## Metrics

| Metric | Rule |
| --- | --- |
| Holds that print `Termination: RELEASED` | 3 of 3 measured |
| Format line | `WAV / 16 kHz / mono / 16-bit` as printed by the command, confirmed with `wave` |
| Listening result | 3 of 3 measured files intelligible, matching the assigned phrase, and not silence-only, severely distorted, or obviously truncated |
| User-observed press-to-print time | Optional stopwatch. **TO BE DEFINED** as a gate. Not GPIO latency. Not an acoustic metric. |

## Acceptance criteria

1. Each measured hold prints `Capture completed`, a path ending in `.wav`,
   `Termination: RELEASED`, and the format line above.
2. The file from that path exists after the command returns and matches the
   format checks of TC-AUD-002 (1 channel, width 2, rate 16000, frames > 0).
   A file that meets this criterion and fails the listening table still
   fails the case.
3. Each measured file has listening answers intelligible = yes, matches
   the phrase = yes, only silence = no, severe distortion = no, and
   obvious truncation = no. The playback method and equipment are recorded.
   The table stays separate from the WAV metadata. Passing this criterion
   is not a claim of an objective acoustic measurement, and it is not a
   speech-to-text result.
4. The command does not print an HTTP envelope. `--send-to-pc` was not used.
5. Ctrl+C stops the process without leaving it running. A hold that was in
   progress at Ctrl+C may be reported as `RELEASED`; that extra file is
   labeled `shutdown` and is not one of the three measured holds.
6. Files remain on disk. This command does not delete them unless asked.

## Failure conditions

- No output on a press: **FAILED**.
- A measured file that is silent, unintelligible, a different phrase,
  severely distorted, or obviously cut off: **FAILED**, even when the WAV
  header is valid.
- The listening table was not filled, or the playback equipment was not
  named: the speech criterion is not met. The case cannot be
  **CLOSED_PASSED**.
- Termination `MAX_DURATION` on a hold the operator released within a few
  seconds: **FAILED**.
- The process cannot open the GPIO pin or the device: **FAILED** if the
  earlier cases passed on this same wiring; otherwise **BLOCKED** with the
  exception text.

## Recovery and cleanup

Ctrl+C. Confirm with the shell that the process is gone. Archive the WAV
files outside git and record the checksums. Do not commit them.

## Limitations and exclusions

This case does not send audio, does not start the web UI, and does not
cover the maximum duration. That is TC-PTT-002. It does not replace
TC-AUD-002, because a failure here could be the button rather than the
microphone. Hearing the phrase does not measure recognition accuracy and
does not close a speech-to-text task. The listening notes are an operator
judgment written beside the objective file metadata.
