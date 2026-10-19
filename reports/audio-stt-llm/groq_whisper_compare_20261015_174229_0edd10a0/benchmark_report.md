# Audio → Groq Whisper → GPT OSS 20B → JSON

Una corrida por modelo y audio; sin calentamiento ni reintentos. Todo se coordina desde la PC. Ambos modelos STT y el LLM son remotos.
Los tiempos API incluyen red, subida y procesamiento remoto; no son tiempos puros de inferencia. pipeline_s empieza antes de leer el WAV y termina al recibir/procesar el JSON del LLM; excluye evaluación y escritura del reporte. Los tiempos agregados cubren sólo recorridos exitosos.
El LLM recibe exclusivamente la transcripción, el contrato y el catálogo; no recibe el texto de referencia ni el JSON esperado. No hay reparación de transcripciones ni cambios al inventario.
WER/CER ignoran puntuación y mayúsculas, pero distinguen números escritos y dígitos. Son métricas textuales; JSON exacto mide el recorrido completo y no garantiza fidelidad del STT. Referencias de audio pendientes de verificación humana. La RAM de los modelos remotos no es observable.

## Resumen por STT

| Modelo STT | JSON exacto | Errores | STT medio s | LLM medio s | Total medio s | WER % | CER % |
|---|---:|---:|---:|---:|---:|---:|---:|
| whisper-large-v3 | 4/10 (40.0%) | 6 | 1.001 | 0.606 | 1.608 | 13.554 | 6.878 |
| whisper-large-v3-turbo | 5/10 (50.0%) | 5 | 0.939 | 0.651 | 1.591 | 12.952 | 7.937 |

## Resultados por nivel

| STT | Nivel | Procesados/esperados | JSON exacto |
|---|---|---:|---:|
| whisper-large-v3 | basico | 2/2 | 2/2 |
| whisper-large-v3 | habitual | 4/4 | 1/4 |
| whisper-large-v3 | exigente | 4/4 | 1/4 |
| whisper-large-v3-turbo | basico | 2/2 | 2/2 |
| whisper-large-v3-turbo | habitual | 4/4 | 2/4 |
| whisper-large-v3-turbo | exigente | 4/4 | 1/4 |

## Tiempos y exactitud por prompt

| STT | Caso | STT s | LLM s | Total s | JSON exacto | Estado |
|---|---|---:|---:|---:|---|---|
| whisper-large-v3 | solo_agregar | 1.763 | 0.513 | 2.276 | True | ok |
| whisper-large-v3-turbo | solo_agregar | 0.690 | 0.523 | 1.213 | True | ok |
| whisper-large-v3-turbo | solo_restar | 0.653 | 0.478 | 1.131 | True | ok |
| whisper-large-v3 | solo_restar | 0.682 | 0.527 | 1.209 | True | ok |
| whisper-large-v3 | restar_ambos | 0.693 | 0.719 | 1.412 | True | ok |
| whisper-large-v3-turbo | restar_ambos | 0.726 | 0.504 | 1.231 | True | ok |
| whisper-large-v3-turbo | corregir_cantidad | 0.668 | 0.625 | 1.294 | True | ok |
| whisper-large-v3 | corregir_cantidad | 0.609 | 0.125 | 0.734 | False | llm_error |
| whisper-large-v3 | negar_agregacion | 0.688 | 0.148 | 0.836 | False | llm_error |
| whisper-large-v3-turbo | negar_agregacion | 0.675 | 0.149 | 0.825 | False | llm_error |
| whisper-large-v3-turbo | negar_restacion | 0.688 | 0.137 | 0.825 | False | llm_error |
| whisper-large-v3 | negar_restacion | 0.822 | 0.132 | 0.955 | False | llm_error |
| whisper-large-v3 | negar_varias_agregaciones | 0.864 | 0.667 | 1.533 | True | ok |
| whisper-large-v3-turbo | negar_varias_agregaciones | 1.058 | 0.126 | 1.185 | False | llm_error |
| whisper-large-v3-turbo | negar_varias_restaciones | 0.744 | 0.139 | 0.883 | False | llm_error |
| whisper-large-v3 | negar_varias_restaciones | 0.813 | 0.134 | 0.947 | False | llm_error |
| whisper-large-v3 | negar_agregacion_y_restacion | 0.752 | 0.141 | 0.894 | False | llm_error |
| whisper-large-v3-turbo | negar_agregacion_y_restacion | 0.980 | 0.130 | 1.110 | False | llm_error |
| whisper-large-v3-turbo | caso_integral | 1.959 | 1.123 | 3.088 | True | ok |
| whisper-large-v3 | caso_integral | 1.746 | 0.147 | 1.894 | False | llm_error |

## Comparación de transcripciones

