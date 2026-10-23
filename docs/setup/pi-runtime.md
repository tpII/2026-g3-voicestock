# Integrated Raspberry Pi runtime

`voicestock-pi` is the process that runs capture, the PC client, the
operation cycle, and the operator page together. The cycle itself is
[the operation workflow](../architecture/pending-operation-flow.md). The
decision to own that cycle in one object is
[ADR-0008](../decisions/0008-use-a-single-raspberry-pi-operation-workflow.md).

The command is `pi.runtime:main`, registered in `pyproject.toml` as
`voicestock-pi`.

The older commands stay available for diagnosis. They do not share this
process:

| Command | Use |
| --- | --- |
| `voicestock-pi-client` | Send one text or one WAV and print the envelope. |
| `voicestock-pi-ptt` | Record from the button, and optionally upload, without the cycle or the page. See the [push-to-talk setup](push-to-talk.md). |
| `voicestock-pi-web` | Serve the page with no ports. `/health` answers, and the API returns `application_not_ready`. See the [web setup](pi-web.md). |

## What one process wires

`build_runtime` creates one `PendingOperationFlow` and connects it to:

- `AudioCapture` with `SoundDeviceBackend`;
- `PushToTalkController`, using the flow as `can_start_capture`,
  `on_capture_completed`, and `on_capture_error`;
- `PushToTalkButton` on the BCM pin given to the command;
- `HttpInterpretationClient` from `ClientSettings.from_environment()`;
- `OperationValidator` over `InMemoryProductResolver(load_catalog(...))`;
- `ProvisionalOperationExecutor`, unless another executor is passed to
  `build_runtime`;
- FastAPI from `create_app`, with the flow's query port, resolution port,
  and the flow itself as the status port.

Confirm through this command does not change inventory. The PC client still
talks to whatever `VOICESTOCK_PC_URL` points at. The current PC audio handler
is the stub described in the
[workflow](../architecture/pending-operation-flow.md#information-flow).

## Install

From the repository root, with the project environment active. The setup
scripts already install the project. If this checkout was installed before
`voicestock-pi` existed, install again so the command is registered:

```bash
pip install -e ".[dev]"
```

The button and the microphone use the same system packages as
[push-to-talk](push-to-talk.md). The page does not need Node.js. The catalog
file is a JSON list of products, the format `pi.operation_contract.load_catalog`
reads. Product identity follows
[ADR-0006](../decisions/0006-identify-products-by-unique-attribute-match.md).

## Run

`--pin`, `--bounce-time`, `--input-device`, `--output-directory`, and
`--catalog` are required. `--input-device` is a name query, not a PortAudio
index. `USB Audio` below is a placeholder; use a name from the capture
device list in the push-to-talk guide.

On the Raspberry Pi, with the PC server reachable on the Ethernet link:

```bash
mkdir -p recordings
VOICESTOCK_PC_URL=http://192.168.50.2:8000 \
  voicestock-pi \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "USB Audio" \
  --output-directory recordings \
  --catalog path/to/catalog.json
```

The process prints the page URL and waits until Ctrl+C. From the PC browser
the default page is `http://192.168.50.1:8000/`.

On a development machine that does not own `192.168.50.1`, bind localhost.
Do not run this web server and `voicestock-pc-server` on the same port of
the same machine:

```bash
VOICESTOCK_PC_URL=http://127.0.0.1:8000 \
VOICESTOCK_WEB_HOST=127.0.0.1 \
VOICESTOCK_WEB_PORT=8123 \
  voicestock-pi \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "USB Audio" \
  --output-directory recordings \
  --catalog path/to/catalog.json
```

Then open `http://127.0.0.1:8123/`.

### Arguments

| Argument | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--pin` | yes | | BCM GPIO pin of the button. |
| `--bounce-time` | yes | | Debounce time in seconds. |
| `--input-device` | yes | | Microphone name query. |
| `--output-directory` | yes | | Directory where WAV files are published. |
| `--catalog` | yes | | JSON product catalog. |
| `--max-duration` | no | `60` | Maximum recording length in seconds. |
| `--keep-recordings` | no | off | Keep each WAV after it is sent. Without this flag the file is deleted after the send. |

### Environment

These variables are the ones `WebServerSettings` and `ClientSettings` already
read. The runtime does not add others.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VOICESTOCK_WEB_HOST` | `192.168.50.1` | Address the operator page binds. |
| `VOICESTOCK_WEB_PORT` | `8000` | TCP port of the operator page. Integer from 1 to 65535. |
| `VOICESTOCK_PC_URL` | `http://127.0.0.1:8000` | Base URL of the PC interpretation server. |
| `VOICESTOCK_PC_TIMEOUT` | `10` | Client timeout in seconds. Finite and positive. |

## Lifecycle

1. Parse arguments and build the client, the catalog validator, the capture
   device, and the button.
2. `serve()` starts the push-to-talk worker, then blocks in the web server.
3. Ctrl+C is a normal stop. The process returns exit code `0`.
4. Shutdown closes, in order, the button, the push-to-talk controller, the
   flow, and the PC client. The flow waits for the current PC request to
   finish and then refuses new work. An in-progress recording is stopped and
   delivered by the controller before the worker exits.

`GET /health` on this process means the HTTP server is responding. It does
not mean the microphone, the button, the PC, or the catalog are healthy.
