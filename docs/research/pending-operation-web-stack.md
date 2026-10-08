# Pending operation web stack

Research record for task **PendingOperationWeb-01**: select the HTTP server,
the initial web interface, and the process topology that exposes the current
pending operation.

**Status:** research closed. The decision is recorded in
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).
This document keeps the comparison. It does not implement the server, the API,
or the page.

| Area | Status |
| --- | --- |
| HTTP server | Decided: FastAPI served by Uvicorn. Not implemented in this task. |
| Frontend | Decided: vanilla HTML, CSS, and JavaScript, served as static files by the same application. Not implemented in this task. |
| Process topology | Decided: one Python process owns the orchestrator, the FSM, and `PendingOperation`. HTTP is an input adapter in that process. |

## Problem

`PendingOperationWeb` lets an operator see the current pending operation from
a browser, and later confirm or cancel it. Three choices have to be fixed
before that work starts:

1. Which HTTP server runs on the Raspberry Pi.
2. How the first web interface is built and delivered.
3. How that HTTP server relates to the process that owns the orchestrator,
   the finite-state machine, and `PendingOperation`.

The browser runs on the PC. The application state stays on the Raspberry Pi.
This task chooses the stack and the topology. It does not define routes,
payloads, or ports of the application layer.

## Constraints

The target board is a Raspberry Pi 3 with 1 GB of RAM, running the same
Python 3.11 baseline as the rest of VoiceStock (`requires-python` in
`pyproject.toml`). That process already has to share the machine with GPIO,
audio capture, local orchestration, SQLite for inventory, and later
speech-to-text. The web stack should not add a second runtime, a build
pipeline, or a cache service.

During normal operation the Raspberry Pi has no Internet access. Libraries
may be installed earlier, while a network is available. At runtime the page
and the API must be served from the Pi itself. The browser must not depend
on a CDN, an npm registry, or any other remote asset.

The operator opens the page from a browser on the PC. Connectivity is the
direct Ethernet link already chosen by `LocalNetworkInfra`:

```text
                    Internet
                       |
                     Wi-Fi
                       |
                      PC
                       |
                    Ethernet
                       |
                Raspberry Pi 3
```

The Raspberry Pi is `192.168.50.1` and the PC is `192.168.50.2` on
`192.168.50.0/24`. That plan, and the rejection of a Raspberry Pi Wi-Fi
access point, are recorded in the
[local network strategy](local-network-strategy.md) and applied by the
[Ethernet setup guide](../setup/local-network.md). This feature uses that
link. It does not choose another one.

The October delivery needs a small page that can show the current pending
operation. November may grow the interface. The HTTP contract should be able
to survive that growth. Operational and maintenance cost should stay low:
one language, one process to start, and no reverse proxy or container whose
only job is to publish this page.

SQLite remains the inventory store. It is not a message bus between HTTP and
the orchestrator. Redis is not introduced for that role either.

## Alternatives considered

The comparison is limited to options that could realistically ship on this
hardware for the October increment. It is not a survey of the web ecosystem.

### HTTP server

#### Flask

Flask is a small WSGI framework. A few routes and Jinja templates are enough
for a read-only page, and the framework is familiar. Request and response
shapes are ordinary Python unless the application adds another validation
library. OpenAPI, when wanted, is also an extra piece.

That is a workable server for a form that posts back to the same process. It
is a weaker fit once `PendingOperationWeb-04` needs an explicit, versioned
HTTP contract with typed request and response models.

#### FastAPI

FastAPI is an ASGI framework. Routes declare Pydantic models, so invalid
bodies fail at the boundary before application code runs. The same
declarations describe the contract that a later page, or a later client,
calls. Uvicorn is the ASGI server that actually accepts connections.

FastAPI and Uvicorn are already dependencies of this repository because the
PC interpretation server uses them. That server is a different process, on
the other machine, and it implements the Pi-to-PC interpretation transport
from [ADR-0001](../decisions/0001-use-http-json-for-pi-pc-communication.md).
Reusing the same libraries on the Pi does not merge the two HTTP surfaces.
Under [ADR-0002](../decisions/0002-split-source-by-runtime-pc-pi-shared.md),
the operator UI lives in `pi` and must not import `pc`.

The reason to prefer FastAPI here is the contract: explicit routes, typed
models, validation, and a boundary that can stay stable if the page is
replaced. Throughput is not the reason. One operator confirming one pending
operation does not stress either framework.

### Frontend

#### Server-rendered templates

Jinja, or an equivalent template engine, can render the pending operation on
each request. Confirm and cancel can be HTML forms. There is no separate
frontend build.

