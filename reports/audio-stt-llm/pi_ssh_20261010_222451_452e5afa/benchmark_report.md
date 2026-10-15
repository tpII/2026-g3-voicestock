# Raspberry STT → SSH → PC Groq integration

Whisper ggml-small-q5_1.bin on remote host → openai/gpt-oss-20b from PC.
Exact JSON: 6/6 processed; six expected cases.
One transcription and one API request per case; no warm-up or retries.
Pi STT resources cover the Whisper process; PC resources cover the Python coordinator.
Remote Groq model RAM is not observable. References require human audio verification.
SSH/scp configuration and host hardware are recorded in environment.json.
No microphone capture or inventory updates occur in this fixture experiment.

## Summary

Exact JSON success: 6/6 (100.0%).
Processed: 6/6; execution errors: 0.

basico: 2/2 exact (100.0%).

habitual: 4/4 exact (100.0%).

| Case | Exact JSON | Pi STT (s) | LLM API (s) | Whisper peak RAM (MiB) |
|---|---|---:|---:|---:|
| solo_agregar | True | 162.114 | 0.560 | 397.664 |
| solo_restar | True | 158.255 | 0.444 | 399.246 |
| restar_ambos | True | 161.279 | 0.695 | 399.996 |
| corregir_cantidad | True | 159.179 | 0.469 | 399.996 |
| negar_agregacion | True | 162.477 | 0.560 | 399.996 |
| negar_restacion | True | 162.401 | 0.593 | 402.582 |

### Resources and audio duration

| Case | Audio (s) | Pi CPU (%) | PC client RAM (MiB) | STT + API (s) |
|---|---:|---:|---:|---:|
| solo_agregar | 8.576 | 375.581 | 30.766 | 162.675 |
| solo_restar | 4.992 | 378.308 | 30.785 | 158.698 |
| restar_ambos | 8.448 | 378.598 | 30.801 | 161.974 |
| corregir_cantidad | 8.064 | 378.550 | 30.836 | 159.648 |
| negar_agregacion | 9.664 | 377.536 | 30.859 | 163.037 |
| negar_restacion | 11.072 | 377.645 | 30.891 | 162.994 |

CPU: 100% represents one logical core. PC RAM is the API client, not the model hosted by Groq.

### Overall metrics

| Metric | Value |
|---|---:|
| Exact JSON success | 6/6 (100.0%) |
| Initial model load (s) | 7.472 |
| Pi STT mean (s) | 160.951 |
| Pi STT min–max (s) | 158.255–162.477 |
| LLM API mean (s) | 0.553 |
| LLM API min–max (s) | 0.444–0.695 |
| Whisper peak RAM (MiB) | 402.582 |
| PC client peak RAM (MiB) | 30.891 |

Pi STT: mean 160.951 s; range 158.255–162.477 s; sum 965.705 s (6 measurements).

LLM API: mean 0.553 s; range 0.444–0.695 s; sum 3.321 s (6 measurements).

Initial model load: 7.472 s.

Whisper maximum sampled RSS: 402.58 MiB.

Pi STT includes WAV reading/conversion and inference. LLM API includes network and response handling. Stage sums exclude SSH transfers, model load and orchestration; they are not total run duration.

### Reference, transcription and JSON comparison

