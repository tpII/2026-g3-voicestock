# ADR-0007: Send push-to-talk audio to the PC as a raw WAV body over HTTP

## Status

Accepted — 22 October 2026. The PC server, the Raspberry Pi client and the
push-to-talk connection belong to
[RaspberryPiPCAudioTransfer-02](https://app.clickup.com/t/1dfdcycurmj),
[-03](https://app.clickup.com/t/1dfdcycurmk) and
[-04](https://app.clickup.com/t/1dfdcycurmm).

## Context

Speech recognition no longer runs on the Raspberry Pi: local processing on the
Pi 3 was too slow, and the team moved transcription to an API called from the
PC. That changes what crosses the local network. Instead of recognized text,
the Raspberry Pi must send the recording produced by PushToTalk, and the PC
must answer with a structured result.

The recording is fixed by the
[push-to-talk capture interface](../interfaces/push-to-talk-capture.md): a WAV
file with PCM16, mono, 16 kHz audio, at most 60 seconds by default. That is
32 000 bytes per second, so a full recording is about 1.9 MB.

[ADR-0001](0001-use-http-json-for-pi-pc-communication.md) already chose HTTP
request/response with a `TransportEnvelope` answer for the text exchange. The
constraints that led there still hold: the Raspberry Pi has no Internet on the
isolated network, the transport must not depend on a concrete provider, and
communication failures must stay distinguishable from service and domain
failures.

Calling the transcription API and passing its text to InterpretationService
belong to another team member. This decision only covers how the audio reaches
the PC and where that code plugs in.

## Decision

Send the WAV file **as the raw body of an HTTP `POST`** and keep the
`TransportEnvelope` answer of ADR-0001.

```text
POST /api/v1/interpret-audio
Content-Type: audio/wav
<WAV file bytes>
```

- **One request per recording**, sent after the button is released. There is
  no streaming while the user speaks.
- **Body limit: 4 MiB**, about two minutes of PCM16 mono 16 kHz audio. It
  covers the 60-second default with margin and stops a wrong file from
  filling the PC's memory. The limit and the media type are constants in
  `src/shared/communication`, used by both ends.
- **The transport validates only the container:** the media type, a non-empty
  body within the limit, and a WAV file that Python's standard `wave` module
  can read. It does not check audio quality, language, sample rate or content:
  the transcription API decides what it can process.
- **The answer is the same `TransportEnvelope`** as for text, with an opaque
  payload. Clients check the outer status first and then the payload, exactly
  as for `/api/v1/interpret`.
- **The PC server invokes a replaceable audio handler**, kept apart from
  `pc.communication` exactly like the text handler. It receives the WAV bytes
  and the metadata read from the header. Until the transcription integration
  exists, a stub answers with that metadata. The real handler is expected to
  transcribe the audio and return the `ServiceResult` of
  `InterpretationService.interpret(text)`, but the transport does not depend on
  that.
- **The text endpoint stays.** `POST /api/v1/interpret` keeps working for
  manual tests and for any flow that already has text.

## Alternatives considered

- **`multipart/form-data`:** rejected. FastAPI needs the extra
  `python-multipart` dependency to parse it, and boundaries and form fields add
  parsing and error cases for a request that carries a single file and no
  other field.
- **JSON with the audio in base64:** rejected. Base64 makes a 1.9 MB recording
  about 2.6 MB on the network and in memory, the Raspberry Pi must encode it,
  and the PC must decode it before the API call.
- **Streaming while recording (chunked HTTP or WebSocket):** rejected for now.
  The transcription API receives a complete file, so streaming would not
  shorten the wait, and it needs a long-lived channel that ADR-0001 already
  avoided.
- **Copying the file with SSH or SCP:** rejected. It needs credentials on the
  Raspberry Pi, has no structured answer and was only used as benchmark
  tooling (`scripts/integration`).

## Consequences

### Positive

- No new dependency on either side: `httpx` sends bytes, FastAPI reads the
  stream, and the standard library reads the WAV header.
- The network carries the file at its real size.
- Clients and callers keep one envelope and one error catalogue for text and
  audio.
- The transcription integration is one handler on the PC; neither the Raspberry
  Pi nor `pc.communication` changes when it arrives.

### Negative

- The request has no room for extra fields. If metadata becomes necessary, it
  must travel in headers or the endpoint must get a new version.
- The answer takes the time of upload, transcription and interpretation. The
  Raspberry Pi timeout must leave room for both API calls.
- The endpoint has no authentication, as with text. It is only acceptable on
  the isolated MVP network.

### Follow-up

- [RaspberryPiPCAudioTransfer-02](https://app.clickup.com/t/1dfdcycurmj)
  implements the endpoint, the limit, the WAV check and the stub handler.
- [RaspberryPiPCAudioTransfer-03](https://app.clickup.com/t/1dfdcycurmk)
  implements the client with the same error codes as the text client.
- [RaspberryPiPCAudioTransfer-04](https://app.clickup.com/t/1dfdcycurmm)
  sends each push-to-talk recording to the PC.
- [RaspberryPiPCAudioTransfer-05](https://app.clickup.com/t/1dfdcycurmn)
  documents the interface and how to connect the transcription API.
- The status of [ADR-0005](0005-use-whisper-small-q5-for-offline-stt.md) (STT
  on the Raspberry Pi) belongs to the SpeechToText owner; this ADR does not
  change it.