The page and the HTTP handler then share one rendering path. A later UI that
is not a set of templates has to be cut free of that path. The October page
is small enough for templates, but the November UI is expected to grow, and
the feature already needs a programmatic API in `PendingOperationWeb-04`.

#### Vanilla HTML, CSS, and JavaScript as static files

The application serves a fixed set of files. JavaScript calls a versioned
HTTP API and updates the page. There is no Node.js process, no bundler, and
no framework runtime in the browser beyond what the browser already provides.

The files stay small, work offline, and can be replaced later by another
client of the same API. The cost is that the first page writes a little more
JavaScript than a template would, and it does not get a component model.

#### Single-page application (React, Vue, Angular, or similar)

A compiled frontend can grow into a larger UI and can talk to the same HTTP
API. It also asks for a Node.js toolchain to build, a bundle to deploy, and
more memory in the browser and in the build environment. None of that runs
comfortably as an extra requirement on the Raspberry Pi for the October
delivery, and the feature does not yet have a UI large enough to need a
component framework.

A separate frontend package would also be a second artifact to version and
start. That split can be reconsidered if a later increment outgrows static
files, because the HTTP contract is what the client depends on.

### Process topology

#### HTTP and the orchestrator in one process

The Python process that runs VoiceStock on the Pi also runs Uvicorn. FastAPI
routes call application ports. Those ports are the only way HTTP reads or
resolves a pending operation. The orchestrator remains the owner of the FSM
and of `PendingOperation`.

```text
PushToTalk
    |
    v
Orchestrator
    |
    v
FSM
    |
    v
PendingOperation
    ^
    |
Application ports
    ^
    |
FastAPI
    |
Ethernet
    |
Browser on PC
```

A confirm from the browser follows the same ownership rule. The route does
not change the FSM and does not delete the pending operation itself:

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

Sharing a process does not mean sharing the domain model with the route
handlers. It means a port call is an in-process call, with one owner of the
state.

#### HTTP and the orchestrator in separate processes

A second process would expose HTTP and talk to the orchestrator through some
inter-process channel. Candidates that were set aside for this increment
include a queue, Redis, and SQLite used as shared state. Each of them adds a
protocol the project would have to define and operate.

The extra problems are:

- an IPC mechanism has to be chosen, framed, and versioned;
- ownership of `PendingOperation` is no longer obvious, because two processes
  can both believe they hold the current operation;
- updates need synchronization that a function call does not;
- one side can be up while the other is down;
- recovery has to decide which side restarts, what it reloads, and which
  in-flight confirm or cancel is still valid;
- a pending operation can be duplicated or lost across that boundary.

Those costs are real for a distributed system. They are not justified while
one board, one operator, and one pending operation are the whole increment.

## Tradeoffs

| Criterion | Flask | FastAPI + Uvicorn | Templates | Static HTML/CSS/JS | SPA | One process | Two processes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Resources on the Pi 3 | Small | Small; libraries already installed for the PC server | Small | Small; no Node.js | Build toolchain and a larger browser payload | One runtime | A second process plus IPC |
| Complexity | Low for a few routes | Low for a typed API; more structure than a single form handler | Low until the page outgrows the templates | Low; the page and the API are separate | High for this increment | Lowest operational shape | IPC, lifecycle, and failure handling |
| Maintainability | Fine while handlers stay thin | Models document the boundary | Rendering changes touch server code | UI changes stay in static files if the API holds | A second stack to maintain | One codebase and one startup | Two deployables that must agree |
| Speed of implementation | Fast for HTML forms | Fast for the versioned API this feature already plans | Fast for October if no API is required | Fast enough for October, and it produces the API client | Slow relative to the page that is needed | No extra integration step | Dominated by the channel between processes |
| Extensibility | A later API is additional work | The contract can gain routes without a new framework | A non-template UI is a rewrite of the rendering path | Another client can replace the files | Strong for a large UI | New ports stay in-process | The channel becomes part of every new operation |
| Typing and validation | Added by hand or by another library | Request and response models are part of the framework | Not an API contract | The API is what the page validates against | Depends on the API, not on the UI kit | Types stay in one process | The IPC schema duplicates the HTTP schema |
| Offline operation | Yes, after install | Yes, after install | Yes | Yes; assets come from the Pi | Only if the bundle is fully local | Yes | Yes, but the second process must also be local |
| Deploy on the Pi | One Python process | One Python process; Uvicorn serves the app and the files | No extra service | No nginx and no frontend server | Needs a build before the files can be copied | Start the existing application | Start and supervise two units |
| State ownership | Depends on topology, not on the framework | Same | Easy to put domain rules in the template layer if nobody stops it | The page cannot own the FSM if it only calls the API | Same, if the API is the only entry | One owner | Contested unless IPC forbids a second copy |
| Concurrency | WSGI workers are a later choice | Async handlers share the process with the orchestrator; they still must not touch the FSM | A form post is one request | Polling is enough for one pending operation | A live socket is optional, not required | In-process calls; the application layer serializes access | Cross-process ordering and retries |
| Failure recovery | Process restart | Process restart | Same as the server | The browser reloads; the server still owns the outcome | Same | HTTP and the FSM stop together | Partial failure: UI up and orchestrator down, or the reverse |
| IPC | None in-process | None in-process | None | None | None by itself | Not required | Required |

