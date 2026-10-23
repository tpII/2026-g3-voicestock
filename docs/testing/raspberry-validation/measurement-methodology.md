# Measurement methodology

Rules for every execution in this campaign. A case may add a metric. It may
not replace these rules with a single untimed impression.

No sample in this repository was collected under this methodology. Empty
tables stay empty until an execution record fills them.

## Sample size

| Kind of check | Warm-up | Measured runs | Why |
| --- | --- | --- | --- |
| Binary hardware fact (device listed, route present, one press detected) | 0 | 3 | One success can be a coincidence. Three is the smallest repeat this campaign accepts before calling the behavior stable. |
| Cheap timed command (`ping`, text HTTP, health HTTP) | 1, discarded | 10 | Ten samples support a median and a standard deviation without a long session. |
| Operator cycle (button, speech, confirm) | 1, discarded | 5 | Each cycle needs a person. Five is enough to see a stuck cycle and small enough to finish in one session. |

The warm-up run uses the same command as the measured runs. Its values are
stored and labeled `warmup`. They are excluded from the mean, median,
standard deviation, minimum, maximum, and any later percentile.

Do not report a 95th percentile unless the measured sample size is at least
20. The sizes above are not. Report minimum, maximum, median, and mean.
Report the sample standard deviation when there are at least five measured
duration samples and the duration is meaningful. For three binary repeats,
report the pass count only.

A later revision may raise the operator-cycle count. It must not lower it
for a **CLOSED_PASSED** claim of stability.

## Clocks

Measure a local duration with `time.monotonic()` in Python on the machine
that starts and finishes the interval. `time.monotonic()` is immune to a
step of the civil clock during the sample.

Do not use `date`, `time.time()`, or a log timestamp as the start or end of
a duration. Civil time is recorded once per execution so a person can find
the session. It is not subtracted.

Do not subtract a timestamp taken on the Raspberry Pi from a timestamp
taken on the PC. Those clocks are not synchronized. The following intervals
stay separate:

| Name | Where it is measured | What it is not |
| --- | --- | --- |
| User-observed latency | The operator's watch or a single video timeline, from a visible start cue to a visible end cue | Network RTT or API time |
| ICMP RTT | `ping` on one host, using that host's ICMP timer | HTTP duration |
| HTTP client duration | `time.monotonic()` on the Pi around one `interpret` or `interpret_audio` call, or around one `curl` of a Pi route | Processing time inside the PC handler |
| Server handling time | A log line on the PC around the handler only, using the PC monotonic clock | The client's observed duration |
| UI lag | On one machine, from the moment a fetched API body shows the new phase until the page shows it | Button-to-pending latency |

Button-to-pending latency, when a video or a stopwatch is used, includes
human reaction, audio capture, transfer, validation, and up to one 1000 ms
page poll. Report it as user-observed latency. If the API is polled from a
script on the Pi with `time.monotonic()`, that sample is an API observation
latency and must be labeled as such. Do not add the two labels together.

GPIO latency from the electrical edge to the Python callback is **NOT
MEASURED** with these clocks. The callback time includes scheduling inside
the process. Claim an edge latency only when the execution names an
external instrument (logic analyzer or oscilloscope), its model, and its
sample rate. If that instrument is absent, write **NOT MEASURED**. Do not
fill the cell with the callback spacing.

## Boundaries

- Audio hold: start the monotonic clock immediately before the action that
  begins the hold and stop it immediately after the action that ends the
  hold. For `AudioCapture`, that is the call to `start` returning, then the
  call to `stop`. Time spent inside `start` is stream initialization and
  is a different sample.
- Stream initialization: monotonic clock from the line before `start()`
  until `start()` returns without raising.
- HTTP: the clock wraps only the client call. DNS and TCP setup on that
  call stay inside the sample. Do not subtract them unless the case adds a
  separate instrumented sample.
- `ping` warm-up is one extra ICMP echo, not a connection warmup of HTTP.
- The first HTTP call after a process start is the warm-up when the table
  above requires one. Do not discard a later call and call it warm-up.

## Units and precision

- Store raw durations in seconds, printed with six digits after the decimal
  point (`f"{seconds:.6f}"`).
- Store sizes in bytes, as integers.
- Store rates in hertz, as integers, except a device's reported default
  sample rate, which is copied as PortAudio prints it.
- Store ICMP RTT as the tool prints it, and also convert each used sample
  to seconds in the raw table so the summary uses one unit.
- Summaries of duration are in milliseconds, rounded half away from zero to
  one decimal place for display. The raw file remains the source of truth.
- SHA-256 is 64 lowercase hexadecimal characters.

The six digits do not mean the measurement is accurate to one microsecond.
They preserve the float the clock returned. Instrumentation overhead is
discussed below.

## Summaries

For a measured set of durations that excludes warm-up, failures, and
timeouts:

- arithmetic mean;
- median (average of the two central values when the count is even);
- sample standard deviation with denominator `n - 1`, when `n >= 5`;
- minimum and maximum.

Show the count `n` beside every summary. Do not compute a summary from a
mixture of success times and timeouts.

## Failures and timeouts

