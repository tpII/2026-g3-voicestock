# Benchmark de precisión de interpretación

## Contrato JSON

```json
{"operaciones":[{"operacion":"agregar_stock|restar_stock","producto":"nombre canónico","cantidad":1}]}
```

- Contrato utilizado: `contract-copy.txt`.
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
| ollama | qwen3:4b-instruct | 9 | 9 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 8207.52 | 12.755 |

## Resultado por caso

`Sí` significa que la respuesta coincidió exactamente con la salida esperada; `No` indica que el caso falló o que la solicitud no se completó.

| Proveedor | Modelo | solo_agregar | solo_restar | negar_agregacion | negar_restacion | restar_ambos | corregir_cantidad | negar_agregacion_y_restacion | negar_varias_agregaciones | negar_varias_restaciones |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama | qwen3:4b-instruct | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí |

## Casos evaluados

### solo_agregar

Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

```json
{
  "operaciones": [
    {
      "operacion": "agregar_stock",
      "producto": "Coca Cola 2L",
      "cantidad": 3
    },
    {
      "operacion": "agregar_stock",
      "producto": "Sprite 1.5L",
      "cantidad": 4
    }
  ]
}
```

### solo_restar

Restá dos paquetes de arroz Gallo de 1 kg.

```json
{
  "operaciones": [
    {
      "operacion": "restar_stock",
      "producto": "Arroz Gallo 1kg",
      "cantidad": 2
    }
  ]
}
```

### negar_agregacion

Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

```json
{
  "operaciones": []
}
```

### negar_restacion

Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

```json
{
  "operaciones": []
}
```

### restar_ambos

Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

```json
{
  "operaciones": [
    {
      "operacion": "restar_stock",
      "producto": "Coca Cola Zero 2L",
      "cantidad": 2
    },
    {
      "operacion": "restar_stock",
      "producto": "Detergente Magistral 750ml",
      "cantidad": 4
    }
  ]
}
```

### corregir_cantidad

Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

```json
{
  "operaciones": [
    {
      "operacion": "agregar_stock",
      "producto": "Coca Cola 2L",
      "cantidad": 2
    }
  ]
}
```

### negar_agregacion_y_restacion

Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

```json
{
  "operaciones": []
}
```

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

### negar_varias_restaciones

Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

```json
{
  "operaciones": [
    {
      "operacion": "restar_stock",
      "producto": "Detergente Magistral 750ml",
      "cantidad": 4
    }
  ]
}
```

## Errores y respuestas no exactas

Todos los modelos obtuvieron exact match en todos los casos.
