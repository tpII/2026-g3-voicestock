# Campaign fixtures

These files are inputs for the procedures. They were not produced by a
microphone and they are not execution evidence.

| File | Use |
| --- | --- |
| [campaign-catalog.json](campaign-catalog.json) | Catalog passed to `voicestock-pi --catalog` and to TC-CON-001. |
| [contract-add-stock.json](contract-add-stock.json) | Payload accepted by `OperationValidator`. No `recognized_text`, because that field is not part of `ContractPayload`. |
| [service-success-payload.json](service-success-payload.json) | Object a future PC audio fixture must place in `ServiceResult.payload`. The `recognized_text` string is synthetic. It is not a transcription. |

`load_catalog` accepts this catalog: the two products are distinguishable
by presentation, and each product is identifiable by its own attributes.
A query with name and brand and no presentation matches both and is
ambiguous.

Expected view after the Pi accepts the service payload:

| API field | Value |
| --- | --- |
| `product` | `Arroz Marolio 1 kg` |
| `operation` | `agregar` |
| `quantity` | `2` |
| `unit` | `unidad` |
| `confirmation_message` | `Agregar 2 unidades de Arroz Marolio 1 kg` |
| `recognized_text` | `agregar dos de arroz marolio de un kilo` |

`unit` stays singular in the field. The sentence uses `unidades` because
`PendingOperation.to_view` pluralizes only the confirmation message. That
is the current implementation. A case that expects `unidades` in the `unit`
field does not match the code.
