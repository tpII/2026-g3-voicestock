# Raspberry Pi web server

How to start the operator web server and check that it answers. The page is a
placeholder. It does not show or resolve a pending operation.

Why this stack exists is
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).
The application ports the later API will call are in the
[flow contract](../research/pending-operation-web-flow-contract.md).

## What this command is

`voicestock-pi-web` starts FastAPI under Uvicorn so the page can be opened
before the orchestrator exists. It is a development and validation entry
point.

The production shape is still one Python process. This command does not
create a second service, a systemd unit, or a channel to the orchestrator.
How the web app and the future runtime share that process is not decided
here.

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

There is no HTTPS, no login, and no CORS. The page, its files, and the later
API are the same origin: `http://192.168.50.1:8000`.

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

`/` shows that VoiceStock Web is up. `/health` returns:

```json
{"status": "ok"}
```

That only means the HTTP server answered. It does not check the microphone,
the button, the PC, the inventory, or the FSM.

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

- The page that calls the API.
- Wiring this app into the orchestrator process, which is what supplies the ports.
- TLS, authentication, and a reverse proxy.
