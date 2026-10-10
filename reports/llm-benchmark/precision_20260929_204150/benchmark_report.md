# Benchmark de precisión de interpretación

## Contrato JSON

```json
{"operaciones":[{"operacion":"agregar_stock|restar_stock","producto":"nombre canónico","cantidad":1}]}
```

- Contrato utilizado: `contract.txt`.
- Ollama se ejecuta con `think: false` y formato `schema`.
- Gemini 3.7 Flash y 3.8 Flash se ejecutan con `thinking_level: low`.
- Los demás modelos Gemini se ejecutan con `thinking_level: minimal`.
- Todos los proveedores usan temperatura 0.
- Gemini restringe la salida con schema; Ollama usa el modo indicado arriba.
- Las métricas marcadas con `*` se calculan solo sobre solicitudes exitosas.
- `Exact total` incluye los errores de API y representa el resultado de punta a punta.

## Resultados por modelo

| Proveedor | Modelo | Casos | Exitosas | API OK | JSON* | Schema* | Operación* | Producto* | Cantidad* | Exact* | Exact total | Latencia ms | Tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gemini | gemini-3.6-flash | 1 | 1 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 2084.48 | 23.987 |

## Resultado por caso

`Sí` significa que la respuesta coincidió exactamente con la salida esperada; `No` indica que el caso falló o que la solicitud no se completó.

| Proveedor | Modelo | negar_varias_agregaciones |
| --- | --- | --- |
| gemini | gemini-3.6-flash | Sí |

## Casos evaluados

### negar_varias_agregaciones

Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

```json
{
  "operaciones": [
    {
      "operacion": "agregar_stock",
      "producto": "Arroz Gallo 1kg",
      "cantidad": 5
    }
  ]
}
```

## Errores y respuestas no exactas

Todos los modelos obtuvieron exact match en todos los casos.
