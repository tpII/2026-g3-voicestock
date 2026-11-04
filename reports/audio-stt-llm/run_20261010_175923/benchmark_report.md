# Audio → STT → LLM → JSON

Whisper Small Q5_1 → qwen3:4b-instruct. Una corrida por prompt, sin calentamiento, reintentos ni corrección manual.
El LLM recibe la transcripción, el contrato y el catálogo existentes; no recibe el texto esperado ni el JSON de referencia.
Temperatura 0, think=false, formato JSON_SCHEMA. El esquema garantiza estructura, no contenido correcto.
RSS en MiB cada 10 ms. Whisper: proceso trabajador; Qwen: suma de procesos Ollama (servidor y runner). Whisper permanece cargado mientras Qwen procesa. La suma de RSS puede contar páginas compartidas varias veces; no representa memoria física exclusiva ni VRAM. La primera solicitud incluye la carga de Qwen si no estaba residente.
Referencias pendientes de verificación escuchando el audio. No se modificó inventario ni se aplicaron las operaciones generadas.

**Cobertura RAM:** El monitor inicial incluía el servidor Ollama pero no su runner llama-server. Se incorporó un monitor externo conservando la traza: casos 2–6 tienen pico RSS servidor+runner por ventana del caso. En solo_agregar sólo hay una observación posterior (~3137 MiB); su pico inicial no está disponible. No se repitió ninguna inferencia. No hay pico simultáneo completo validado para esta corrida; se marca sin dato.

**JSON exacto esperado: 5/6 casos procesados.**

| Caso | Nivel | JSON exacto | Whisper MiB | Ollama MiB | Pico simultáneo MiB |
| --- | --- | --- | --- | --- | --- |
| solo_agregar | basico | True | 344.8 | — | — |
| solo_restar | basico | True | 346.4 | 3137.8 | — |
| restar_ambos | habitual | False | 347.1 | 3158.2 | — |
| corregir_cantidad | habitual | True | 347.1 | 3158.4 | — |
| negar_agregacion | habitual | True | 347.1 | 3158.4 | — |
| negar_restacion | habitual | True | 347.0 | 3151.6 | — |

## solo_agregar

**Texto esperado:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Transcripción recibida por Qwen:**  Agrega 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

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

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## solo_restar

**Texto esperado:** Restá dos paquetes de arroz Gallo de 1 kg.

**Transcripción recibida por Qwen:**  Resta dos paquetes de arroz gallo de un kilo.

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

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## restar_ambos

**Texto esperado:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Transcripción recibida por Qwen:**  Resta 2 Coca-Cola 0 de 2 litros y 4 en bases de detergente magistral de 750 mililitros.

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
      "producto": "Coca Cola 2L",
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

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": false, "correct_quantity": true, "exact_match": false}
**Error:** None

## corregir_cantidad

**Texto esperado:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Transcripción recibida por Qwen:**  Agrega 3 Coca-Cola comunes de 2 litros, perdón eran 2.

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
{"operaciones": [{"operacion": "agregar_stock", "producto": "Coca Cola 2L", "cantidad": 2}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## negar_agregacion

**Texto esperado:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Transcripción recibida por Qwen:**  Agrega 5 botellas de agua billa de licencia de 1,5 litros. Perdón, esas no llegaron, no las cargues.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**Salida real:**
```json
{
  "operaciones": []
}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## negar_restacion

**Texto esperado:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Transcripción recibida por Qwen:**  Resta 4 en bases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**Salida real:**
```json
{
  "operaciones": []
}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Error:** None

## Devolución

Básicos: 2/2 JSON exactos. Habituales: 3/4 JSON exactos. Todas las salidas
son JSON y cumplen el esquema; sólo cinco preservan el contenido esperado.

En `restar_ambos`, Whisper entrega «Coca-Cola 0», pero Qwen selecciona
`Coca Cola 2L` en lugar de `Coca Cola Zero 2L`. Las dos operaciones y
sus cantidades (2 y 4) se conservan. El error es la selección de variante
del artículo en la interpretación del texto transcrito. No se ejecutó
una segunda solicitud con el texto limpio, por lo que no se aisla
experimentalmente si el fallo también ocurre con «Zero» escrito.

La corrección tres → dos y ambas cancelaciones simples fueron interpretadas
correctamente. Qwen produjo la lista vacía aun cuando Whisper deformó
Villavicencio, ya que conservó la cancelación completa.

Whisper alcanzó ~347 MiB RSS. Ollama con Qwen alcanzó ~3158 MiB RSS
(~3,08 GiB) en las ventanas observadas: servidor incluido, primera carga
sin pico completo. Ollama informó contexto 4096 y `size_vram` ~91 MiB,
que se conserva por separado y no se suma a la RAM RSS.
