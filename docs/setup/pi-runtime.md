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
- `OperationValidator` over `OpeningProductResolver`, which opens the Pi
  SQLite database on the audio-processing thread and delegates to
  `SqliteProductResolver`;
- `OpeningSnapshotReader` for `GET /api/v1/catalog`, which opens that same
  file on the HTTP thread;
- `ProvisionalOperationExecutor`, unless another executor is passed to
  `build_runtime`;
- FastAPI from `create_app`, with the flow's query port, resolution port,
  the flow itself as the status port, and the snapshot reader.

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
[push-to-talk](push-to-talk.md). A headset that cannot open 16000 Hz on the
raw ALSA device needs an explicit plug profile before `--input-device` will
accept it. The Logitech G435 profile used in validation is the
[ALSA microphone profile](alsa-microphone.md). Other microphones are not
routed through that profile. The page does not need Node.js. Product identity
follows
[ADR-0006](../decisions/0006-identify-products-by-unique-attribute-match.md)
and comes only from the persistent catalog
([product catalog](../interfaces/product-catalog.md)).

Prepare that database once, before starting the runtime. The command applies
migrations, loads the catalog seed and initializes stock. It is idempotent.
Stop `voicestock-pi` first if it is already running, because one process owns
writes to the file:

```bash
voicestock-pi-database init
```

The file is `~/.local/share/voicestock/voicestock.sqlite3`, or
`$XDG_DATA_HOME/voicestock/voicestock.sqlite3`. `VOICESTOCK_DATABASE` selects
another persistent path. `voicestock-pi` and `voicestock-pi-database` use
that same path. The runtime does not load the seed, does not reset stock and
does not read a JSON catalog. If the file has no active products, startup
prints the error and exits `1` before opening the microphone or the GPIO pin.
`voicestock-pi-database status` shows what the file holds
([inventory stock](../interfaces/inventory-stock.md#preparing-the-database)).

## Run

`--pin`, `--bounce-time`, `--input-device` and `--output-directory` are
required. `--input-device` is a name query, not a PortAudio
index. `USB Audio` below is a placeholder; use a name from the capture
device list in the push-to-talk guide.

On the Raspberry Pi the PC server has to be reachable on the VoiceStock Wi-Fi
cell. That cell is the
[local network setup](local-network.md). `192.168.50.2` is the PC address
defined there. Port `8000` in the example is the PC server default, not a
second network setting:

```bash
mkdir -p recordings
VOICESTOCK_PC_URL=http://192.168.50.2:8000 \
  voicestock-pi \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "USB Audio" \
  --output-directory recordings
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
  --output-directory recordings
```

Then open `http://127.0.0.1:8123/`. The catalog of this process is:

```bash
curl -D - http://127.0.0.1:8123/api/v1/catalog
curl -D - -H 'If-None-Match: "<revision>"' http://127.0.0.1:8123/api/v1/catalog
```

Replace `<revision>` with the `ETag` from the first response, including the
quotes. A match answers `304` with an empty body. `Cache-Control` is
`no-store` on both. On the Raspberry Pi the same request uses
`http://192.168.50.1:8000/api/v1/catalog`.

### Arguments

| Argument | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--pin` | yes | | BCM GPIO pin of the button. |
| `--bounce-time` | yes | | Debounce time in seconds. |
| `--input-device` | yes | | Microphone name query. |
| `--output-directory` | yes | | Directory where WAV files are published. |
| `--max-duration` | no | `60` | Maximum recording length in seconds. |
| `--keep-recordings` | no | off | Keep each WAV after it is sent. Without this flag the file is deleted after the send. |

### Environment

These variables are the ones `WebServerSettings`, `ClientSettings` and
`default_database_path` already read.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VOICESTOCK_DATABASE` | `~/.local/share/voicestock/voicestock.sqlite3` | SQLite file shared with `voicestock-pi-database`. Not a temporary path. |
| `VOICESTOCK_WEB_HOST` | `192.168.50.1` | Address the operator page binds. |
| `VOICESTOCK_WEB_PORT` | `8000` | TCP port of the operator page. Integer from 1 to 65535. |
| `VOICESTOCK_PC_URL` | `http://127.0.0.1:8000` | Base URL of the PC interpretation server. |
| `VOICESTOCK_PC_TIMEOUT` | `10` | Client timeout in seconds. Finite and positive. |

## Lifecycle

1. Parse arguments.
2. Resolve the database path, apply pending migrations and require at least
   one active product. That connection is closed before anything else starts.
   A missing catalog, a volatile path or a SQLite error exits `1` and does
   not open the microphone, the GPIO pin or the PC client.
3. Build the client, the SQLite-backed validator, the snapshot reader, the
   capture device and the button.
4. `serve()` starts the push-to-talk worker, then blocks in the web server.
5. Ctrl+C is a normal stop. The process returns exit code `0`.
6. Shutdown closes, in order, the button, the push-to-talk controller, the
   flow, and the PC client. The flow waits for the current PC request to
   finish and then refuses new work. An in-progress recording is stopped and
   delivered by the controller before the worker exits.

Catalog connections are not held across those steps. Product resolution and
`GET /api/v1/catalog` each open a connection on the thread that performs the
work and close it when the call returns, including when the call raises.
`check_same_thread` stays enabled. One connection is not shared between the
startup thread, the audio worker and the HTTP server.

`GET /health` on this process means the HTTP server is responding. It does
not mean the microphone, the button, the PC, or the catalog are healthy.

The PC downloads this catalog with `GET /api/v1/catalog` before each Groq
interpretation. It does not open the database. `InMemoryProductResolver`
remains for isolated tests and is not what `voicestock-pi` uses.