| Caso | Referencia | Large V3 | Turbo |
|---|---|---|---|
| solo_agregar | Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros. |  Agregá tres Coca Cola comunes de dos litros y cuatro Sprites comunes de 1,5 litros. |  Agregar 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros. |
| solo_restar | Restá dos paquetes de arroz Gallo de 1 kg. |  Resta dos paquetes de arroz gallo de un kilo. |  Resta dos paquetes de arroz gallo de un kilo. |
| restar_ambos | Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml. |  Restá dos Coca Cola Cola Zero de dos litros y cuatro envases de detergente magistral de 750 mililitros. |  Resta 2 Coca-Cola Zero de 2 litros y 4 envases de detergente Magistral de 750 mililitros. |
| corregir_cantidad | Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos. |  Agregá tres Coca Cola comunes de dos litros, perdón, eran dos. |  Agregá, tres Coca-Cola comunes de dos litros, perdón, eran dos. |
| negar_agregacion | Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues. |  Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron, no las cargues. |  Agrega 5 botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron, no las cargues. |
| negar_restacion | Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes. |  Restá cuatro envases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes. |  Resta 4 envases de detergente Magistral de 750 mililitros. Perdón, no se vendieron, no los restes. |
| negar_varias_agregaciones | Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues. |  Agregá tres Coca Cola comunes de dos litros, cuatro Sprites comunes de 1,5 litros y cinco paquetes de arroz gallo de un kilo. Me equivoqué, las CocaColas comunes de dos litros y las Sprites comunes de 1,5 no las cargues. |  Agregá 3 Coca-Cola comunes de 2 litros, 4 Sprite comunes de 1,5 litros y 5 paquetes de arroz gallo de 1 kilo. Me equivoqué, las Coca-Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues. |
| negar_varias_restaciones | Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes. |  Restá dos Coca Cola Cero de dos litros, tres paquetes de arroz gallo de un kilo y cuatro envases de detergente magistral de 750 mililitros. Las CocaCero y el arroz no se vendieron, no los restes. |  Restá dos Coca-Cola Cero de dos litros, tres paquetes de arroz gallo de un kilo y cuatro envases de detergente magistral de 750 mililitros. Las Coca Cero y el arroz no se vendieron, no los restes. |
| negar_agregacion_y_restacion | Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones. |  Agregá cuatro sprites comunes de dos litros y restá dos paquetes de arroz gallo de un kilo. Perdón, las sprites no llegaron y el arroz no se vendió. No hagas ninguna de esas dos operaciones. |  Agregá 4 Sprites comunes de 2 litros y restá 2 paquetes de arroz gallo de 1 kilo. Perdón, las Sprites no llegaron y el arroz no se vendió. No hagas ninguna de esas dos operaciones. |
| caso_integral | Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite. |  Agregá tres Coca Cola comunes de dos litros, perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz gallo de un kilo y tres paquetes de fideos Matarazzo de 500 gramos. Restá cuatro Coca Colas Cero de dos litros y cinco envases de detergente magistral de 750 mililitros. Perdón, ni las Coca Cero ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de un litro y restá dos Sprite comunes de dos litros. Perdón, la leche no llegó y esas sprites no se vendieron. No cargues la leche ni restes esas sprites. |  Agregá, tres Coca-Cola comunes de dos litros, perdón, eran dos. Agregá, cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargues. Resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos Matarazzo de 500 gramos. Resta cuatro Coca-Cola cero de dos litros y cinco envases de detergente magistral de 750 ml. Perdón, ni las Coca Cero ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de un litro y restá dos Sprite comunes de dos litros. Perdón, la leche no llegó y esas Sprite no se vendieron. No cargues la leche ni restes esas Sprite. |

## whisper-large-v3 / solo_agregar

**Referencia:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Transcripción:**  Agregá tres Coca Cola comunes de dos litros y cuatro Sprites comunes de 1,5 litros.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":3},{"operacion":"agregar_stock","producto":"Sprite 1.5L","cantidad":4}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3-turbo / solo_agregar

**Referencia:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Transcripción:**  Agregar 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":3},{"operacion":"agregar_stock","producto":"Sprite 1.5L","cantidad":4}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3-turbo / solo_restar

**Referencia:** Restá dos paquetes de arroz Gallo de 1 kg.

**Transcripción:**  Resta dos paquetes de arroz gallo de un kilo.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Arroz Gallo 1kg","cantidad":2}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3 / solo_restar

**Referencia:** Restá dos paquetes de arroz Gallo de 1 kg.

**Transcripción:**  Resta dos paquetes de arroz gallo de un kilo.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Arroz Gallo 1kg","cantidad":2}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3 / restar_ambos

**Referencia:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Transcripción:**  Restá dos Coca Cola Cola Zero de dos litros y cuatro envases de detergente magistral de 750 mililitros.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Coca Cola Zero 2L","cantidad":2},{"operacion":"restar_stock","producto":"Detergente Magistral 750ml","cantidad":4}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3-turbo / restar_ambos

**Referencia:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Transcripción:**  Resta 2 Coca-Cola Zero de 2 litros y 4 envases de detergente Magistral de 750 mililitros.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Coca Cola Zero 2L","cantidad":2},{"operacion":"restar_stock","producto":"Detergente Magistral 750ml","cantidad":4}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3-turbo / corregir_cantidad

**Referencia:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Transcripción:**  Agregá, tres Coca-Cola comunes de dos litros, perdón, eran dos.

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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":2}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3 / corregir_cantidad

