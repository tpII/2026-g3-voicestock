# Audio → Whisper Small Q5 → Gemini → JSON

Modelo solicitado: `gemini-3.8-flash`. Una corrida por prompt; sin calentamiento, reintentos ni reparación de transcripciones.
El LLM recibe sólo la transcripción dentro del contrato y catálogo existentes. No recibe texto ni JSON esperado.
RAM RSS en MiB muestreada cada 10 ms: trabajador Whisper y proceso Python del cliente API (incluye orquestación y SDK). La RAM de Gemini remoto no es observable y queda sin dato. No se aplican operaciones al inventario.
Referencias pendientes de verificación humana del audio.

JSON exacto: **4/6** casos procesados.

| Caso | Nivel | JSON exacto | Whisper MiB | Cliente API MiB |
| --- | --- | --- | --- | --- |
| solo_agregar | basico | False | 344.8 | — |
| solo_restar | basico | True | 346.3 | 73.2 |
| restar_ambos | habitual | True | 347.0 | 73.3 |
| corregir_cantidad | habitual | False | 347.0 | — |
| negar_agregacion | habitual | True | 347.0 | 73.3 |
| negar_restacion | habitual | True | 349.5 | 73.4 |

## solo_agregar

**Referencia:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Transcripción enviada:**  Agrega 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

**JSON esperado:**
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

**Salida real:**
```json

```

**Evaluación:** {}
**Error:** 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}

## solo_restar

**Referencia:** Restá dos paquetes de arroz Gallo de 1 kg.

**Transcripción enviada:**  Resta dos paquetes de arroz gallo de un kilo.

**JSON esperado:**
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

**Salida real:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Arroz Gallo 1kg","cantidad":2}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## restar_ambos

**Referencia:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Transcripción enviada:**  Resta 2 Coca-Cola 0 de 2 litros y 4 en bases de detergente magistral de 750 mililitros.

**JSON esperado:**
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

**Salida real:**
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

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## corregir_cantidad

**Referencia:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Transcripción enviada:**  Agrega 3 Coca-Cola comunes de 2 litros, perdón eran 2.

**JSON esperado:**
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

**Salida real:**
```json

```

**Evaluación:** {}
**Error:** 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}

## negar_agregacion

**Referencia:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Transcripción enviada:**  Agrega 5 botellas de agua billa de licencia de 1,5 litros. Perdón, esas no llegaron, no las cargues.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**Salida real:**
```json
{"operaciones":[]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## negar_restacion

**Referencia:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Transcripción enviada:**  Resta 4 en bases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**Salida real:**
```json
{"operaciones":[]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None
