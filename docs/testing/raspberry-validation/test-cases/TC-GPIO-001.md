# TC-GPIO-001 — Physical GPIO press and release

- Status: DESIGNED
- Executions: none
- Procedure version: 2

## Objective

Show that a real button, wired to ground with the internal pull-up, produces
one press callback and one release callback through `PushToTalkButton` for
each measured physical action. The measured set is three cycles of three
actions, so nine press callbacks and nine release callbacks.

## Test level and type

Level: hardware validation.

Type: functional. Edge latency is not a criterion.

## Requirements and ClickUp traceability

- ClickUp: [PushToTalk-06](https://app.clickup.com/t/86e3euv9u).
- Requirement: the Pi adapter used by `voicestock-pi` observes press and
  release. Wiring and polarity are those in
  [push-to-talk setup](../../../setup/push-to-talk.md).

## Source modules and documentation

- `pi.input.push_to_talk_button.PushToTalkButton`.
- [ADR-0003](../../../decisions/0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md).
- [Push-to-talk capture](../../../interfaces/push-to-talk-capture.md).

## Preconditions and dependencies

- [TC-ENV-001](TC-ENV-001.md) execution exists.
- No `voicestock-pi`, `voicestock-pi-ptt`, or other process holds the GPIO
  pin.
- The project environment on the Pi imports `gpiozero`. If the baseline
  showed that it does not, this case is **BLOCKED** until a new execution
  records the installation as a deviation from a fresh baseline.

## Required hardware and software

- Raspberry Pi 3 and a momentary button.
- Jumper from the chosen BCM pin to one side of the button, and from the
  other side to GND. BCM numbering. No external pull-up.
- The pin number is the one the operator wires. The examples in the setup
  guide use BCM 17. That number is not valid for a board wired to another
  pin.
- `bounce_time` of `0.05` seconds is the example passed through to GPIO
  Zero. It is not a measured characteristic of the switch. Record the value
  used. Do not tune it during the measured repeats.

## Preparation

1. Power off is not required if the pin is free. If the operator is unsure
   which pin is free, stop and record **BLOCKED** instead of probing
   randomly.
2. Photograph or sketch the wiring for the evidence archive. Do not commit
   the photo if it is large; store the URI and a checksum.
3. From the repository root, with the project environment active, confirm
   the pin factory after the button is constructed (step 1 below).

## Execution

Save the following as a scratch file outside the repository, or run it with
`python -` and a here-document. Do not add it to the product source.

Replace `<BCM_PIN>` and keep `0.05` unless the execution states a different
agreed value before the first sample.

```bash
python - <<'PY'
import time
from pi.input.push_to_talk_button import PushToTalkButton
import gpiozero

pin = int("<BCM_PIN>")
bounce = 0.05

def pressed():
    print(f"pressed {time.monotonic():.6f}", flush=True)

def released():
    print(f"released {time.monotonic():.6f}", flush=True)

button = PushToTalkButton(pin, bounce, pressed, released)
print(f"pin_factory {type(gpiozero.Device.pin_factory).__name__}", flush=True)
print("ready", flush=True)
try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    button.close()
PY
```

Wait for `ready` before touching the button.

Practice, excluded from the counts below. Do this once, before cycle 1.
Label every callback from it `practice` in the notes.

- One physical action: press, hold about one second, release.
- Those callbacks are not part of the nine.

Measured set: 3 cycles. Each cycle has the same 3 physical actions, in
this order. A physical action is one press followed by its release. A
cycle is those three actions plus the idle wait that ends the cycle.

1. Action A. Press and hold about one second, then release. Wait one
   second. That wait is a pause, not another action.
2. Action B. Press and release once, quickly.
3. Action C. Press and release once, then do not touch the button for two
   seconds. Those two seconds are the idle interval of the cycle.

Do not add actions. Completing cycle 1, then cycle 2, then cycle 3
produces:

| Count | Value |
| --- | --- |
| Practice actions, excluded | 1 press and 1 release |
| Measured cycles | 3 |
| Physical actions in one measured cycle | 3 |
| Physical actions in the measured set | 9 |
| Expected `pressed` lines in the measured set | 9 |
| Expected `released` lines in the measured set | 9 |
| Idle intervals | 3, one at the end of each cycle |
| Callbacks during those idle intervals | 0 |
| Callbacks during the one-second pauses | 0 |

Stop the process with Ctrl+C after cycle 3. Confirm it printed nothing
further and the shell returned.

Count `pressed` and `released` lines in the transcript. Practice lines are
omitted from the nine. The operator's note of which lines are practice is
evidence. The timestamps are not a latency measurement. Edge latency stays
**NOT MEASURED** unless an external instrument is named.

## Observations and evidence

- Transcript of the script.
- Pin factory class name.
- A table with one row per physical action. Columns: cycle (`practice`,
  `1`, `2`, or `3`), action (`practice`, `A`, `B`, or `C`), expected
  `pressed` count (1), expected `released` count (1), observed counts.
- Totals for the measured rows only: 9 observed `pressed` lines and 9
  observed `released` lines.
- A count of lines that appeared during the three idle intervals and
  during the one-second pauses. The required count is zero.
- Any exception from GPIO Zero, copied in full.

## Metrics

| Metric | Unit | Rule |
| --- | --- | --- |
| Measured `pressed` lines | count | 9, practice excluded |
| Measured `released` lines | count | 9, practice excluded |
| Unsolicited callbacks in pauses and idle intervals | count | 0 |
| Edge latency | seconds | **NOT MEASURED** without an external instrument |

Spacing between the Python timestamps is recorded and is not an acceptance
limit. Debounce behavior is the absence of a burst for one mechanical
press at the chosen `bounce_time`. A numeric bounce specification is
**TO BE DEFINED** after these transcripts exist. Do not change `bounce_time`
to chase a burst inside this execution.

## Acceptance criteria

1. The measured table has 9 actions (3 cycles × 3 actions). Each of those
   rows has one observed `pressed` line and one observed `released` line.
   The measured totals are 9 and 9. The practice action is present in the
   notes and is not included in those totals.
2. The three two-second idle intervals and the one-second pauses produce
   no callback lines.
3. The process exits on Ctrl+C after `close`, without a traceback.
4. Polarity matches the adapter: the callback fires on the physical press,
   not on release only. If the names are swapped relative to the finger,
   the criterion fails.
5. Edge latency is reported as **NOT MEASURED** unless the instrument
   section of the execution names the instrument.

## Failure conditions

- Any measured total other than 9 `pressed` lines and 9 `released`
  lines, or any unsolicited line during a pause or an idle interval:
  **FAILED**.
- `GPIO busy`, permission denied, or no pin factory: **BLOCKED** if the
  baseline did not already include a working GPIO library; **FAILED** if
  the same pin and user worked in a previous execution of this case and
  the setup did not change.
- Editing the product to log GPIO: **FAILED** as a procedure deviation.

## Recovery and cleanup

Ctrl+C must run `button.close()`. If the process is killed another way,
reboot is not the first recovery. Run nothing else on that pin until
`gpioinfo` or a fresh attempt shows it is free, and record the recovery in
the execution. Do not leave the scratch process running.

## Limitations and exclusions

This case does not start audio capture, does not measure contact bounce in
milliseconds, and does not show that `PushToTalkController` saw the event.
Those are TC-PTT-001 and TC-PTT-002. GPIO Zero's `bounce_time` is used as
implemented; this case does not redefine it.
