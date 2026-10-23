# Raspberry Pi–PC audio interface

## Purpose

This interface carries a push-to-talk recording from the Raspberry Pi to a
replaceable audio handler on the PC, and brings the handler's result back.
Speech recognition no longer runs on the Raspberry Pi: the PC sends the audio
to a transcription API. This interface only moves the file. It does not
transcribe, interpret inventory commands, validate products or orchestrate
pending operations.

It extends the [text interface](pc-communication.md) with a second endpoint on
the same server. The protocol, the `TransportEnvelope`, the configuration and
the client error codes are the same. Why the WAV travels as a raw body is
recorded in
[ADR-0007](../decisions/0007-send-push-to-talk-audio-as-raw-wav-over-http.md).

```text
Raspberry Pi                                    PC
PushToTalk ── WAV ──► RecordingSender
                      └─► HttpInterpretationClient.interpret_audio
                              │  POST /api/v1/interpret-audio (audio/wav)
                              ▼
                          PC server ── ReceivedAudio ──► audio handler
                              ▲                          (stub today;
                              │                           transcription API +
                              └──── TransportEnvelope ◄── InterpretationService)
```

| Layer | Owner | Answers |
|---|---|---|
| `TransportEnvelope` | RaspberryPiPCAudioTransfer | Did the audio travel between Raspberry Pi and PC? |
| `ServiceResult` | Audio handler: transcription + InterpretationService | Could the audio be transcribed and interpreted? |
| `ContractPayload` | OperationContractValidation | Is the operation valid for the domain? |

## Quick start: local roundtrip

With the project installed (`python -m pip install -e ".[dev]"`), terminal 1
starts the PC server, which already serves both endpoints:

```bash
voicestock-pc-server
```

Terminal 2 sends one of the recorded fixtures:

```bash
voicestock-pi-client --audio tests/fixtures/speech_to_text/wav/basico/solo_agregar.wav
```

Expected output, exit code `0`. Until the transcription handler exists, the
stub reports what arrived:

```json
{
  "status": "success",
  "payload": {
    "status": "success",
    "payload": {
      "received_audio": {
        "size_bytes": 274476,
        "duration_seconds": 8.576,
        "sample_rate_hz": 16000,
        "channels": 1,
        "sample_width_bytes": 2
      }
    },
    "error": null
  },
  "error": null
}
```

`voicestock-pi-client --audio <file>` exits with `0` for a success envelope,
`1` for an error envelope and `2` for wrong arguments. The text form,
`voicestock-pi-client "texto"`, still works.

## From the Raspberry Pi

