# TC-COM-002 — WAV transfer to the PC

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that a WAV produced on the Pi is posted to
`POST /api/v1/interpret-audio` and that the current audio stub reports the
same size and PCM header fields.

## Test level and type

Level: integration.

Type: functional and measurement.

## Requirements and ClickUp traceability

- ClickUp: [RaspberryPiPCCommunication-05](https://app.clickup.com/t/86e3ev0ux).
- Requirement: raw WAV body, `Content-Type: audio/wav`, as in
  [ADR-0007](../../../decisions/0007-send-push-to-talk-audio-as-raw-wav-over-http.md)
  and [audio interface](../../../interfaces/pc-audio-communication.md).

## Source modules and documentation

- `pi.communication.client.HttpInterpretationClient.interpret_audio`.
- `pc.communication.audio.read_wav`.
- `pc.main.describe_received_audio`.
- The in-process test
  `tests/integration/test_pi_pc_audio_roundtrip.py` documents the stub
  shape. It is not evidence for this case.

## Preconditions and dependencies

- [TC-COM-001](TC-COM-001.md) showed the server is reachable with the text
  client.
- [TC-AUD-002](TC-AUD-002.md) or [TC-PTT-001](TC-PTT-001.md) produced at
  least one WAV whose checksum is known. Prefer a file from TC-PTT-001 so
  the bytes came from the button path. Record which execution owns the
  file.
- The file is at most `MAX_AUDIO_BYTES` (4 MiB). A one-minute 16 kHz mono
  16-bit file is about 1.9 MB and fits. Do not use a longer file to force
  the 413 path in this case.

## Required hardware and software

- Same bind as TC-COM-001: PC server on `192.168.50.2:8000` using the
  default audio handler. Do not start the contract fixture.
- The WAV on the Pi filesystem.

## Preparation

```bash
sha256sum <WAV_PATH>
python - <<'PY'
import wave
path = "<WAV_PATH>"
with wave.open(path, "rb") as wav:
    frames = wav.getnframes()
    rate = wav.getframerate()
    print(rate, wav.getnchannels(), wav.getsampwidth(), frames, frames / rate)
import os
print(os.path.getsize(path))
PY
```

Start the PC server as in TC-COM-001.

## Execution

One warm-up upload, then five measured uploads of the same file. Recompute
nothing on the PC by trusting a shared clock. Compare fields inside the
JSON the Pi prints.

```bash
python - <<'PY'
import os
import time
import subprocess
os.environ["VOICESTOCK_PC_URL"] = "http://192.168.50.2:8000"
os.environ["VOICESTOCK_PC_TIMEOUT"] = "10"
path = "<WAV_PATH>"
for index in range(1, 6):
    t0 = time.monotonic()
    completed = subprocess.run(
        ["voicestock-pi-client", "--audio", path],
        check=False,
        capture_output=True,
        text=True,
    )
    t1 = time.monotonic()
    print(f"sample {index} exit {completed.returncode} duration {t1 - t0:.6f}")
    print(completed.stdout)
    print(completed.stderr)
PY
```

Exit 0 means the envelope status is `success`. The service payload must
contain `received_audio.size_bytes`, `duration_seconds`,
`sample_rate_hz`, `channels`, and `sample_width_bytes`.

After the uploads, confirm the local file's SHA-256 is unchanged.

## Observations and evidence

- Local size, header duration, checksum before and after.
- Five response bodies and client durations.
- Byte size next to each duration. Throughput is not gated.

## Metrics

| Metric | Limit |
| --- | --- |
| `size_bytes` versus local size | Must be equal |
| `sample_rate_hz`, `channels`, `sample_width_bytes` | 16000, 1, 2 for a VoiceStock WAV |
| `duration_seconds` versus `frames / rate` | Equal within the JSON number the server sends. Record both. A mismatch fails. |
| Client duration | Recorded. Budget **TO BE DEFINED**. |
| SHA-256 after the run | Must match the hash from preparation |

The server computes duration as `frames / sample_rate` from the header. It
does not require 16 kHz. This case still requires 16 kHz because the file
under test is a VoiceStock capture.

## Acceptance criteria

1. Five measured calls exit 0.
2. Each `received_audio.size_bytes` equals the local file size.
3. Each response reports 16000 Hz, 1 channel, and sample width 2.
4. Each reported duration matches the header duration recorded in
   preparation. Write both numbers. They are the same quantity computed
   from the same header on two machines; they are not a clock comparison.
5. The local checksum does not change.
6. The response is the stub object, not a `ContractPayload`. A contract
   body means the wrong server is running and the case fails as a
   deviation. It is not a bonus pass.

## Failure conditions

- Non-zero exit or a client error code: **FAILED**.
- Size or format mismatch: **FAILED**.
- File larger than 4 MiB used by mistake: stop, mark the sample invalid,
  and do not treat HTTP 413 as the success path of this case.

## Recovery and cleanup

Stop the PC server. Leave the WAV in the external archive.

## Limitations and exclusions

A matching stub description proves the bytes arrived and the header was
readable. It does not prove a pending operation will be created. The Pi
rejects this payload as a contract. That rejection is exercised in
TC-FLOW-001, not counted as success here.
Speech inside the file is not evaluated.
