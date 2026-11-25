# ProductCatalog integration checks

This procedure checks that the Raspberry Pi catalog and the PC Groq pipeline
use one snapshot. It is a specification. It is not an execution record.
Nothing in this file has been run on hardware.

The closed v0.5.0 campaign stays as it was. Persistence across restart is
already recorded in
[EX-TC-PER-001-20261108-01](raspberry-validation/executions/EX-TC-PER-001-20261108-01.md).
That execution does not cover the HTTP synchronization added later.

The snapshot, the ETag and the error `catalog_unavailable` are specified in
the [product catalog](../interfaces/product-catalog.md). Commands are in the
[Pi runtime](../setup/pi-runtime.md) and the
[PC audio pipeline](../setup/pc-audio-pipeline.md).

## Preconditions

- `voicestock-pi-database init` has been run on the Pi database that
  `voicestock-pi` will open.
- `voicestock-pi` is the integrated runtime, without a JSON catalog argument.
- `voicestock-pc-server` uses `VOICESTOCK_AUDIO_PIPELINE=groq` and
  `VOICESTOCK_PI_URL` pointing at that Pi.
- The PC client timeout on the Pi is long enough for the catalog request
  plus speech-to-text plus the language model. The default of 10 seconds
  is not a measured budget.
- Logs from both processes are kept. HTTP status and `ETag` /
  `If-None-Match` are observed on the catalog request, not inferred from
  the spoken result alone.
- Stock and history, if compared, come from `voicestock-pi-database status`
  or from a read of the same database while the runtime is stopped.

No scenario below is marked passed. An execution record is a separate file,
created only after the run.

## Scenarios

### A. First synchronization

Start the Pi, then the PC, or the other way around. Speak one command that
names one product completely.

Expect the PC log or a capture of `GET /api/v1/catalog` to show no
`If-None-Match`, HTTP `200`, and an `ETag` equal to the `revision` in the
body. The body lists active products only. Expect a version-1 contract back
to the Pi. Do not treat a successful page as proof of the status code.

### B. Unchanged catalog

Speak a second command without editing the catalog.

Expect `If-None-Match` with the ETag from A, HTTP `304`, and an empty body.
Expect the interpretation to continue. There is no second prompt build to
observe directly; the evidence is the `304` together with a contract that
still matches the same catalog.

### C. Full identification

Use a command that states name, brand, variant and presentation of one seed
product, when that product has all of those attributes.

Expect the contract to carry those canonical strings, not a `product_id`.
Expect the Pi pending operation to show the product id from the database.
Read the id from the operator page or from the service log. Do not invent
the id in the procedure.

### D. Ambiguity

Use a phrase that matches more than one active product, such as a name and
brand that the seed documents as ambiguous. The
[product catalog](../interfaces/product-catalog.md) lists those groups.

Expect no pending operation that picks one package. Expect the service
error for an ambiguous product, not a guessed presentation.

### E. Alias

Use one alias stored on a seed product, for example a phrase listed in
`pi.catalog.seed`.

Expect the contract to contain that product's canonical attributes, not the
alias as the name and not a `product_id`. Expect the Pi to resolve the same
product id as in C for that product.

### F. Pi catalog unreachable

Stop the Pi process, or block `VOICESTOCK_PI_URL`, and submit one WAV.

Expect `catalog_unavailable` inside the service result. Expect no Groq
speech-to-text request and no language-model request in the PC log for that
WAV. Expect no pending operation on the Pi. A transport failure before the
PC handler is a different error and does not satisfy this scenario.

### G. Recovery

Restore the Pi endpoint. Submit the same kind of command without restarting
the PC.

Expect a new catalog request and a normal interpretation. Restarting the PC
is not part of this scenario.

### H. PC restart

Stop and start `voicestock-pc-server`. Submit one command.

Expect the first catalog request after the restart to omit `If-None-Match`
and to receive `200`.

### I. Revision change

Use a copy of the database, not the operational file. Retire a product that
has no stock, or add a product through the existing catalog API, then point
both processes at that copy.

Expect the next catalog response to be `200` with a different `revision`.
Expect a command that needs the changed product to follow the new snapshot.
Do not delete rows from the operational database to force a new hash.

### J. Isolation from stock

Before and after A and B, record stock quantities and movement counts with
`voicestock-pi-database status`.

Expect those counts to be unchanged by synchronization and interpretation.
Confirming the pending operation is out of scope: the provisional executor
reports success and does not write stock. Do not record a stock change from
confirm as a ProductCatalog result.