The PC server must listen on the network and the Raspberry Pi must point at
it, exactly as for text: see
[running on the local network](pc-communication.md#running-on-the-local-network).

```bash
# PC
VOICESTOCK_PC_HOST=0.0.0.0 VOICESTOCK_PC_PORT=8123 voicestock-pc-server

# Raspberry Pi
export VOICESTOCK_PC_URL=http://192.168.50.2:8123
export VOICESTOCK_PC_TIMEOUT=10
voicestock-pi-client --audio grabacion.wav
```

### Sending push-to-talk recordings

`voicestock-pi-ptt` sends every recording to the PC when `--send-to-pc` is
given, and prints the PC answer after the capture data. It needs the button
and the USB microphone described in the
[push-to-talk setup](../setup/push-to-talk.md):

```bash
voicestock-pi-ptt --pin 17 --bounce-time 0.05 \
  --input-device "USB Audio" --output-directory recordings --send-to-pc
```

The WAV files stay in `--output-directory`. Add `--delete-after-send` to
delete each one once it was sent, whatever the answer. Without `--send-to-pc`
the command only records, as before.

The send runs on the push-to-talk worker. While it waits for the answer, at
most `VOICESTOCK_PC_TIMEOUT` seconds, a new press is queued and handled
afterwards.

### Testing remotely over Tailscale

During development the Raspberry Pi is reached through a Tailscale node
shared from another tailnet. That share lets the PC open connections to the
Raspberry Pi but not the other way round. A reverse SSH tunnel opened from the
PC carries the Raspberry Pi's requests back:

```bash
# PC, terminal 1: server on the PC's Tailscale address
VOICESTOCK_PC_HOST=<pc-tailscale-ip> VOICESTOCK_PC_PORT=8123 voicestock-pc-server

# PC, terminal 2: port 8123 on the Raspberry Pi leads to the PC server
ssh -N -R 127.0.0.1:8123:<pc-tailscale-ip>:8123 <raspberry-ssh-alias>

# Raspberry Pi
VOICESTOCK_PC_URL=http://127.0.0.1:8123 voicestock-pi-client --audio grabacion.wav
```

On 22 October 2026 this setup sent the 8.6 s and 51 s fixtures from the
Raspberry Pi 3 in about 3.5 s each, most of it Python start-up on the Pi.

## Endpoint

```text
POST /api/v1/interpret-audio
Content-Type: audio/wav
<WAV file bytes>
```

### Request

- The body is the complete WAV file, unchanged. There is no JSON and no
  multipart form.
- `Content-Type` must be `audio/wav`. Parameters such as `; codecs=1` are
  ignored.
- The body must not be empty and must be at most `MAX_AUDIO_BYTES`, 4 MiB
  (4 194 304 bytes). Push-to-talk records PCM16 mono 16 kHz, 32 000 bytes per
  second, so its 60-second default is about 1.9 MB. The server stops reading as
  soon as the body exceeds the limit, with or without `Content-Length`.
- The body must be a WAV container that Python's `wave` module can read. The
  server reads its header but does not require a sample rate, channel count
  or duration: the transcription API decides what it accepts.

`WAV_MEDIA_TYPE` and `MAX_AUDIO_BYTES` live in `src/shared/communication`, so
both ends use the same values.

### Successful response

`200 OK` with a success `TransportEnvelope`. The payload is whatever the audio
handler returned, opaque to this interface. The stub returns the
`ServiceResult` shown in the [quick start](#quick-start-local-roundtrip). As
with text, the caller checks the outer `status` first and then the inner
`ServiceResult`.

### Error response

Errors are error `TransportEnvelope`s, as in the
[text interface](pc-communication.md#error-response).

## Raspberry Pi client

`HttpInterpretationClient` implements two protocols. Code that sends audio
depends on `AudioInterpretationClient`, not on HTTP:

```python
class AudioInterpretationClient(Protocol):
    def interpret_audio(self, wav_path: Path) -> TransportEnvelope: ...
```

```python
from pathlib import Path

from pi.communication import ClientSettings, HttpInterpretationClient

with HttpInterpretationClient(ClientSettings.from_environment()) as client:
    envelope = client.interpret_audio(Path("recordings/take.wav"))

if envelope.status == "success":
    service_result = envelope.payload
else:
    handle_communication_error(envelope.error.code)
```

What the client does and does not do:

- it reads the file and sends it unchanged; it does not check the format, the
  size or the duration, because the server decides;
- a file that cannot be read gives `audio_read_failure` and nothing is sent;
- it uses the same timeout, a single request and no retries, as `interpret`;
- it validates only the HTTP status, the encoding and the envelope shape,
  never the payload.

The timeout covers the whole exchange, including transcription and
interpretation on the PC. With the real handler, two API calls happen before
the answer: raise `VOICESTOCK_PC_TIMEOUT` if the default 10 seconds are not
enough.

### Push-to-talk consumer

`RecordingSender` connects push-to-talk to the client. It is passed as
`on_capture_completed` of `PushToTalkController`:

```python
from pi.push_to_talk import PushToTalkController, RecordingSender

sender = RecordingSender(client, on_sent=show_answer, delete_after_send=True)
controller = PushToTalkController(
    capture, on_capture_completed=sender, on_capture_error=show_capture_error
)
```

- It sends each recording once and calls `on_sent(result, envelope)` with the
  answer, success or error. A communication failure does not stop
  push-to-talk: the next press records and sends again.
- `delete_after_send` is required, so the file policy is always explicit.
  With `True` the WAV is deleted after the send, whatever the answer; with
  `False` it stays where `AudioCapture` published it.
- It does not read the payload or create pending operations. That is
  PendingOperationFlow's job.

## Error catalogue

Server codes come from the PC in an HTTP error response; client codes are
produced on the Raspberry Pi. `timeout`, `connection_failed`,
`unexpected_status`, `invalid_response_encoding` and `invalid_envelope` are
shared with text and described in the
[text error catalogue](pc-communication.md#communication-error-catalogue).

| Code | Side | HTTP | Cause |
|---|---|---|---|
| `unsupported_media_type` | Server | `415` | `Content-Type` is not `audio/wav`. |
| `audio_too_large` | Server | `413` | The body exceeds 4 MiB. |
| `empty_audio` | Server | `422` | The body is empty. |
| `invalid_audio` | Server | `422` | The body is not a readable WAV file. |
| `handler_failure` | Server | `500` | The audio handler raised an exception. |
| `serialization_failure` | Server | `500` | The audio handler returned a value that cannot be encoded as JSON. |
| `audio_read_failure` | Client | — | The WAV file does not exist or cannot be read; nothing was sent. |

### Reproducing each error

With the server running as in the [quick start](#quick-start-local-roundtrip):

```bash
# invalid_audio: a file that is not a WAV
voicestock-pi-client --audio README.md

# audio_read_failure: a file that does not exist
voicestock-pi-client --audio missing.wav

# audio_too_large: 5 MB of zeros
head -c 5000000 /dev/zero > /tmp/big.wav
voicestock-pi-client --audio /tmp/big.wav

# empty_audio
curl -s -X POST http://127.0.0.1:8000/api/v1/interpret-audio \
  -H "Content-Type: audio/wav" --data-binary @/dev/null

# unsupported_media_type
curl -s -X POST http://127.0.0.1:8000/api/v1/interpret-audio \
  -H "Content-Type: application/octet-stream" \
  --data-binary @tests/fixtures/speech_to_text/wav/basico/solo_agregar.wav
```

`handler_failure` and `serialization_failure` need a faulty handler and are
covered by `tests/pc/communication/test_audio_endpoint.py`.

## PC audio handler: connecting the transcription API

The server calls one function per valid request:

```python
AudioHandler = Callable[[ReceivedAudio], Any]

@dataclass(frozen=True)
class ReceivedAudio:
    wav: bytes                # the complete WAV file, as it arrived
    duration_seconds: float   # read from the WAV header
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int
```

`create_app(handler, audio_handler=...)` in `pc.communication` exposes
`/api/v1/interpret-audio` only when an audio handler is given. The PC entry
point, `src/pc/main.py`, passes the stub `describe_received_audio` today.
That is the only place to change. `pc.communication` and the Raspberry Pi stay
as they are.

The expected real handler transcribes `audio.wav` and returns the
`ServiceResult` of `InterpretationService.interpret` for that text. Then the
Raspberry Pi gets the same layers as for text. A sketch for `src/pc/main.py`,
where `transcribe` stands for the API call owned by SpeechToText:

```python
def create_pc_app(registry, provider_name, transcriber) -> FastAPI:
    service = InterpretationService(registry, provider_name)

    def interpret_audio(audio: ReceivedAudio) -> ServiceResult:
        try:
            text = transcriber.transcribe(audio.wav)
        except TranscriptionError as error:
            return ServiceResult.failure(ServiceErrorCode.PROVIDER_FAILURE, str(error))
        return service.interpret(text)

    return create_app(service.interpret, audio_handler=interpret_audio)
```

Rules for the handler:

- **Return, do not raise.** An exception becomes `handler_failure` with HTTP
  500, and the Raspberry Pi cannot tell why. Report expected failures, such
  as no API key, a timeout or an empty transcription, as a typed
  `ServiceResult` error.
- **Return a JSON-serializable value.** A `ServiceResult` or plain
  dictionaries are fine; anything else becomes `serialization_failure`.
- **Send `audio.wav` as it is.** It is already a WAV file. The Groq
  transcription endpoint receives it as a multipart file upload, as
  `scripts/benchmarks/groq_audio_pipeline_benchmark.py` does. Benchmark code
  must not be imported into `src/`.
- **Keep credentials and endpoints inside the handler's module**, as the
  [interpretation providers](interpretation-service.md) do. The transport
  knows nothing about them.
- **Mind the time budget.** The Raspberry Pi waits at most
  `VOICESTOCK_PC_TIMEOUT` seconds for transcription plus interpretation.

## Automated verification

```bash
pytest tests/pc/communication tests/pc/test_pc_main.py \
  tests/pi/communication tests/pi/push_to_talk/test_sender.py \
  tests/pi/test_pi_main.py tests/integration/test_pi_pc_audio_roundtrip.py
```

- `tests/pc/communication/test_audio.py`: reading WAV headers, other PCM
  formats accepted, and unreadable files rejected.
- `tests/pc/communication/test_audio_endpoint.py`: the endpoint through
  HTTPX's ASGI transport, including every server error, the 4 MiB boundary and
  a body without `Content-Length`.
- `tests/pc/test_pc_main.py`: the stub with a real fixture and a replaced
  handler.
- `tests/pi/communication/test_audio_client.py`: the client against a mocked
  transport.
- `tests/integration/test_pi_pc_audio_roundtrip.py`: the client against the
  real server on localhost sockets.
- `tests/pi/push_to_talk/test_sender.py`: `RecordingSender` alone and with
  the real `PushToTalkController`.
