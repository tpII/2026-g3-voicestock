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
- Gemini y Groq restringen la salida con schema; Ollama usa el modo indicado arriba.
- Groq usa `reasoning_effort: none` y schema estricto.
- Las métricas marcadas con `*` se calculan solo sobre solicitudes exitosas.
- `Exact total` incluye los errores de API y representa el resultado de punta a punta.

## Resultados por modelo

| Proveedor | Modelo | Casos | Exitosas | API OK | JSON* | Schema* | Operación* | Producto* | Cantidad* | Exact* | Exact total | Latencia ms | Tok/s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama | qwen3:4b-instruct | 10 | 10 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 10215.27 | 15.14 |

## Resultado por caso

`Sí` significa que la respuesta coincidió exactamente con la salida esperada; `No` indica que el caso falló o que la solicitud no se completó.

| Proveedor | Modelo | solo_agregar | solo_restar | negar_agregacion | negar_restacion | restar_ambos | corregir_cantidad | negar_agregacion_y_restacion | negar_varias_agregaciones | negar_varias_restaciones | caso_integral |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ollama | qwen3:4b-instruct | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí | Sí |

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

### caso_integral

Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

```json
{
  "operaciones": [
    {
      "operacion": "agregar_stock",
      "producto": "Coca Cola 2L",
      "cantidad": 2
    },
    {
      "operacion": "restar_stock",
      "producto": "Arroz Gallo 1kg",
      "cantidad": 2
    },
    {
      "operacion": "restar_stock",
      "producto": "Fideos Matarazzo 500g",
      "cantidad": 3
    }
  ]
}
```

## Errores y respuestas no exactas

Todos los modelos obtuvieron exact match en todos los casos.
