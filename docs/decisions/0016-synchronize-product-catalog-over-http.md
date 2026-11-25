# ADR-0016: Synchronize the product catalog over HTTP

## Status

Accepted — 25 November 2026. Implemented by `voicestock-pi` publishing
`GET /api/v1/catalog` and by the PC Groq pipeline requesting it before each
interpretation. Product identity stays
[ADR-0006](0006-identify-products-by-unique-attribute-match.md). The single
database stays
[ADR-0014](0014-keep-catalog-stock-and-history-in-one-pi-sqlite-database.md).
The persistent catalog itself stays
[ADR-0015](0015-persist-the-product-catalog-in-the-pi-database.md).
The snapshot and conditional-GET rules are specified in the
[product catalog](../interfaces/product-catalog.md).

## Context

ADR-0015 stored products, categories and aliases on the Raspberry Pi and
left the voice process on a JSON file. The PC prompt used another JSON file.
Two files can name the same package differently, and the Pi is the only
component allowed to assign `product_id`.

The application has one operator. An inventory command is expected about
once every 30–60 seconds. The operator does not edit the catalog while an
operation is in progress. The Pi owns the catalog. The PC keeps a derived
copy in memory for the current process and discards it on exit.

## Decision

1. Use ordinary HTTP. There is no custom handshake, heartbeat, WebSocket or
   background poller.
2. `voicestock-pi` exposes `GET /api/v1/catalog` from the same SQLite file
   it uses to resolve products.
3. The PC, in `groq` mode, requests that endpoint before every audio
   interpretation, and before Whisper or the language model.
4. Conditional requests use `ETag` and `If-None-Match`.
5. HTTP `200` installs one validated snapshot. The body and the ETag must
   agree.
6. HTTP `304` reuses the snapshot already installed. It has no JSON body.
   A `304` with no installed snapshot, or with a contradictory ETag, fails
   the request.
7. `version` is the snapshot schema. `revision` is the SHA-256 of the active
   products. The ETag is that revision in quotes. None of the three is the
   migration version, and none is added to `ContractPayload` or to the WAV.
8. The PC replaces the language-model context and the local matcher
   together, after validation. It does not publish a half-updated catalog.
9. A synchronization failure returns `catalog_unavailable` for that audio.
   It is not an unknown product and it does not create a pending operation.
   The next audio tries again. The previous snapshot stays in memory and is
   not used to interpret the failed audio.
10. The PC does not write the Pi database, does not persist the snapshot,
    and does not generate product identifiers.
11. The Pi still resolves the returned canonical attributes with
    `SqliteProductResolver`.
12. The audio transport and the operation contract stay as they are.

A successful catalog response shows that this request reached the catalog
endpoint. It does not show that the microphone, the button, Groq or the
stock tables are healthy.

The PC server may start while the Pi is down. Stub mode does not call the
catalog and does not need a Groq key.

## Alternatives considered

- **Independent JSON catalogs.** Already the v0.5.0 arrangement. The prompt
  and the Pi validator could diverge. Rejected as the steady state.
- **Download once when the PC starts.** A later seed or retirement would be
  invisible until restart, and the PC could not start before the Pi.
- **Send the revision with the WAV.** The Pi would still have to define what
  a mismatch means, and the PC would need a catalog from somewhere else
  first. The WAV contract would change.
- **Periodic polling.** Extra traffic while nobody is speaking, and a
  freshness window that this workload does not need.
- **A custom handshake.** More states than HTTP already provides for one
  document that changes rarely.
- **Conditional GET before each interpretation.** One small request per
  spoken command. `304` skips the body. This is the MVP.

## Consequences

- Each Groq interpretation pays one catalog request before any paid model
  call.
- An unchanged revision does not download the product list again.
- If the catalog cannot be checked, that audio is not interpreted.
- Nothing notices a catalog edit until the next interpretation.
- There is no multi-operator locking and no distributed conflict protocol.
- Synchronization does not confirm an operation and does not change stock
  or movement history. Confirmation remains provisional.
