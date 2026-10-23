# TC-PTT-002 — Maximum duration and ignored extra presses

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that a hold longer than `--max-duration` stops the WAV with
`MAX_DURATION`, that another press during the recording does not start a
second capture, and that a new capture starts only after release.

## Test level and type

Level: integration.

Type: functional, aimed at the controller races. The short max duration is
a test setting, not the product default.

## Requirements and ClickUp traceability

- ClickUp: [PushToTalk-06](https://app.clickup.com/t/86e3euv9u).
- Requirement: `PushToTalkController` arms `max_duration`, publishes the
  partial recording, and enters `WAITING_FOR_RELEASE` until the button is
  released (`src/pi/push_to_talk/controller.py`).

## Source modules and documentation

- `pi.push_to_talk.controller`.
- [TC-PTT-001](TC-PTT-001.md).

## Preconditions and dependencies

- [TC-PTT-001](TC-PTT-001.md) is not **FAILED** or **BLOCKED**.
- Same pin and microphone query.

## Required hardware and software

- Same as TC-PTT-001.
- A stopwatch or the Pi monotonic clock visible in a second terminal is
  optional. The termination reason is the functional result. The duration
  error against 2 seconds is recorded and its allowed error is
  **TO BE DEFINED**.

## Preparation

```bash
mkdir -p recordings/tc-ptt-002
```

## Execution

```bash
voicestock-pi-ptt \
  --pin <BCM_PIN> \
  --bounce-time 0.05 \
  --input-device "<QUERY>" \
  --output-directory recordings/tc-ptt-002 \
  --max-duration 2
```

Measured cycles (three). One practice cycle may precede them and must be
labeled `practice`.

1. Press and hold. Do not release when the first capture line appears.
2. While still holding, press harder or click again if the button allows a
   second mechanical event. If the button cannot generate a second event
   while held, record "second press not mechanically possible" and skip
   criterion 3 for that cycle. Do not fail the button for being a simple
   momentary switch.
3. Keep holding until a capture is printed. Note the termination reason.
4. Only then release.
5. Press and release normally. A new capture must be printed with
   `RELEASED`.

Ctrl+C after the three cycles.

Inspect header durations with the same `wave` loop as TC-AUD-002.

## Observations and evidence

- Transcript showing, per cycle, one `MAX_DURATION` file and one later
  `RELEASED` file.
- Header durations of the `MAX_DURATION` files.
- Operator note on whether a second mechanical press was possible.

## Metrics

| Metric | Rule |
| --- | --- |
| Header duration of the max-duration file | Recorded versus 2 seconds. Gate **TO BE DEFINED**. |
| Extra WAV files per hold | Must be one file for the forced stop, not two, before release |

The 2 second value is the argument under test. It is not a campaign-wide
recording limit. TC-PTT-001 uses 60 seconds, which is the code default.

## Acceptance criteria

1. Each measured long hold prints exactly one capture with
   `Termination: MAX_DURATION` before the finger releases.
2. No second WAV appears while the button stays down.
3. If a second mechanical press was possible and was performed, it still
   does not create a second file before release.
4. After release, the next press-and-release prints `Termination: RELEASED`.
5. Format of both files matches the 16 kHz mono 16-bit contract.

## Failure conditions

- The long hold never stops and the operator has waited well past 2 seconds
  plus the stream start: **FAILED**. "Well past" is the operator's safety
  stop at 10 seconds of holding. Ten seconds is a test abort, not a product
  budget. Abort, keep the transcript, and fail the cycle.
- A second file appears before release: **FAILED**.
- The cycle after release does not record: **FAILED**.

## Recovery and cleanup

Ctrl+C. Archive WAV files outside git. Restore later cases to
`--max-duration 60` or to the runtime default. This case must not leave a
shell alias that forces 2 seconds.

## Limitations and exclusions

The controller's queue drops a press that arrives while not `IDLE`. This
procedure observes that from the files, not from an internal trace. There
is no product log line for an ignored press. Absence of a second file is
the observation. This case does not involve `PendingOperationFlow`; a press
ignored because a pending operation exists is TC-FLOW-001.
