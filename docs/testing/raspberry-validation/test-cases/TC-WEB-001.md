# TC-WEB-001 — Raspberry Pi web server

- Status: DESIGNED
- Executions: none
- Procedure version: 1

## Objective

Show that the Pi serves `/health` and the operator page, that
`voicestock-pi-web` reports the application as not ready, and that
`voicestock-pi` reports `idle` before any button press.

## Test level and type

Level: software component on the Raspberry Pi, observed over the cell from
the PC.

Type: functional and measurement of the HTTP samples only.

## Requirements and ClickUp traceability

- ClickUp: [PendingOperationWeb-07](https://app.clickup.com/t/86e3eve7j).
- Requirement: the page and `/health` described in
  [web setup](../../../setup/pi-web.md) and the idle phase described in
  [the workflow](../../../architecture/pending-operation-flow.md).

## Source modules and documentation

- `pi.web.app` (`GET /health`, `GET /`).
- `pi.web.server` (`voicestock-pi-web`).
- `pi.runtime` (`voicestock-pi`).
- `pi.web.api` (`GET /api/v1/system-status`).
- [Pending-operation API](../../../interfaces/pending-operation-web-api.md).

## Preconditions and dependencies

- [TC-NET-001](TC-NET-001.md) so `192.168.50.1` exists on the Pi. The PC
  browser checks also need [TC-NET-002](TC-NET-002.md).
- Port 8000 on `192.168.50.1` is free. The PC server uses port 8000 on
  `192.168.50.2`. Those are different addresses. Do not run the PC server
  on the Pi.
- A catalog file is required to start `voicestock-pi`. Use
  [../fixtures/campaign-catalog.json](../fixtures/campaign-catalog.json).
- The microphone query and BCM pin are required by the command even for the
  idle check. They come from TC-AUD-001 and TC-GPIO-001. Do not press the
  button in this case.

## Required hardware and software

- Pi on the cell, project environment, `curl` on the Pi and on the PC.
- A browser on the PC for the page check.

## Preparation

Copy the catalog to the Pi checkout if it is not already there. Record its
SHA-256. Create an empty output directory:

```bash
mkdir -p recordings/tc-web-001
```

## Execution

Trial A, page without the cycle. On the Pi:

```bash
VOICESTOCK_WEB_HOST=192.168.50.1 VOICESTOCK_WEB_PORT=8000 voicestock-pi-web
```

The defaults are already that host and port when the address exists. Setting
them makes the execution explicit. From the Pi, ten measured requests after
one warm-up:

```bash
curl -sS -D - http://192.168.50.1:8000/health
curl -sS -D - http://192.168.50.1:8000/api/v1/system-status
curl -sS -o /dev/null -w "%{http_code}\n" http://192.168.50.1:8000/
```

Wrap the ten `/health` calls with `time.monotonic()` the same way as
TC-COM-001. Expect `/health` body `{"status":"ok"}` and HTTP 200.
Expect `/api/v1/system-status` HTTP 503 and JSON code
`application_not_ready`. Expect `/` HTTP 200 and HTML that contains
`id="confirm-button"`.

From the PC browser open `http://192.168.50.1:8000/`. The page is allowed
to show the not-ready state. Record what it shows. Do not treat a blank
pending card as a pending operation.

Stop `voicestock-pi-web`.

Trial B, integrated process, idle only. On the Pi:

```bash
VOICESTOCK_PC_URL=http://192.168.50.2:8000 \
VOICESTOCK_WEB_HOST=192.168.50.1 \
VOICESTOCK_WEB_PORT=8000 \
  voicestock-pi \
  --pin <BCM_PIN> \
  --bounce-time 0.05 \
  --input-device "<QUERY>" \
  --output-directory recordings/tc-web-001 \
  --catalog <CATALOG_PATH> \
  --keep-recordings
```

The PC URL is set so a later accidental press does not use the loopback
default. The PC server may be stopped. Do not press the button.

```bash
curl -sS http://192.168.50.1:8000/health
curl -sS http://192.168.50.1:8000/api/v1/system-status
curl -sS -D - -o /dev/null http://192.168.50.1:8000/api/v1/pending-operation
```

Expect health 200, `phase` `idle`, `headline` `Listo para escuchar`,
`detail` `Presioná el botón para hablar`, `operator_message` null,
`pending_operation` null, and `pending-operation` HTTP 204.

Repeat the status read three times. From the PC browser, load the page and
record the idle headline. Then Ctrl+C the Pi process and confirm the
process exits. The runtime treats Ctrl+C as exit code 0.

## Observations and evidence

- Response headers and bodies.
- A short note of the browser headline. A screenshot is optional and stays
  outside git if it is stored.
- Durations for the ten health reads.

## Metrics

| Metric | Limit |
| --- | --- |
| `/health` client duration on the Pi | Recorded. Budget **TO BE DEFINED**. |
| Status code and phase strings | Exact match |

UI lag is not measured here because the phase does not change.

## Acceptance criteria

1. Trial A: `/health` is 200 with `status` `ok` for all ten measured reads.
2. Trial A: `system-status` is 503 with `application_not_ready`.
3. Trial A: `/` is 200 and the HTML includes the confirm control.
4. Trial B: three status reads are `idle` with the headline and detail
   strings above, and `pending-operation` is 204.
5. The PC browser loads `http://192.168.50.1:8000/` in both trials without
   using a tunnel or the Internet interface as the path. `ip route get
   192.168.50.1` on the PC names the VoiceStock interface.
6. Ctrl+C stops `voicestock-pi`. The operator records the shell's exit
   status when it is available.

## Failure conditions

- Bind error because `192.168.50.1` is missing: **BLOCKED** on TC-NET-001.
- Idle status is anything other than `idle` before a press: **FAILED**.
- Trial A returns a pending operation: **FAILED**. That command has no
  ports and must not invent one.

## Recovery and cleanup

Stop both servers. Confirm port 8000 on the Pi is free before the next
case. Do not commit the output directory.

## Limitations and exclusions

`/health` does not mean the microphone, the button, or the PC is healthy.
The runtime documents that. This case does not confirm or cancel anything.
That is TC-WEB-002. It does not close
[PendingOperationWeb-08](https://app.clickup.com/t/86e3evek6).
