# Análisis STT por prompt

Repeticiones medidas agrupadas por configuración; calentamientos excluidos.
Los textos esperados vienen de los prompts y requieren revisión humana del audio.
WER estricto: números en palabras/dígitos, acentos y marcas cuentan como diferencias.
Las alineaciones explican diferencias textuales, no evalúan el significado.
Una alineación mínima puede tener otras alternativas igualmente válidas.

## WER medio por prompt (%)

| Prompt | whisper_small_q5_1 |
| --- | --- |
| solo_agregar | 18.75 |
| solo_restar | 33.33 |
| restar_ambos | 41.18 |
| corregir_cantidad | 27.27 |
| negar_agregacion | 29.41 |
| negar_restacion | 37.50 |
| negar_varias_agregaciones | 16.28 |
| negar_varias_restaciones | 27.03 |
| negar_agregacion_y_restacion | 22.86 |
| caso_integral | 28.24 |

## Casos con mayor WER por configuración

- **whisper_small_q5_1:** restar_ambos (41.18 %); negar_restacion (37.50 %); solo_restar (33.33 %)

## solo_agregar

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 18.75 % | 13.92 % | 18.75–18.75 % | 3.00 | 0.00 | 0.00 | 4.924 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `cuatro` → `4`


## solo_restar

**Texto esperado:**

> Restá dos paquetes de arroz Gallo de 1 kg.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 4.761 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta dos paquetes de arroz gallo de un kilo.

- **Sustituciones:** `restá` → `resta`; `1` → `un`; `kg` → `kilo`


## restar_ambos

**Texto esperado:**

> Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 41.18 % | 27.59 % | 41.18–41.18 % | 6.00 | 0.00 | 1.00 | 4.939 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta 2 Coca-Cola 0 de 2 litros y 4 en bases de detergente magistral de 750 mililitros.

- **Sustituciones:** `restá` → `resta`; `dos` → `2`; `zero` → `0`; `cuatro` → `en`; `envases` → `bases`; `ml` → `mililitros`
- **Agregados:** `4`


## corregir_cantidad

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 27.27 % | 14.04 % | 27.27–27.27 % | 3.00 | 0.00 | 0.00 | 4.949 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 3 Coca-Cola comunes de 2 litros, perdón eran 2.

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `dos` → `2`


## negar_agregacion

**Texto esperado:**

> Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 29.41 % | 13.54 % | 29.41–29.41 % | 3.00 | 0.00 | 2.00 | 5.079 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 5 botellas de agua billa de licencia de 1,5 litros. Perdón, esas no llegaron, no las cargues.

- **Sustituciones:** `agregá` → `agrega`; `cinco` → `5`; `villavicencio` → `licencia`
- **Agregados:** `billa`; `de`


## negar_restacion

**Texto esperado:**

> Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 37.50 % | 19.78 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 4.988 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta 4 en bases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

- **Sustituciones:** `restá` → `4`; `cuatro` → `en`; `envases` → `bases`; `detergente` → `detergentes`; `ml` → `mililitros`
- **Agregados:** `resta`


## negar_varias_agregaciones

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 16.28 % | 14.49 % | 16.28–16.28 % | 5.00 | 2.00 | 0.00 | 5.590 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  3 Coca-Cola comunes de 2 litros 4 Sprite comunes de 1,5 litros y 5 paquetes de arroz gallo de 1 kilo. Me equivoque, las Coca-Cola comunes de 2 litros y Sprite comunes de 1,5 no las cargués.

- **Sustituciones:** `tres` → `3`; `cuatro` → `4`; `cinco` → `5`; `kg` → `kilo`; `cargues` → `cargués`
- **Omisiones:** `agregá`; `las`


## negar_varias_restaciones

**Texto esperado:**

> Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 27.03 % | 21.23 % | 27.03–27.03 % | 9.00 | 0.00 | 1.00 | 5.295 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Prestar 2 Coca-Cola 0 de 2 litros, 3 paquetes de arroz gallo de 1 kilo y 4 en base de detergente magistral de 750 mililitros. Las Coca-0 y el arroz no se vendieron, no los restes.

- **Sustituciones:** `restá` → `prestar`; `dos` → `2`; `zero` → `0`; `tres` → `3`; `kg` → `kilo`; `cuatro` → `en`; `envases` → `base`; `ml` → `mililitros`; `zero` → `0`
- **Agregados:** `4`


## negar_agregacion_y_restacion

**Texto esperado:**

> Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 22.86 % | 12.85 % | 22.86–22.86 % | 8.00 | 0.00 | 0.00 | 5.367 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 4 spray comunes de 2 litros y resta 2 paquetes de arroz gallo de 1 kilo. Perdón, las spray no llegaron y el arroz no se vendió, no hagas ninguna de esas 2 operaciones.

- **Sustituciones:** `agregá` → `agrega`; `cuatro` → `4`; `sprite` → `spray`; `restá` → `resta`; `dos` → `2`; `kg` → `kilo`; `sprite` → `spray`; `dos` → `2`


## caso_integral

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| whisper_small_q5_1 | 28.24 % | 16.64 % | 28.24–28.24 % | 27.00 | 7.00 | 3.00 | 12.774 s |

Los conteos de la tabla son promedios de las repeticiones.

### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  3 Coca-Cola comunes de 2 litros, 4 Sprite comunes de 1,5 litros y 5 botellas de agua viva visencio de 1,5 litros. No llegó ninguno de esos 2 productos, así que no los cargués. Resta 2 paquetes de arroz gallo de 1 kilo y 3 paquetes de fideos matarazos de 500 gramos. Resta 4 Coca-Cola 0 de 2 litros y 5 en bases de detergente magistral de 750 ml. Perdón, ni las Coca-cero ni los detergentes se vendieron, no restes ninguno de esos 2 productos. Agrega 6 en bases de leche lazerenísima de 1 litro y resta 2 Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron. No cargués la leche ni restes esa Sprite.

- **Sustituciones:** `tres` → `3`; `cuatro` → `4`; `cinco` → `5`; `villavicencio` → `visencio`; `dos` → `2`; `cargues` → `cargués`; `restá` → `resta`; `dos` → `2`; `kg` → `kilo`; `tres` → `3`; `matarazzo` → `matarazos`; `g` → `gramos`; `restá` → `resta`; `cuatro` → `4`; `zero` → `0`; `cinco` → `en`; `envases` → `bases`; `zero` → `cero`; `dos` → `2`; `agregá` → `6`; `seis` → `en`; `envases` → `bases`; `serenísima` → `lazerenísima`; `restá` → `resta`; `dos` → `2`; `cargues` → `cargués`; `esas` → `esa`
- **Omisiones:** `agregá`; `perdón`; `eran`; `dos`; `agregá`; `perdón`; `la`
- **Agregados:** `viva`; `5`; `agrega`