**Referencia:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Transcripción:**  Agregá tres Coca Cola comunes de dos litros, perdón, eran dos.

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

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7382, Requested 1261. Please try again in 4.8225s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3 / negar_agregacion

**Referencia:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Transcripción:**  Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron, no las cargues.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7245, Requested 1257. Please try again in 3.765s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3-turbo / negar_agregacion

**Referencia:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Transcripción:**  Agrega 5 botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron, no las cargues.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7133, Requested 1274. Please try again in 3.0525s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3-turbo / negar_restacion

**Referencia:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Transcripción:**  Resta 4 envases de detergente Magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7008, Requested 1258. Please try again in 1.995s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3 / negar_restacion

**Referencia:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Transcripción:**  Restá cuatro envases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 6823, Requested 1257. Please try again in 600ms. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3 / negar_varias_agregaciones

**Referencia:** Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

**Transcripción:**  Agregá tres Coca Cola comunes de dos litros, cuatro Sprites comunes de 1,5 litros y cinco paquetes de arroz gallo de un kilo. Me equivoqué, las CocaColas comunes de dos litros y las Sprites comunes de 1,5 no las cargues.

**JSON esperado:**
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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Arroz Gallo 1kg","cantidad":5}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3-turbo / negar_varias_agregaciones

**Referencia:** Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

**Transcripción:**  Agregá 3 Coca-Cola comunes de 2 litros, 4 Sprite comunes de 1,5 litros y 5 paquetes de arroz gallo de 1 kilo. Me equivoqué, las Coca-Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

**JSON esperado:**
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

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7778, Requested 1322. Please try again in 8.25s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3-turbo / negar_varias_restaciones

**Referencia:** Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

**Transcripción:**  Restá dos Coca-Cola Cero de dos litros, tres paquetes de arroz gallo de un kilo y cuatro envases de detergente magistral de 750 mililitros. Las Coca Cero y el arroz no se vendieron, no los restes.

**JSON esperado:**
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

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7658, Requested 1473. Please try again in 8.4825s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3 / negar_varias_restaciones

**Referencia:** Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

**Transcripción:**  Restá dos Coca Cola Cero de dos litros, tres paquetes de arroz gallo de un kilo y cuatro envases de detergente magistral de 750 mililitros. Las CocaCero y el arroz no se vendieron, no los restes.

**JSON esperado:**
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

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7530, Requested 1312. Please try again in 6.314999999s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3 / negar_agregacion_y_restacion

**Referencia:** Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

**Transcripción:**  Agregá cuatro sprites comunes de dos litros y restá dos paquetes de arroz gallo de un kilo. Perdón, las sprites no llegaron y el arroz no se vendió. No hagas ninguna de esas dos operaciones.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7371, Requested 1466. Please try again in 6.2775s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3-turbo / negar_agregacion_y_restacion

**Referencia:** Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

**Transcripción:**  Agregá 4 Sprites comunes de 2 litros y restá 2 paquetes de arroz gallo de 1 kilo. Perdón, las Sprites no llegaron y el arroz no se vendió. No hagas ninguna de esas dos operaciones.

**JSON esperado:**
```json
{
  "operaciones": []
}
```

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7004, Requested 1311. Please try again in 2.3625s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}


## whisper-large-v3-turbo / caso_integral

**Referencia:** Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

**Transcripción:**  Agregá, tres Coca-Cola comunes de dos litros, perdón, eran dos. Agregá, cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargues. Resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos Matarazzo de 500 gramos. Resta cuatro Coca-Cola cero de dos litros y cinco envases de detergente magistral de 750 ml. Perdón, ni las Coca Cero ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de un litro y restá dos Sprite comunes de dos litros. Perdón, la leche no llegó y esas Sprite no se vendieron. No cargues la leche ni restes esas Sprite.

**JSON esperado:**
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

**JSON obtenido:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":2},{"operacion":"restar_stock","producto":"Arroz Gallo 1kg","cantidad":2},{"operacion":"restar_stock","producto":"Fideos Matarazzo 500g","cantidad":3}]}
```

**Evaluación:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}

**Error:** Ninguno

## whisper-large-v3 / caso_integral

**Referencia:** Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

**Transcripción:**  Agregá tres Coca Cola comunes de dos litros, perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz gallo de un kilo y tres paquetes de fideos Matarazzo de 500 gramos. Restá cuatro Coca Colas Cero de dos litros y cinco envases de detergente magistral de 750 mililitros. Perdón, ni las Coca Cero ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de un litro y restá dos Sprite comunes de dos litros. Perdón, la leche no llegó y esas sprites no se vendieron. No cargues la leche ni restes esas sprites.

**JSON esperado:**
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

**JSON obtenido:**
```json

```

**Evaluación:** {}

**Error:** HTTP 429: {"error":{"message":"Rate limit reached for model `openai/gpt-oss-20b` in organization `org_01m3qrt8faefzbhch0grmbwwg4` service tier `on_demand` on tokens per minute (TPM): Limit 8000, Used 7738, Requested 1610. Please try again in 10.11s. Need more tokens? Upgrade to Dev Tier today at https://console.groq.com/settings/billing","type":"tokens","code":"rate_limit_exceeded"}}