- A failed functional trial counts in the success rate. It is omitted from
  duration statistics.
- A timeout is recorded as its own outcome. The time waited is recorded and
  is not used as the duration of a successful operation.
- Do not impute a missing sample.
- If a run is aborted because the operator stopped early, mark the remaining
  samples `not_collected`. They are not failures of the product. The
  execution cannot be **CLOSED_PASSED** while required samples are
  `not_collected`.
- An exception text is evidence. Truncate only by reference to an external
  log, and keep the exception type and message in the execution record.

Success rate is `successful measured trials / measured trials`, not
including warm-up. Report the fraction and the counts.

## Reproducibility

Record, every execution:

- git commit (`git rev-parse HEAD`) and `git status --porcelain` on the
  machine under test;
- `/proc/device-tree/model` when it exists;
- `/etc/os-release` (`PRETTY_NAME` and `VERSION_ID`);
- `uname -srvmo`;
- `python --version`;
- installed versions of `voicestock`, `gpiozero`, `sounddevice`, `httpx`,
  `fastapi`, and `uvicorn` (`python -m pip show <name>`);
- the GPIO pin factory actually constructed, when the case uses GPIO;
- the PortAudio device name and host API used, when the case uses audio;
- the network interface names used, taken from `nmcli` and `ip`, not assumed
  to be `wlan0` or `wlan1`;
- power-supply description the operator can see (mark **UNKNOWN** if it is
  not visible);
- `vcgencmd get_throttled` when the command exists, as a hex flag, without
  treating a value as a pass or fail unless a case says so.

A dirty worktree or a commit other than the specification revision is a
deviation. The run may continue only if the deviation is written down
before the measurements.

## Environment

The room is not controlled. Record anything the operator notices that can
move a result: a different USB port, a hub, a supply that is warm, another
process using the microphone, or a second Wi-Fi network with the same SSID.
Do not estimate a temperature if no thermometer was read. Write **NOT
MEASURED**.

Commands that depend on the OS, an interface name, a device name, a
privilege, or a BCM number must name that dependency in the execution
record. The examples in the cases (`17`, `wlan0`, `USB Audio`) are
placeholders until the baseline replaces them.

## Uncertainty and overhead

- A Python `time.monotonic()` sample around a short call includes
  interpreter overhead. Differences below 1 ms are reported but are not
  interpreted as a product change.
- `ping` RTT includes the remote ICMP stack. It is not the VoiceStock
  processing time.
- The web poll adds up to 1000 ms, and 2000 ms after a failed poll
  (`RETRY_INTERVAL_MS`), before the page can change. A user-observed UI
  delay inside one poll interval is consistent with the current page.
- SSH or a serial console adds its own delay. Do not time a keystroke
  through SSH and call it GPIO latency.
- Checksums prove file identity. They do not prove that the microphone
  heard the intended words.

## Raw data and summaries

Each execution keeps a raw table of every sample and a summary computed
from that table by the rules above. If a summary and the raw table
disagree, the raw table wins and the summary is corrected. The project
bitácora receives one entry at the end of the testing day and links to
that day's execution records. It does not gain a section per test, and it
does not replace the raw tables.

## Metrics by area

### GPIO

Record press and release callback counts for the scripted sequence, missed
pairs, and extra callbacks. Debounce is the `bounce_time` passed to
`PushToTalkButton`, which passes it to GPIO Zero. This campaign does not
define a new debounce algorithm. Latency is **NOT MEASURED** without an
external instrument.

### Audio

Record requested hold (monotonic), header duration (`nframes / sample_rate`),
file size, format fields, stream initialization time, and exceptions.
A discontinuity check by ear or by opening the file is an observation.
There is no numeric discontinuity limit. The overflow flag is not available
from the current backend.

### Network

Record ICMP RTT, replies lost, the interface selected by `ip route get`,
whether a public IP answers from the PC and from the Pi, and whether the
profiles return after reboot. Isolation fails closed: if the PC cannot
reach the public IP either, the Pi result is **BLOCKED**, not a pass.

### HTTP

Record client duration, HTTP status, envelope `status`, and the error code
when the call is a failure trial. For a WAV, record local size and SHA-256
against the size the server reports. Transfer duration is the client
duration and stays next to the byte size. Do not divide them into a
throughput gate; a throughput limit is **TO BE DEFINED**.

### Web

Record time to first `/health` response, time to `system-status`, the phase
string, and whether a confirm or cancel response matches the
[resolution map](../../interfaces/pending-operation-web-api.md). State
synchronization is "the page shows the same `operation_id` and
`confirmation_message` as the API", not a millisecond gate.

### Simulated end-to-end

Record user-observed button-to-pending latency separately from per-stage
samples the operator can actually instrument. Stages without a timestamp in
the product are **NOT MEASURED** rather than estimated. Record the success
count over the five measured cycles, whether a second press during
`wait_confirmation` leaves the same `operation_id` in place, and whether
idle is reached after confirm and after cancel.

Error recovery in the simulated cycle uses the trials in
[TC-FLOW-001](test-cases/TC-FLOW-001.md): stub rejection and PC unreachable.
Those are flow trials, not speech-recognition trials.
