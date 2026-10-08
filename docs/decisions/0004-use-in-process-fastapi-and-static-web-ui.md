# ADR-0004: Use in-process FastAPI and a static web UI for pending operations

## Status

Accepted

## Context

VoiceStock must show the current pending operation in a browser on the PC,
and later confirm or cancel it. The page is served by the Raspberry Pi 3.
The Pi has 1 GB of RAM, does not use Internet while the system is running,
and reaches the PC through the direct Ethernet link from `LocalNetworkInfra`
(`192.168.50.1` on the Pi, `192.168.50.2` on the PC). A Wi-Fi access point is
not the network topology.

The orchestrator, the finite-state machine, and `PendingOperation` already
belong to the Python process on the Pi. The web stack has to expose that
state without becoming a second owner of it.

The comparison is in
[the pending-operation web research](../research/pending-operation-web-stack.md).

## Decision

Serve the operator UI with FastAPI and Uvicorn, using vanilla HTML, CSS, and
JavaScript as static files of that same application. Run it inside the one
Python process that runs the orchestrator and owns the FSM and
`PendingOperation`.

```text
FastAPI + Uvicorn + vanilla HTML/CSS/JavaScript
served by the application itself,
inside the same Python process that runs
the orchestrator and owns the FSM and PendingOperation.
```

HTTP is an input adapter. Routes call application ports. They do not own
`PendingOperation`, delete it, modify the FSM, or hold domain rules.

```text
HTTP confirm
    |
    v
ResolutionPort.confirm(operation_id)
    |
    v
Application / Domain
    |
    v
FSM
```

This is not the PC interpretation server from
[ADR-0001](0001-use-http-json-for-pi-pc-communication.md). That server stays
on the PC. The UI lives in `pi`, consistent with
[ADR-0002](0002-split-source-by-runtime-pc-pi-shared.md), and does not import
`pc`.

FastAPI is selected for the explicit HTTP contract: typed request and
response models, validation, and a boundary that later UI work can keep.
The choice is not based on performance against Flask.

One process is selected so that a single component owns the execution state.
This increment does not add IPC.

Not part of this increment: React, Vue, Angular, a separate frontend,
Node.js as a frontend runtime, a second process only for HTTP, Redis,
SQLite as shared state between HTTP and the orchestrator, WebSockets, nginx,
and Docker as the way to publish this UI.

## Alternatives considered

- **Flask.** Enough for a few routes and templates. Not chosen: the pending
  API needs typed models and validation without an extra library, and that
  contract is the point of `PendingOperationWeb-04`.
- **Server-rendered templates.** Fast to ship a single page. Not chosen: the
  page and a versioned API would then be two styles of the same feature, and
  a later UI would be tied to the template engine.
- **A React, Vue, or Angular application.** Able to grow. Not chosen for this
  increment: it adds a Node.js build and a second artifact that the October
  page does not need.
- **A separate HTTP process.** Rejected. It requires an IPC mechanism,
  splits ownership of `PendingOperation`, and adds synchronization, partial
  failure, recovery, and the risk of duplicating or losing the operation.

## Consequences

### Positive

- The browser talks to the Pi over the existing Ethernet segment. No access
  point and no Internet path are required at runtime.
- One process starts the orchestrator and the UI. There is no second service
  to supervise.
- The HTTP contract can grow in later tasks while the static page remains a
  replaceable client.
- A crash stops HTTP and the FSM together, so the two sides cannot disagree
  about which pending operation is current.

### Negative

- FastAPI and Uvicorn may be imported from the PC server and from `pi/web`.
  The rest of `pi`, including pending operations, still must not import them.
  `voicestock-pi-web` only starts that app for development and validation
  until the orchestrator exists. It is not a second production process.
- Handlers share a process with the FSM. They must call ports and must not
  mutate orchestrator state, including under concurrent requests.
  `PendingOperationWeb-02` serializes resolution with one lock on the
  application gateway. See the
  [flow contract](../research/pending-operation-web-flow-contract.md).
- In-memory pending state dies with the process. This ADR does not add a
  recovery store.
- Uvicorn is the process that accepts browser connections. Putting nginx or
  another proxy in front is a later decision, not the current deploy.

### Follow-up

- `PendingOperationWeb-02` defined the query and resolution ports. The
  integration contract for `PendingOperationFlow` is the
  [flow contract](../research/pending-operation-web-flow-contract.md).
- `PendingOperationWeb-03` added the FastAPI application, the temporary
  Uvicorn command, and the placeholder static page. How that app shares the
  process with the orchestrator is still open. See the
  [web setup guide](../setup/pi-web.md).
- `PendingOperationWeb-04` implemented the versioned HTTP API. The status
  map is the
  [pending-operation web API](../interfaces/pending-operation-web-api.md).
- `PendingOperationWeb-05` consumes that API from vanilla JavaScript. See the
  [pending operation page](../interfaces/pending-operation-web-ui.md).
- `PendingOperationWeb-06` documents the resulting architecture and the HTTP
  contract.
