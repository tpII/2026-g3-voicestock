# TC-PTT-001 — Integrated physical push-to-talk

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that `voicestock-pi-ptt` records a WAV when the physical button is
pressed and released, using the GPIO adapter and the USB microphone
together, without contacting the PC.

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

One practice hold, then three measured holds:

1. Press, speak for about two seconds, release.
2. Read the printed artifact id, path, duration, termination, and format.
3. Wait until the shell is idle of new output before the next press.

After the three holds, press Ctrl+C.

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

- The command transcript for each hold.
- SHA-256 and `wave` fields.
- Whether Ctrl+C returned the shell.

## Metrics

| Metric | Rule |
| --- | --- |
| Holds that print `Termination: RELEASED` | 3 of 3 measured |
| Format line | `WAV / 16 kHz / mono / 16-bit` as printed by the command, confirmed with `wave` |
| User-observed press-to-print time | Optional stopwatch. **TO BE DEFINED** as a gate. Not GPIO latency. |

## Acceptance criteria

1. Each measured hold prints `Capture completed`, a path ending in `.wav`,
   `Termination: RELEASED`, and the format line above.
2. The file from that path exists after the command returns and matches the
   format checks of TC-AUD-002 (1 channel, width 2, rate 16000, frames > 0).
3. The command does not print an HTTP envelope. `--send-to-pc` was not used.
4. Ctrl+C stops the process without leaving it running. A hold that was in
   progress at Ctrl+C may be reported as `RELEASED`; that extra file is
   labeled `shutdown` and is not one of the three measured holds.
5. Files remain on disk. This command does not delete them unless asked.

## Failure conditions

- No output on a press: **FAILED**.
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
microphone.
