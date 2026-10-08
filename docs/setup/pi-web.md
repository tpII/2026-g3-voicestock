# Raspberry Pi web server

How to start the operator web server and check that it answers. `/` is the
pending-operation page. What it does with each HTTP result is the
[pending operation page](../interfaces/pending-operation-web-ui.md).

Why this stack exists is
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).
The boundary with `PendingOperationFlow` is the
[flow contract](../research/pending-operation-web-flow-contract.md). The HTTP
map is the
[pending-operation web API](../interfaces/pending-operation-web-api.md).

## What this command is

`voicestock-pi-web` starts FastAPI under Uvicorn so the page can be opened
before the orchestrator exists. It is a development and validation entry
point.

The production shape is still one Python process. This command does not
create a second service, a systemd unit, or a channel to the orchestrator.
How the web app and the future runtime share that process is still open.
That list is [Still open](../research/pending-operation-web-flow-contract.md#still-open)
in the flow contract.

## Network

The browser runs on the PC. The server runs on the Raspberry Pi. They meet
on the Ethernet link from the
[Ethernet setup guide](local-network.md):

```text
Raspberry Pi  192.168.50.1
        |
     Ethernet
        |
PC            192.168.50.2
        |
      Wi-Fi
        |
     Internet
```

The web server binds to `192.168.50.1` port `8000` unless the environment
overrides it. The PC interpretation server also defaults to port `8000`, on
the PC. They do not share a machine. On one computer, run only one of them
on `8000`, or set `VOICESTOCK_WEB_PORT` / `VOICESTOCK_PC_PORT`.

The page, its files, and the API are the same origin:
`http://192.168.50.1:8000`. This increment has no HTTPS, no login, and no
CORS. Those limits are
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).

## Install

From the repository root, with the project virtualenv active. If this
checkout was installed before `voicestock-pi-web` existed, install again so
the command is registered:

```bash
pip install -e ".[dev]"
```

The setup scripts do that install. FastAPI and Uvicorn are already project
dependencies. The page does not use a CDN, npm, or Node.js.

## Run on the Raspberry Pi

The Ethernet address has to be configured first. Then:

```bash
voicestock-pi-web
```

From the PC browser:

```text
http://192.168.50.1:8000/
http://192.168.50.1:8000/health
```

`/` is the operator page. `GET /health` returns:

```json
{"status": "ok"}
```

That only means the HTTP server is alive and can respond. It does not mean
that:

- `PendingOperationFlow` is ready;
- a pending operation exists;
- the microphone works;
- GPIO works;
- the PC is reachable;
- inventory works.

`/health` is not a readiness check. Do not extend it into one.

`/static/styles.css` and `/static/app.js` are served by the same process.

`voicestock-pi-web` does not receive the pending-operation ports. `/health`
stays `200`. The API then answers `503` with `application_not_ready` until a
later runtime passes those ports into `create_app`. The contract is the
[pending-operation web API](../interfaces/pending-operation-web-api.md).

```text
GET  /api/v1/pending-operation
POST /api/v1/pending-operation/{operation_id}/confirm
POST /api/v1/pending-operation/{operation_id}/cancel
```

## Run on a development machine

The default host is the Pi address. A laptop usually does not have
`192.168.50.1`, so bind localhost:

```bash
VOICESTOCK_WEB_HOST=127.0.0.1 voicestock-pi-web
```

Optional port:

```bash
VOICESTOCK_WEB_HOST=127.0.0.1 VOICESTOCK_WEB_PORT=8123 voicestock-pi-web
```

Then open `http://127.0.0.1:8123/` and `http://127.0.0.1:8123/health`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `VOICESTOCK_WEB_HOST` | `192.168.50.1` | Interface address to bind. |
| `VOICESTOCK_WEB_PORT` | `8000` | TCP port. Must be an integer from 1 to 65535. |

## What is not here yet

`voicestock-pi-web` does not start `PendingOperationFlow`, and confirm does
not update inventory. The open list, including the single-process lifecycle,
the real executor, and durable idempotency, is
[Still open](../research/pending-operation-web-flow-contract.md#still-open).
