# ADR-0002: Split source code by runtime into pc, pi and shared

## Status

Accepted

## Context

VoiceStock runs on two machines. The Raspberry Pi captures audio, converts it
to text, sends it to the PC, manages pending operations, the inventory and the
web interface. The PC runs the HTTP server and the language-model
interpretation, which the Raspberry Pi 3 cannot run.

The code started as a single `voicestock` package organized by feature
(`communication`, `interpretation`). That layout mixed both machines: the
`communication` package contained the PC server and the Raspberry Pi client
side by side. Nothing in the tree showed what had to be installed or run on
each device, and nothing prevented PC code from importing Raspberry Pi code or
the other way around.

The team agreed to organize the source by the machine that runs it.

## Decision

`src/` contains three top-level packages:

| Package | Contains | Examples |
|---|---|---|
| `pc` | Code that runs on the PC. | HTTP server, `InterpretationService`, providers, `voicestock-pc-server`. |
| `pi` | Code that runs on the Raspberry Pi. | Communication client, `voicestock-pi-client`; later Push-to-Talk, SpeechToText, pending operations, database and web. |
| `shared` | Contracts that both machines exchange. | `TransportEnvelope`, `InterpretationRequest`. |

Inside each package, code is still grouped by feature, for example
`pc/communication` and `pi/communication`.

Import rules, enforced by `tests/test_architecture.py`:

- `pc` never imports `pi`, and `pi` never imports `pc`;
- `shared` imports neither;
- only what both sides must agree on goes into `shared`. Code used by a single
  machine stays in that machine's package.

Tests mirror the layout: `tests/pc`, `tests/pi` and `tests/shared`. Tests that
need both machines at once, such as a real client–server roundtrip, live in
`tests/integration`.

The three packages are distributed together as the single `voicestock`
project, so `pip install -e ".[dev]"` installs everything on either machine.

## Alternatives considered

- **`src/voicestock/pc` and `src/voicestock/pi`:** keeps every module under
  one `voicestock` namespace and avoids generic top-level names such as `pc`
  and `pi`, which could collide with another installed package. The team
  preferred the shorter, literal `src/pc` and `src/pi`.
- **Duplicating the shared contracts in `pc` and `pi`:** gives total
  separation, but a change to one copy and not the other would make the PC
  and the Raspberry Pi stop understanding each other.
- **Keeping the layout by feature:** does not show what runs on each machine.

## Consequences

- Imports change from `voicestock.*` to `pc.*`, `pi.*` and `shared.*`.
- The `voicestock-pc-server` and `voicestock-pi-client` commands keep their
  names; they now point to `pc.main` and `pi.main`, so the project must be
  reinstalled with `pip install -e ".[dev]"`.
- `pc`, `pi` and `shared` are generic names. If a dependency ever installs a
  package with one of those names, the imports would clash; renaming would
  then require the `voicestock` namespace alternative.
- Both machines still install every package and dependency. Splitting the
  installation per machine can be decided later if the Raspberry Pi needs a
  lighter install.