WebSockets were not selected. The interaction is request/response: read the
current pending operation, then confirm or cancel it. A push channel can be
reconsidered only if a later task shows that polling cannot meet a concrete
requirement. nginx is not required to serve one application and its static
files on a two-host Ethernet segment. Docker is not part of this feature;
the [development workflow](../guides/development-workflow.md) already keeps
containers out of the current Raspberry Pi path.

## Decision

Use FastAPI and Uvicorn, with vanilla HTML, CSS, and JavaScript served by
that same application, inside the single Python process that runs the
orchestrator and owns the FSM and `PendingOperation`.

```text
FastAPI + Uvicorn + vanilla HTML/CSS/JavaScript
served by the application itself,
inside the same Python process that runs
the orchestrator and owns the FSM and PendingOperation.
```

FastAPI is the HTTP framework because the feature needs an explicit contract:
typed request and response models, validation at the boundary, and a surface
that `PendingOperationWeb-04` can implement directly. A later frontend can
replace the static files without a new HTTP design. Performance relative to
Flask is not the justification.

One process is the topology because it keeps a single owner of the execution
state and avoids IPC and distributed failure modes that this increment does
not need.

The listen address will be the Raspberry Pi address on the VoiceStock
Ethernet segment, `192.168.50.1`. The port is not chosen here.

FastAPI routes, and the page they serve, are not the owner of
`PendingOperation`. They do not delete a pending operation, they do not
modify the FSM, and they do not contain domain rules. Query and resolution
go through application ports. A route that mutates orchestrator state
directly would violate this decision even if it lives in the same process.

## Implications for later tasks

- **PendingOperationWeb-02** defines the application ports used to query the
  current pending operation and to resolve it (`confirm` / `cancel`). Those
  ports are the only write path the HTTP adapter may call. The types and the
  hand-off to `PendingOperationFlow` are in the
  [flow contract](pending-operation-web-flow-contract.md).
- **PendingOperationWeb-03** creates the FastAPI application, runs it with
  Uvicorn, and mounts the static files. HTTP frameworks stay in `pi/web` and
  in the PC server. The command `voicestock-pi-web` is a temporary way to
  start that app before the orchestrator exists. It is not a second
  production process. How the app and the orchestrator share one process is
  still open. The
  [web setup guide](../setup/pi-web.md) is the run procedure.
- **PendingOperationWeb-04** implements a versioned HTTP API on that
  application. Schemas belong to the API, not to the FSM.
- **PendingOperationWeb-05** implements the page in vanilla JavaScript that
  calls that API. It does not import Python and it does not embed domain
  transitions.
- **PendingOperationWeb-06** documents the resulting architecture and the
  HTTP contract, including how the browser on `192.168.50.2` reaches the Pi
  on `192.168.50.1`. The contract's source of truth will be that interface
  document, not this research note.

## Out of scope

This task does not add a FastAPI app, routes, static files, a query port, a
resolution port, confirmation, cancellation, FSM changes, or inventory
updates. It does not change `pyproject.toml`: FastAPI and Uvicorn are
already declared.

## References

- [ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md),
  the decision that implementation follows.
- [ADR-0001](../decisions/0001-use-http-json-for-pi-pc-communication.md),
  the Pi-to-PC interpretation transport. A different HTTP server, on the PC.
- [ADR-0002](../decisions/0002-split-source-by-runtime-pc-pi-shared.md),
  package split. The operator UI belongs in `pi`.
- [Local network strategy](local-network-strategy.md) and the
  [Ethernet setup guide](../setup/local-network.md).
- FastAPI, first steps (path operations, Pydantic models, and OpenAPI):
  <https://fastapi.tiangolo.com/tutorial/first-steps/>.
- Uvicorn, an ASGI server used to run FastAPI:
  <https://www.uvicorn.org/>.
- FastAPI static files (`StaticFiles`):
  <https://fastapi.tiangolo.com/tutorial/static-files/>.