| Case | Reference | STT output | Expected JSON | Actual JSON |
|---|---|---|---|---|
| solo_agregar | Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros. | Agrega, tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros. | {"operaciones": [{"operacion": "agregar_stock", "producto": "Coca Cola 2L", "cantidad": 3}, {"operacion": "agregar_stock", "producto": "Sprite 1.5L", "cantidad": 4}]} | {"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":3},{"operacion":"agregar_stock","producto":"Sprite 1.5L","cantidad":4}]} |
| solo_restar | Restá dos paquetes de arroz Gallo de 1 kg. | resta, dos paquetes de arrroz gallo de un kilo | {"operaciones": [{"operacion": "restar_stock", "producto": "Arroz Gallo 1kg", "cantidad": 2}]} | {"operaciones":[{"operacion":"restar_stock","producto":"Arroz Gallo 1kg","cantidad":2}]} |
| restar_ambos | Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml. | restá, 2 Coca Cola Zero de 2 litros y 4 envases de detergente Magistral de 750 mililitros. | {"operaciones": [{"operacion": "restar_stock", "producto": "Coca Cola Zero 2L", "cantidad": 2}, {"operacion": "restar_stock", "producto": "Detergente Magistral 750ml", "cantidad": 4}]} | {"operaciones":[{"operacion":"restar_stock","producto":"Coca Cola Zero 2L","cantidad":2},{"operacion":"restar_stock","producto":"Detergente Magistral 750ml","cantidad":4}]} |
| corregir_cantidad | Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos. | Agrega, tres Coca Cola comunes de 2 litros, perdón, eran dos. | {"operaciones": [{"operacion": "agregar_stock", "producto": "Coca Cola 2L", "cantidad": 2}]} | {"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":2}]} |
| negar_agregacion | Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues. | Agrega 5 botellas de agua Villavicencio de 1,5 litros, perdón, esas no llegaron, no las cargue. | {"operaciones": []} | {"operaciones": []} |
| negar_restacion | Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes. | restá, 4 envases de detergentes magistral de 750 mililitros, perdón, no se vendieron, no los restes. | {"operaciones": []} | {"operaciones": []} |

### Validation by case

| Case | Level | Status | Valid JSON | Schema | Operation | Product | Quantity | Exact JSON | Error |
|---|---|---|---|---|---|---|---|---|---|
| solo_agregar | basico | ok | True | True | True | True | True | True | None |
| solo_restar | basico | ok | True | True | True | True | True | True | None |
| restar_ambos | habitual | ok | True | True | True | True | True | True | None |
| corregir_cantidad | habitual | ok | True | True | True | True | True | True | None |
| negar_agregacion | habitual | ok | True | True | True | True | True | True | None |
| negar_restacion | habitual | ok | True | True | True | True | True | True | None |

### Component resources by case

| Case | Component | Wall time (s) | Base RAM (MiB) | Peak RAM (MiB) | CPU time (s) | CPU (%) |
|---|---|---:|---:|---:|---:|---:|---:|
| solo_agregar | Pi Whisper | 162.114 | 277.875 | 397.664 | 608.870 | 375.581 |
| solo_agregar | PC API client | 0.560 | 27.867 | 30.766 | 0.030 | 5.352 |
| solo_restar | Pi Whisper | 158.255 | 397.246 | 399.246 | 598.690 | 378.308 |
| solo_restar | PC API client | 0.444 | 30.777 | 30.785 | 0.010 | 2.254 |
| restar_ambos | Pi Whisper | 161.279 | 399.246 | 399.996 | 610.600 | 378.598 |
| restar_ambos | PC API client | 0.695 | 30.793 | 30.801 | 0.010 | 1.438 |
| corregir_cantidad | Pi Whisper | 159.179 | 399.996 | 399.996 | 602.570 | 378.550 |
| corregir_cantidad | PC API client | 0.469 | 30.828 | 30.836 | 0.010 | 2.132 |
| negar_agregacion | Pi Whisper | 162.477 | 399.996 | 399.996 | 613.410 | 377.536 |
| negar_agregacion | PC API client | 0.560 | 30.855 | 30.859 | 0.010 | 1.787 |
| negar_restacion | Pi Whisper | 162.401 | 399.957 | 402.582 | 613.300 | 377.645 |
| negar_restacion | PC API client | 0.593 | 30.883 | 30.891 | 0.010 | 1.687 |

### Initial load resources

| Metric | Value |
|---|---:|
| request_wall_s | 7.481 |
| ram_base_mib | 0.000 |
| ram_peak_mib | 277.875 |
| cpu_s | 1.140 |
| cpu_pct | 15.239 |

Exact JSON evaluates the complete pipeline; it does not measure STT semantic accuracy or prove that quantities were present in the transcription. Missing measurements are shown as N/A.

## solo_agregar (basico)

**Reference:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Pi transcription:** Agrega, tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Expected JSON:**
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

