# Raspberry STT → SSH → PC Groq integration

Whisper Small Q5_1 on remote host → openai/gpt-oss-20b from PC.
Exact JSON: 5/6 processed; six expected cases.
One transcription and one API request per case; no warm-up or retries.
Pi STT resources cover the Whisper process; PC resources cover the Python coordinator.
Remote Groq model RAM is not observable. References require human audio verification.
SSH/scp configuration and host hardware are recorded in environment.json.
No microphone capture or inventory updates occur in this fixture experiment.

## solo_agregar (basico)

**Reference:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Pi transcription:** Agrega 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

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
**Pi resources:** {"ram_base_mib": 277.625, "ram_peak_mib": 343.1640625, "cpu_s": 541.2400000000001, "cpu_pct": 371.11514737662986, "request_wall_s": 145.84152757599986}
**PC resources:** {"ram_base_mib": 27.6875, "ram_peak_mib": 30.59375, "cpu_s": 0.030000000000000027, "cpu_pct": 5.081805378466599, "request_wall_s": 0.5903413799969712}
**Error:** None

## solo_restar (basico)

**Reference:** Restá dos paquetes de arroz Gallo de 1 kg.

**Pi transcription:** Resta dos paquetes de arroz gallo de un kilo.

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
**Pi resources:** {"ram_base_mib": 342.65625, "ram_peak_mib": 344.65625, "cpu_s": 532.5499999999998, "cpu_pct": 367.76230742096175, "request_wall_s": 144.80820607600026}
**PC resources:** {"ram_base_mib": 30.609375, "ram_peak_mib": 30.6171875, "cpu_s": 0.010000000000000009, "cpu_pct": 2.4560322578720157, "request_wall_s": 0.40716077600154676}
**Error:** None

## restar_ambos (habitual)

**Reference:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Pi transcription:** Resta 2 Coca-Cola 0 de 2 litros y 4 en bases de detergente magistral de 750 mililitros.

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
{"operaciones":[{"operacion":"restar_stock","producto":"Detergente Magistral 750ml","cantidad":4}]}
```

**Evaluation:** {"valid_json": true, "schema_valid": true, "correct_operation": false, "correct_product": false, "correct_quantity": false, "exact_match": false}
**Pi resources:** {"ram_base_mib": 344.65625, "ram_peak_mib": 345.15625, "cpu_s": 542.2, "cpu_pct": 376.8264975368694, "request_wall_s": 143.88584760999993}
**PC resources:** {"ram_base_mib": 30.62109375, "ram_peak_mib": 30.62890625, "cpu_s": 0.019999999999999962, "cpu_pct": 2.792166700843052, "request_wall_s": 0.7162896110021393}
**Error:** None

## corregir_cantidad (habitual)

**Reference:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Pi transcription:** Agrega 3 Coca-Cola comunes de 2 litros, perdón eran 2.

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
**Pi resources:** {"ram_base_mib": 345.15625, "ram_peak_mib": 345.15625, "cpu_s": 535.7299999999998, "cpu_pct": 377.2671020670565, "request_wall_s": 142.00284018000002}
**PC resources:** {"ram_base_mib": 30.6328125, "ram_peak_mib": 30.640625, "cpu_s": 0.020000000000000018, "cpu_pct": 3.9770847377269396, "request_wall_s": 0.5028809119976358}
**Error:** None

## negar_agregacion (habitual)

**Reference:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Pi transcription:** Agrega 5 botellas de agua billa de licencia de 1,5 litros. Perdón, esas no llegaron, no las cargues.

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
**Pi resources:** {"ram_base_mib": 345.15625, "ram_peak_mib": 347.53125, "cpu_s": 550.48, "cpu_pct": 375.5530658611811, "request_wall_s": 146.5784865149999}
**PC resources:** {"ram_base_mib": 30.671875, "ram_peak_mib": 30.6796875, "cpu_s": 0.010000000000000009, "cpu_pct": 1.912973308068067, "request_wall_s": 0.5227464470008272}
**Error:** None

## negar_restacion (habitual)

**Reference:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Pi transcription:** Resta 4 en bases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

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
**Pi resources:** {"ram_base_mib": 344.40234375, "ram_peak_mib": 347.15234375, "cpu_s": 547.0200000000004, "cpu_pct": 375.7450423294063, "request_wall_s": 145.5827591520001}
**PC resources:** {"ram_base_mib": 30.703125, "ram_peak_mib": 30.70703125, "cpu_s": 0.010000000000000009, "cpu_pct": 1.5006949658375708, "request_wall_s": 0.6663579359992582}
**Error:** None
