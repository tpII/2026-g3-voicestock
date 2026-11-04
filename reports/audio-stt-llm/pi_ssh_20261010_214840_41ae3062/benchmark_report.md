# Raspberry STT → SSH → PC Groq integration

Whisper ggml-base.bin on remote host → openai/gpt-oss-20b from PC.
Exact JSON: 5/6 processed; six expected cases.
One transcription and one API request per case; no warm-up or retries.
Pi STT resources cover the Whisper process; PC resources cover the Python coordinator.
Remote Groq model RAM is not observable. References require human audio verification.
SSH/scp configuration and host hardware are recorded in environment.json.
No microphone capture or inventory updates occur in this fixture experiment.

## Summary

Exact JSON success: 5/6 (83.3%).
Processed: 6/6; execution errors: 0.

basico: 2/2 exact (100.0%).

habitual: 3/4 exact (75.0%).

| Case | Exact JSON | Pi STT (s) | LLM API (s) | Whisper peak RAM (MiB) |
|---|---|---:|---:|---:|
| solo_agregar | True | 47.982 | 0.666 | 289.730 |
| solo_restar | True | 45.127 | 0.915 | 291.219 |
| restar_ambos | False | 46.860 | 0.607 | 291.719 |
| corregir_cantidad | True | 46.565 | 0.519 | 291.719 |
| negar_agregacion | True | 48.401 | 1.159 | 293.055 |
| negar_restacion | True | 47.960 | 0.532 | 293.895 |

### Resources and audio duration

| Case | Audio (s) | Pi CPU (%) | PC client RAM (MiB) | STT + API (s) |
|---|---:|---:|---:|---:|
| solo_agregar | 8.576 | 364.264 | 30.754 | 48.648 |
| solo_restar | 4.992 | 375.626 | 30.773 | 46.042 |
| restar_ambos | 8.448 | 374.094 | 30.789 | 47.467 |
| corregir_cantidad | 8.064 | 369.076 | 30.816 | 47.084 |
| negar_agregacion | 9.664 | 367.991 | 30.836 | 49.559 |
| negar_restacion | 11.072 | 370.539 | 30.883 | 48.492 |

CPU: 100% represents one logical core. PC RAM is the API client, not the model hosted by Groq.

### Overall metrics

| Metric | Value |
|---|---:|
| Exact JSON success | 5/6 (83.3%) |
| Initial model load (s) | 1.785 |
| Pi STT mean (s) | 47.149 |
| Pi STT min–max (s) | 45.127–48.401 |
| LLM API mean (s) | 0.733 |
| LLM API min–max (s) | 0.519–1.159 |
| Whisper peak RAM (MiB) | 293.895 |
| PC client peak RAM (MiB) | 30.883 |

Pi STT: mean 47.149 s; range 45.127–48.401 s; sum 282.894 s (6 measurements).

LLM API: mean 0.733 s; range 0.519–1.159 s; sum 4.399 s (6 measurements).

Initial model load: 1.785 s.

Whisper maximum sampled RSS: 293.89 MiB.

Pi STT includes WAV reading/conversion and inference. LLM API includes network and response handling. Stage sums exclude SSH transfers, model load and orchestration; they are not total run duration.

## solo_agregar (basico)

**Reference:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Pi transcription:** agregá, 3 Coca Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

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
**Pi resources:** {"ram_base_mib": 187.75, "ram_peak_mib": 289.73046875, "cpu_s": 174.78, "cpu_pct": 364.2640217281558, "request_wall_s": 47.9816807520001}
**PC resources:** {"ram_base_mib": 27.79296875, "ram_peak_mib": 30.75390625, "cpu_s": 0.03999999999999998, "cpu_pct": 6.003072630703992, "request_wall_s": 0.6663254380000581}
**Error:** None

## solo_restar (basico)

**Reference:** Restá dos paquetes de arroz Gallo de 1 kg.

**Pi transcription:** Restá, dos paquetes de arroz gallo de un kilo.

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
**Pi resources:** {"ram_base_mib": 289.21875, "ram_peak_mib": 291.21875, "cpu_s": 169.51000000000005, "cpu_pct": 375.6258923214622, "request_wall_s": 45.12734703999922}
**PC resources:** {"ram_base_mib": 30.765625, "ram_peak_mib": 30.7734375, "cpu_s": 0.020000000000000018, "cpu_pct": 2.1859230344837806, "request_wall_s": 0.9149452969977574}
**Error:** None

## restar_ambos (habitual)

**Reference:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Pi transcription:** Restá, toco Coca Cola Zero de 2 litros y 4 envases de detergente Magistral de 750 mililitros.

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
{"operaciones":[{"operacion":"restar_stock","producto":"Coca Cola Zero 2L","cantidad":1},{"operacion":"restar_stock","producto":"Detergente Magistral 750ml","cantidad":4}]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": false, "exact_match": false}
**Pi resources:** {"ram_base_mib": 291.21875, "ram_peak_mib": 291.71875, "cpu_s": 175.29999999999995, "cpu_pct": 374.0940313827603, "request_wall_s": 46.85987620600099}
**PC resources:** {"ram_base_mib": 30.77734375, "ram_peak_mib": 30.7890625, "cpu_s": 0.010000000000000009, "cpu_pct": 1.646154950444018, "request_wall_s": 0.6074762280004506}
**Error:** None

## corregir_cantidad (habitual)

**Reference:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Pi transcription:** Agrega, 3 Coca Cola Comunes de 2 litros, perdón, eran 2.

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
**Pi resources:** {"ram_base_mib": 291.71875, "ram_peak_mib": 291.71875, "cpu_s": 171.86, "cpu_pct": 369.0757149898578, "request_wall_s": 46.5649710939997}
**PC resources:** {"ram_base_mib": 30.80859375, "ram_peak_mib": 30.81640625, "cpu_s": 0.010000000000000009, "cpu_pct": 1.9276161625871115, "request_wall_s": 0.5187754799990216}
**Error:** None

## negar_agregacion (habitual)

**Reference:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Pi transcription:** Agrega, 5 botellas de agua Villavicencio de 1,5 litros, perdón, esas no llegaron, no las carguez.

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
**Pi resources:** {"ram_base_mib": 291.71875, "ram_peak_mib": 293.0546875, "cpu_s": 178.11, "cpu_pct": 367.9907897770037, "request_wall_s": 48.400667883001006}
**PC resources:** {"ram_base_mib": 30.83203125, "ram_peak_mib": 30.8359375, "cpu_s": 0.020000000000000018, "cpu_pct": 1.7262058914687282, "request_wall_s": 1.158610342998145}
**Error:** None

## negar_restacion (habitual)

**Reference:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Pi transcription:** Restá, 4 envases de detergentes Magistral de 750 mililitros, perdón, no se vendieron, no los restes.

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
**Pi resources:** {"ram_base_mib": 291.01953125, "ram_peak_mib": 293.89453125, "cpu_s": 177.71000000000004, "cpu_pct": 370.5387550464366, "request_wall_s": 47.95989557900066}
**PC resources:** {"ram_base_mib": 30.875, "ram_peak_mib": 30.8828125, "cpu_s": 0.010000000000000009, "cpu_pct": 1.8781916709823805, "request_wall_s": 0.5324270229975809}
**Error:** None
