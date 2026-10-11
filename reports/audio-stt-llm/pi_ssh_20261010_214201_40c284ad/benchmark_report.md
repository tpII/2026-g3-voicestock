# Raspberry STT → SSH → PC Groq integration

Whisper ggml-tiny.bin on remote host → openai/gpt-oss-20b from PC.
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
| solo_agregar | True | 21.713 | 0.663 | 199.652 |
| solo_restar | True | 21.157 | 0.609 | 201.242 |
| restar_ambos | True | 21.701 | 0.504 | 201.867 |
| corregir_cantidad | True | 21.272 | 0.575 | 201.867 |
| negar_agregacion | True | 22.014 | 0.441 | 201.867 |
| negar_restacion | True | 22.343 | 0.508 | 204.359 |

### Resources and audio duration

| Case | Audio (s) | Pi CPU (%) | PC client RAM (MiB) | STT + API (s) |
|---|---:|---:|---:|---:|
| solo_agregar | 8.576 | 370.014 | 30.898 | 22.376 |
| solo_restar | 4.992 | 362.619 | 30.918 | 21.766 |
| restar_ambos | 8.448 | 366.665 | 30.930 | 22.205 |
| corregir_cantidad | 8.064 | 365.832 | 30.965 | 21.847 |
| negar_agregacion | 9.664 | 365.638 | 30.984 | 22.454 |
| negar_restacion | 11.072 | 361.320 | 31.012 | 22.851 |

CPU: 100% represents one logical core. PC RAM is the API client, not the model hosted by Groq.

### Overall metrics

| Metric | Value |
|---|---:|
| Exact JSON success | 6/6 (100.0%) |
| Initial model load (s) | 0.766 |
| Pi STT mean (s) | 21.700 |
| Pi STT min–max (s) | 21.157–22.343 |
| LLM API mean (s) | 0.550 |
| LLM API min–max (s) | 0.441–0.663 |
| Whisper peak RAM (MiB) | 204.359 |
| PC client peak RAM (MiB) | 31.012 |

Pi STT: mean 21.700 s; range 21.157–22.343 s; sum 130.200 s (6 measurements).

LLM API: mean 0.550 s; range 0.441–0.663 s; sum 3.299 s (6 measurements).

Initial model load: 0.766 s.

Whisper maximum sampled RSS: 204.36 MiB.

Pi STT includes WAV reading/conversion and inference. LLM API includes network and response handling. Stage sums exclude SSH transfers, model load and orchestration; they are not total run duration.

## solo_agregar (basico)

**Reference:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Pi transcription:** agrega 3 Coca Cola Comunes de 2 litros y 4 Sprite Comunes de 1,5 litros.

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
**Pi resources:** {"ram_base_mib": 107.875, "ram_peak_mib": 199.65234375, "cpu_s": 80.34, "cpu_pct": 370.01395550832547, "request_wall_s": 21.712694563000696}
**PC resources:** {"ram_base_mib": 27.9921875, "ram_peak_mib": 30.8984375, "cpu_s": 0.03, "cpu_pct": 4.524267510388044, "request_wall_s": 0.6630907639992074}
**Error:** None

## solo_restar (basico)

**Reference:** Restá dos paquetes de arroz Gallo de 1 kg.

**Pi transcription:** restá, 2 paquetes de arroz gashos de 1 kilo.

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
**Pi resources:** {"ram_base_mib": 199.2421875, "ram_peak_mib": 201.2421875, "cpu_s": 76.72000000000001, "cpu_pct": 362.61920002261746, "request_wall_s": 21.157180864999646}
**PC resources:** {"ram_base_mib": 30.91015625, "ram_peak_mib": 30.91796875, "cpu_s": 0.0, "cpu_pct": 0.0, "request_wall_s": 0.6089204640011303}
**Error:** None

## restar_ambos (habitual)

**Reference:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Pi transcription:** restá, Coca Cola Zero de dos litros y cuatro envases de detergente Magistral de 750 mililitros.

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
**Pi resources:** {"ram_base_mib": 201.2421875, "ram_peak_mib": 201.8671875, "cpu_s": 79.57, "cpu_pct": 366.6650368312778, "request_wall_s": 21.701005552000424}
**PC resources:** {"ram_base_mib": 30.921875, "ram_peak_mib": 30.9296875, "cpu_s": 0.009999999999999981, "cpu_pct": 1.9850870257743902, "request_wall_s": 0.5037562520010397}
**Error:** None

## corregir_cantidad (habitual)

**Reference:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Pi transcription:** agríate, trisco Coca Cola con 1 de 2 litros perdón, eran 2.

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
**Pi resources:** {"ram_base_mib": 201.8671875, "ram_peak_mib": 201.8671875, "cpu_s": 77.82000000000002, "cpu_pct": 365.83208904855394, "request_wall_s": 21.27205412799958}
**PC resources:** {"ram_base_mib": 30.95703125, "ram_peak_mib": 30.96484375, "cpu_s": 0.010000000000000009, "cpu_pct": 1.7401850868184146, "request_wall_s": 0.5746515169994382}
**Error:** None

## negar_agregacion (habitual)

**Reference:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Pi transcription:** agrega 5 tillas de agua Villavicencio de 1,5 litros, perdón, esas no llegaron a las cargos.

**Expected JSON:**
```json
{
  "operaciones": []
}
```

**Actual JSON:**
```json
{"operaciones":[]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 201.8671875, "ram_peak_mib": 201.8671875, "cpu_s": 80.48999999999995, "cpu_pct": 365.63847756860355, "request_wall_s": 22.013547517000006}
**PC resources:** {"ram_base_mib": 30.9765625, "ram_peak_mib": 30.984375, "cpu_s": 0.020000000000000018, "cpu_pct": 4.539458251243289, "request_wall_s": 0.44058120800036704}
**Error:** None

## negar_restacion (habitual)

**Reference:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Pi transcription:** restá 4 envases de detergentes magistral de 750 mililitros, perdón, no se vendieron, no los restes.

**Expected JSON:**
```json
{
  "operaciones": []
}
```

**Actual JSON:**
```json
{"operaciones":[]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": true, "correct_product": true, "correct_quantity": true, "exact_match": true}
**Pi resources:** {"ram_base_mib": 201.859375, "ram_peak_mib": 204.359375, "cpu_s": 80.73000000000002, "cpu_pct": 361.32046616272146, "request_wall_s": 22.34304656400036}
**PC resources:** {"ram_base_mib": 31.00390625, "ram_peak_mib": 31.01171875, "cpu_s": 0.0, "cpu_pct": 0.0, "request_wall_s": 0.508101274001092}
**Error:** None