**Actual JSON:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":3},{"operacion":"agregar_stock","producto":"Sprite 1.5L","cantidad":4}]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 277.875, "ram_peak_mib": 397.6640625, "cpu_s": 608.87, "cpu_pct": 375.58060208971847, "request_wall_s": 162.11433620699972}
**PC resources:** {"ram_base_mib": 27.8671875, "ram_peak_mib": 30.765625, "cpu_s": 0.02999999999999997, "cpu_pct": 5.352384062035225, "request_wall_s": 0.5604978949995711}
**Error:** None

## solo_restar (basico)

**Reference:** Restá dos paquetes de arroz Gallo de 1 kg.

**Pi transcription:** resta, dos paquetes de arrroz gallo de un kilo

**Expected JSON:**
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

**Actual JSON:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Arroz Gallo 1kg","cantidad":2}]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 397.24609375, "ram_peak_mib": 399.24609375, "cpu_s": 598.69, "cpu_pct": 378.3081794396247, "request_wall_s": 158.2545745869993}
**PC resources:** {"ram_base_mib": 30.77734375, "ram_peak_mib": 30.78515625, "cpu_s": 0.010000000000000009, "cpu_pct": 2.2544964562207253, "request_wall_s": 0.44355802700010827}
**Error:** None

## restar_ambos (habitual)

**Reference:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Pi transcription:** restá, 2 Coca Cola Zero de 2 litros y 4 envases de detergente Magistral de 750 mililitros.

**Expected JSON:**
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

**Actual JSON:**
```json
{"operaciones":[{"operacion":"restar_stock","producto":"Coca Cola Zero 2L","cantidad":2},{"operacion":"restar_stock","producto":"Detergente Magistral 750ml","cantidad":4}]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 399.24609375, "ram_peak_mib": 399.99609375, "cpu_s": 610.5999999999999, "cpu_pct": 378.59832458588244, "request_wall_s": 161.27910779000013}
**PC resources:** {"ram_base_mib": 30.79296875, "ram_peak_mib": 30.80078125, "cpu_s": 0.010000000000000009, "cpu_pct": 1.4381024484378375, "request_wall_s": 0.6953607520008518}
**Error:** None

## corregir_cantidad (habitual)

**Reference:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Pi transcription:** Agrega, tres Coca Cola comunes de 2 litros, perdón, eran dos.

**Expected JSON:**
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

**Actual JSON:**
```json
{"operaciones":[{"operacion":"agregar_stock","producto":"Coca Cola 2L","cantidad":2}]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 399.99609375, "ram_peak_mib": 399.99609375, "cpu_s": 602.5699999999999, "cpu_pct": 378.549838625728, "request_wall_s": 159.17851192000126}
**PC resources:** {"ram_base_mib": 30.828125, "ram_peak_mib": 30.8359375, "cpu_s": 0.010000000000000009, "cpu_pct": 2.131737111322043, "request_wall_s": 0.46910099500018987}
**Error:** None

## negar_agregacion (habitual)

**Reference:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Pi transcription:** Agrega 5 botellas de agua Villavicencio de 1,5 litros, perdón, esas no llegaron, no las cargue.

**Expected JSON:**
```json
{
  "operaciones": []
}
```

**Actual JSON:**
```json
{"operaciones": []}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 399.99609375, "ram_peak_mib": 399.99609375, "cpu_s": 613.4100000000003, "cpu_pct": 377.535985761707, "request_wall_s": 162.4772268429988}
**PC resources:** {"ram_base_mib": 30.85546875, "ram_peak_mib": 30.859375, "cpu_s": 0.010000000000000009, "cpu_pct": 1.7865645213326777, "request_wall_s": 0.5597334930025681}
**Error:** None

## negar_restacion (habitual)

**Reference:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Pi transcription:** restá, 4 envases de detergentes magistral de 750 mililitros, perdón, no se vendieron, no los restes.

**Expected JSON:**
```json
{
  "operaciones": []
}
```

**Actual JSON:**
```json
{"operaciones": []}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 399.95703125, "ram_peak_mib": 402.58203125, "cpu_s": 613.2999999999997, "cpu_pct": 377.6448854452906, "request_wall_s": 162.40124615400055}
**PC resources:** {"ram_base_mib": 30.8828125, "ram_peak_mib": 30.890625, "cpu_s": 0.010000000000000009, "cpu_pct": 1.6874382325894615, "request_wall_s": 0.5926142839998647}
**Error:** None
