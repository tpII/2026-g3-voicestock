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

| Case | Exact JSON | Pi STT (s) | LLM API (s) | Whisper peak RAM (MiB) |
|---|---|---:|---:|---:|
| solo_agregar | True | 42.947 | 0.701 | 254.660 |
| solo_restar | True | 41.711 | 0.442 | 256.277 |
| restar_ambos | False | 42.806 | 0.689 | 257.027 |
| corregir_cantidad | True | 42.369 | 0.541 | 257.027 |
| negar_agregacion | True | 44.158 | 0.447 | 259.402 |
| negar_restacion | True | 43.817 | 1.023 | 258.289 |

Pi STT: mean 42.968 s; range 41.711–44.158 s; sum 257.808 s (6 measurements).

LLM API: mean 0.640 s; range 0.442–1.023 s; sum 3.843 s (6 measurements).

Initial model load: 0.898 s.

Whisper maximum sampled RSS: 259.40 MiB.

Pi STT includes WAV reading/conversion and inference. LLM API includes network and response handling. Stage sums exclude SSH transfers, model load and orchestration; they are not total run duration.

## solo_agregar (basico)

**Reference:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Pi transcription:** Agrega 3 Coca Cola Comunes de 2 litros y 4 Sprite Comunes de 1,5 litros.

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
**Pi resources:** {"ram_base_mib": 187.875, "ram_peak_mib": 254.66015625, "cpu_s": 161.39, "cpu_pct": 375.7871249249821, "request_wall_s": 42.947187196000414}
**PC resources:** {"ram_base_mib": 27.796875, "ram_peak_mib": 30.79296875, "cpu_s": 0.030000000000000027, "cpu_pct": 4.280426228802111, "request_wall_s": 0.7008647830007249}
**Error:** None

## solo_restar (basico)

**Reference:** Restá dos paquetes de arroz Gallo de 1 kg.

**Pi transcription:** Restá, 2 paquetes de arroz gallo de 1 kilo.

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
**Pi resources:** {"ram_base_mib": 254.27734375, "ram_peak_mib": 256.27734375, "cpu_s": 155.62000000000003, "cpu_pct": 373.08755008065884, "request_wall_s": 41.711389180999504}
**PC resources:** {"ram_base_mib": 30.8046875, "ram_peak_mib": 30.8125, "cpu_s": 0.019999999999999962, "cpu_pct": 4.528174947533972, "request_wall_s": 0.44167904799905955}
**Error:** None

## restar_ambos (habitual)

**Reference:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Pi transcription:** Resta, toco Coca Cola Zero de 2 litros y 4 envases de detergente Magistral de 750 ml.

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
**Pi resources:** {"ram_base_mib": 256.27734375, "ram_peak_mib": 257.02734375, "cpu_s": 160.53999999999996, "cpu_pct": 375.0418946080299, "request_wall_s": 42.80588443800025}
**PC resources:** {"ram_base_mib": 30.8125, "ram_peak_mib": 30.8203125, "cpu_s": 0.010000000000000009, "cpu_pct": 1.450849936108897, "request_wall_s": 0.6892511590012873}
**Error:** None

## corregir_cantidad (habitual)

**Reference:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Pi transcription:** Agrega, 3 Coca Cola Comunes de 2 Litros, perdón, eran 2.

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
**Pi resources:** {"ram_base_mib": 257.02734375, "ram_peak_mib": 257.02734375, "cpu_s": 157.56, "cpu_pct": 371.8751947472468, "request_wall_s": 42.36905344199931}
**PC resources:** {"ram_base_mib": 30.83203125, "ram_peak_mib": 30.83984375, "cpu_s": 0.009999999999999953, "cpu_pct": 1.8475278907381216, "request_wall_s": 0.541263817998697}
**Error:** None

## negar_agregacion (habitual)

**Reference:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Pi transcription:** Agrega 5 tellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron las cargues.

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
**Pi resources:** {"ram_base_mib": 257.02734375, "ram_peak_mib": 259.40234375, "cpu_s": 163.80000000000007, "cpu_pct": 370.9414847751281, "request_wall_s": 44.1579081130003}
**PC resources:** {"ram_base_mib": 30.8671875, "ram_peak_mib": 30.87109375, "cpu_s": 0.020000000000000018, "cpu_pct": 4.473991599657695, "request_wall_s": 0.4470281079993583}
**Error:** None

## negar_restacion (habitual)

**Reference:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Pi transcription:** Restá 4 envases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

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
**Pi resources:** {"ram_base_mib": 255.9140625, "ram_peak_mib": 258.2890625, "cpu_s": 162.55999999999995, "cpu_pct": 370.9974342805906, "request_wall_s": 43.81701461499961}
**PC resources:** {"ram_base_mib": 30.8984375, "ram_peak_mib": 30.90625, "cpu_s": 0.010000000000000009, "cpu_pct": 0.9779116886570124, "request_wall_s": 1.022587225001189}
**Error:** None
