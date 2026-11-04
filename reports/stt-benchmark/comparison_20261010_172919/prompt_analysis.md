# Análisis STT por prompt

Repeticiones medidas agrupadas por configuración; calentamientos excluidos.
Los textos esperados vienen de los prompts y requieren revisión humana del audio.
WER estricto: números en palabras/dígitos, acentos y marcas cuentan como diferencias.
Las alineaciones explican diferencias textuales, no evalúan el significado.
Una alineación mínima puede tener otras alternativas igualmente válidas.

## WER medio por prompt (%)

| Prompt | vosk_full | vosk_250ms | whisper_tiny | whisper_base | whisper_small_q5_1 | moonshine_tiny_es | moonshine_small_es |
| --- | --- | --- | --- | --- | --- | --- | --- |
| solo_agregar | 37.50 | 37.50 | 18.75 | 18.75 | 18.75 | 37.50 | 37.50 |
| solo_restar | 33.33 | 33.33 | 44.44 | 33.33 | 33.33 | 33.33 | 33.33 |
| restar_ambos | 39.22 | 39.22 | 29.41 | 41.18 | 41.18 | 52.94 | 35.29 |
| corregir_cantidad | 30.30 | 27.27 | 54.55 | 27.27 | 27.27 | 18.18 | 18.18 |
| negar_agregacion | 41.18 | 41.18 | 35.29 | 29.41 | 29.41 | 29.41 | 35.29 |
| negar_restacion | 50.00 | 50.00 | 50.00 | 18.75 | 37.50 | 18.75 | 31.25 |
| negar_varias_agregaciones | 41.86 | 44.19 | 27.91 | 32.56 | 16.28 | 34.88 | 27.91 |
| negar_varias_restaciones | 37.84 | 37.84 | 51.35 | 32.43 | 27.03 | 35.14 | 27.03 |
| negar_agregacion_y_restacion | 28.57 | 28.57 | 25.71 | 25.71 | 22.86 | 28.57 | 22.86 |
| caso_integral | 37.91 | 38.17 | 52.67 | 34.35 | 28.24 | 31.30 | 25.95 |

## Casos con mayor WER por configuración

- **vosk_full:** negar_restacion (50.00 %); negar_varias_agregaciones (41.86 %); negar_agregacion (41.18 %)
- **vosk_250ms:** negar_restacion (50.00 %); negar_varias_agregaciones (44.19 %); negar_agregacion (41.18 %)
- **whisper_tiny:** corregir_cantidad (54.55 %); caso_integral (52.67 %); negar_varias_restaciones (51.35 %)
- **whisper_base:** restar_ambos (41.18 %); caso_integral (34.35 %); solo_restar (33.33 %)
- **whisper_small_q5_1:** restar_ambos (41.18 %); negar_restacion (37.50 %); solo_restar (33.33 %)
- **moonshine_tiny_es:** restar_ambos (52.94 %); solo_agregar (37.50 %); negar_varias_restaciones (35.14 %)
- **moonshine_small_es:** solo_agregar (37.50 %); restar_ambos (35.29 %); negar_agregacion (35.29 %)

## solo_agregar

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 37.50 % | 25.32 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 0.716 s |
| vosk_250ms | 37.50 % | 25.32 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 0.708 s |
| whisper_tiny | 18.75 % | 13.92 % | 18.75–18.75 % | 3.00 | 0.00 | 0.00 | 0.545 s |
| whisper_base | 18.75 % | 13.92 % | 18.75–18.75 % | 3.00 | 0.00 | 0.00 | 1.173 s |
| whisper_small_q5_1 | 18.75 % | 13.92 % | 18.75–18.75 % | 3.00 | 0.00 | 0.00 | 4.924 s |
| moonshine_tiny_es | 37.50 % | 25.32 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 0.634 s |
| moonshine_small_es | 37.50 % | 25.32 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 1.274 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca-cola comunes de dos litros y cuatro spray comunes de uno coma cinco litros

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca-cola comunes de dos litros y cuatro spray comunes de uno coma cinco litros

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  agrega 3 Coca-Cola comunes de 2 litros y 4 sprite comunes de 1,5 litros

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `cuatro` → `4`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 3 Coca-Cola comunes de 2 litros y 4 sprite comunes de 1,5 litros.

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `cuatro` → `4`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 3 Coca-Cola comunes de 2 litros y 4 Sprite comunes de 1,5 litros.

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `cuatro` → `4`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros y cuatro pryt comunes de uno coma cinco litros

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `pryt`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros y cuatro sprays comunes de uno coma cinco litros

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `sprays`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`


## solo_restar

**Texto esperado:**

> Restá dos paquetes de arroz Gallo de 1 kg.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 0.404 s |
| vosk_250ms | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 0.410 s |
| whisper_tiny | 44.44 % | 31.71 % | 44.44–44.44 % | 4.00 | 0.00 | 0.00 | 0.518 s |
| whisper_base | 33.33 % | 17.07 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 1.080 s |
| whisper_small_q5_1 | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 4.761 s |
| moonshine_tiny_es | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 0.233 s |
| moonshine_small_es | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 0.562 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> resta dos paquetes de arroz gallo de un kilo

- **Sustituciones:** `restá` → `resta`; `1` → `un`; `kg` → `kilo`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> resta dos paquetes de arroz gallo de un kilo

- **Sustituciones:** `restá` → `resta`; `1` → `un`; `kg` → `kilo`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Prega 2 paquetes de arroz gashos de 1 kilo

- **Sustituciones:** `restá` → `prega`; `dos` → `2`; `gallo` → `gashos`; `kg` → `kilo`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  resta 2 paquetes de arroz gallo de 1 kilo

- **Sustituciones:** `restá` → `resta`; `dos` → `2`; `kg` → `kilo`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta dos paquetes de arroz gallo de un kilo.

- **Sustituciones:** `restá` → `resta`; `1` → `un`; `kg` → `kilo`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> resta dos paquetes de arroz gallo de un kilo

- **Sustituciones:** `restá` → `resta`; `1` → `un`; `kg` → `kilo`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> resta dos paquetes de arroz gallo de un kilo

- **Sustituciones:** `restá` → `resta`; `1` → `un`; `kg` → `kilo`


## restar_ambos

**Texto esperado:**

> Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 39.22 % | 43.30 % | 35.29–41.18 % | 5.00 | 0.67 | 1.00 | 0.679 s |
| vosk_250ms | 39.22 % | 42.53 % | 35.29–41.18 % | 5.33 | 0.33 | 1.00 | 0.689 s |
| whisper_tiny | 29.41 % | 17.24 % | 29.41–29.41 % | 4.00 | 0.00 | 1.00 | 0.534 s |
| whisper_base | 41.18 % | 20.69 % | 41.18–41.18 % | 7.00 | 0.00 | 0.00 | 1.230 s |
| whisper_small_q5_1 | 41.18 % | 27.59 % | 41.18–41.18 % | 6.00 | 0.00 | 1.00 | 4.939 s |
| moonshine_tiny_es | 52.94 % | 43.68 % | 52.94–52.94 % | 7.00 | 1.00 | 1.00 | 0.451 s |
| moonshine_small_es | 35.29 % | 39.08 % | 35.29–35.29 % | 5.00 | 0.00 | 1.00 | 1.233 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1 — estado: ok**

> resta dos coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `restá` → `resta`; `zero` → `serio`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `setecientos`

**Repeticiones 2, 3 — estado: ok**

> resta coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `dos` → `resta`; `zero` → `serio`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Omisiones:** `restá`
- **Agregados:** `setecientos`


### vosk_250ms

**Repeticiones 1 — estado: ok**

> resta dos coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `restá` → `resta`; `zero` → `serio`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `setecientos`

**Repeticiones 2 — estado: ok**

> resta coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `dos` → `resta`; `zero` → `serio`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Omisiones:** `restá`
- **Agregados:** `setecientos`

**Repeticiones 3 — estado: ok**

> resta tus coca cola serio de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `restá` → `resta`; `dos` → `tus`; `zero` → `serio`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `setecientos`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Restar 2 Coca-Cola a 0 de 2 litros y 4 envases de detergente magistral de 750 ml.

- **Sustituciones:** `restá` → `restar`; `dos` → `2`; `zero` → `0`; `cuatro` → `4`
- **Agregados:** `a`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta, toco cacola a 0 de 2 litros y 4 embases de detergente magistral de 750 ml.

- **Sustituciones:** `restá` → `resta`; `dos` → `toco`; `coca` → `cacola`; `cola` → `a`; `zero` → `0`; `cuatro` → `4`; `envases` → `embases`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta 2 Coca-Cola 0 de 2 litros y 4 en bases de detergente magistral de 750 mililitros.

- **Sustituciones:** `restá` → `resta`; `dos` → `2`; `zero` → `0`; `cuatro` → `en`; `envases` → `bases`; `ml` → `mililitros`
- **Agregados:** `4`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> resta tosco cacola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `dos` → `resta`; `coca` → `tosco`; `cola` → `cacola`; `zero` → `cero`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Omisiones:** `restá`
- **Agregados:** `setecientos`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> resta dos coca cola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `setecientos`


## corregir_cantidad

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 30.30 % | 13.45 % | 27.27–36.36 % | 2.67 | 0.00 | 0.67 | 0.551 s |
| vosk_250ms | 27.27 % | 10.53 % | 27.27–27.27 % | 2.00 | 0.00 | 1.00 | 0.557 s |
| whisper_tiny | 54.55 % | 22.81 % | 54.55–54.55 % | 6.00 | 0.00 | 0.00 | 0.520 s |
| whisper_base | 27.27 % | 14.04 % | 27.27–27.27 % | 3.00 | 0.00 | 0.00 | 1.155 s |
| whisper_small_q5_1 | 27.27 % | 14.04 % | 27.27–27.27 % | 3.00 | 0.00 | 0.00 | 4.949 s |
| moonshine_tiny_es | 18.18 % | 8.77 % | 18.18–18.18 % | 2.00 | 0.00 | 0.00 | 0.612 s |
| moonshine_small_es | 18.18 % | 7.02 % | 18.18–18.18 % | 2.00 | 0.00 | 0.00 | 1.216 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2 — estado: ok**

> a great tres coca cola comunes de dos litros perdón eran dos

- **Sustituciones:** `agregá` → `great`; `2` → `dos`
- **Agregados:** `a`

**Repeticiones 3 — estado: ok**

> a great tres cola comunes de dos litros perdón eran dos

- **Sustituciones:** `agregá` → `a`; `tres` → `great`; `coca` → `tres`; `2` → `dos`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> a great tres coca cola comunes de dos litros perdón eran dos

- **Sustituciones:** `agregá` → `great`; `2` → `dos`
- **Agregados:** `a`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Agree, 3 cocacó la comune de 2 litros perdón, eran 2.

- **Sustituciones:** `agregá` → `agree`; `tres` → `3`; `coca` → `cocacó`; `cola` → `la`; `comunes` → `comune`; `dos` → `2`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega, 3 coca-cola comunes de 2 litros, perdón, eran 2.

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `dos` → `2`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 3 Coca-Cola comunes de 2 litros, perdón eran 2.

- **Sustituciones:** `agregá` → `agrega`; `tres` → `3`; `dos` → `2`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> agregad tres coca cola comunes de dos litros perdón eran dos

- **Sustituciones:** `agregá` → `agregad`; `2` → `dos`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros perdón eran dos

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`


## negar_agregacion

**Texto esperado:**

> Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 41.18 % | 18.75 % | 41.18–41.18 % | 5.00 | 0.00 | 2.00 | 0.857 s |
| vosk_250ms | 41.18 % | 18.75 % | 41.18–41.18 % | 5.00 | 0.00 | 2.00 | 0.854 s |
| whisper_tiny | 35.29 % | 25.00 % | 35.29–35.29 % | 5.00 | 1.00 | 0.00 | 0.569 s |
| whisper_base | 29.41 % | 17.71 % | 29.41–29.41 % | 4.00 | 1.00 | 0.00 | 1.221 s |
| whisper_small_q5_1 | 29.41 % | 13.54 % | 29.41–29.41 % | 3.00 | 0.00 | 2.00 | 5.079 s |
| moonshine_tiny_es | 29.41 % | 18.75 % | 29.41–29.41 % | 4.00 | 0.00 | 1.00 | 0.626 s |
| moonshine_small_es | 35.29 % | 20.83 % | 35.29–35.29 % | 4.00 | 0.00 | 2.00 | 1.862 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cinco botellas de agua villavicencio de uno coma cinco litros perdón esas no llegar a no las carnes

- **Sustituciones:** `agregá` → `agrega`; `1` → `coma`; `5` → `cinco`; `llegaron` → `a`; `cargues` → `carnes`
- **Agregados:** `uno`; `llegar`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cinco botellas de agua villavicencio de uno coma cinco litros perdón esas no llegar a no las carnes

- **Sustituciones:** `agregá` → `agrega`; `1` → `coma`; `5` → `cinco`; `llegaron` → `a`; `cargues` → `carnes`
- **Agregados:** `uno`; `llegar`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Abrega 5 de agua visualicencia de 1,5 litros. Perdón, esas no llegaron a las carres.

- **Sustituciones:** `cinco` → `abrega`; `botellas` → `5`; `villavicencio` → `visualicencia`; `no` → `a`; `cargues` → `carres`
- **Omisiones:** `agregá`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Abrega 5 tallas de agua vizadiscencio de 1,5 litros. Perdón, esas no llegaron las cargues.

- **Sustituciones:** `agregá` → `abrega`; `cinco` → `5`; `botellas` → `tallas`; `villavicencio` → `vizadiscencio`
- **Omisiones:** `no`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 5 botellas de agua billa de licencia de 1,5 litros. Perdón, esas no llegaron, no las cargues.

- **Sustituciones:** `agregá` → `agrega`; `cinco` → `5`; `villavicencio` → `licencia`
- **Agregados:** `billa`; `de`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cinco botellas de agua visualicencia de uno coma cinco litros perdón esas no llegaron no las cargues

- **Sustituciones:** `agregá` → `agrega`; `villavicencio` → `visualicencia`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cinco botellas de agua a visodicencio de uno coma cinco litros perdón esas no llegaron no las cargues

- **Sustituciones:** `agregá` → `agrega`; `villavicencio` → `visodicencio`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `a`; `uno`


## negar_restacion

**Texto esperado:**

> Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 50.00 % | 40.66 % | 50.00–50.00 % | 6.00 | 1.00 | 1.00 | 0.829 s |
| vosk_250ms | 50.00 % | 40.66 % | 50.00–50.00 % | 6.00 | 1.00 | 1.00 | 0.842 s |
| whisper_tiny | 50.00 % | 35.16 % | 50.00–50.00 % | 7.00 | 0.00 | 1.00 | 0.548 s |
| whisper_base | 18.75 % | 16.48 % | 18.75–18.75 % | 3.00 | 0.00 | 0.00 | 1.253 s |
| whisper_small_q5_1 | 37.50 % | 19.78 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 4.988 s |
| moonshine_tiny_es | 18.75 % | 31.87 % | 18.75–18.75 % | 2.00 | 0.00 | 1.00 | 0.639 s |
| moonshine_small_es | 31.25 % | 34.07 % | 31.25–31.25 % | 4.00 | 0.00 | 1.00 | 1.460 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> resta cuatro envases detergentes magistral de setecientos cincuenta mililitros perdón no se vendieron no lo agrestes

- **Sustituciones:** `restá` → `resta`; `detergente` → `detergentes`; `750` → `cincuenta`; `ml` → `mililitros`; `los` → `lo`; `restes` → `agrestes`
- **Omisiones:** `de`
- **Agregados:** `setecientos`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> resta cuatro envases detergentes magistral de setecientos cincuenta mililitros perdón no se vendieron no lo agrestes

- **Sustituciones:** `restá` → `resta`; `detergente` → `detergentes`; `750` → `cincuenta`; `ml` → `mililitros`; `los` → `lo`; `restes` → `agrestes`
- **Omisiones:** `de`
- **Agregados:** `setecientos`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta 4 en bases de 300 magistrales de 750 mililitros, pero no se vendieron, no los restes.

- **Sustituciones:** `restá` → `4`; `cuatro` → `en`; `envases` → `bases`; `detergente` → `300`; `magistral` → `magistrales`; `ml` → `mililitros`; `perdón` → `pero`
- **Agregados:** `resta`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Restá 4 envases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

- **Sustituciones:** `cuatro` → `4`; `detergente` → `detergentes`; `ml` → `mililitros`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Resta 4 en bases de detergentes magistral de 750 mililitros. Perdón, no se vendieron, no los restes.

- **Sustituciones:** `restá` → `4`; `cuatro` → `en`; `envases` → `bases`; `detergente` → `detergentes`; `ml` → `mililitros`
- **Agregados:** `resta`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> restá cuatro envases de detergente magistral de setecientos cincuenta mililitros perdón no se vendieron no los restes

- **Sustituciones:** `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `setecientos`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> resta cuatro envases de detergentes magistral de setecientos cincuenta mililitros perdón no se vendieron no los restes

- **Sustituciones:** `restá` → `resta`; `detergente` → `detergentes`; `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `setecientos`


## negar_varias_agregaciones

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 41.86 % | 26.09 % | 41.86–41.86 % | 16.00 | 0.00 | 2.00 | 1.336 s |
| vosk_250ms | 44.19 % | 28.50 % | 44.19–44.19 % | 16.00 | 1.00 | 2.00 | 1.341 s |
| whisper_tiny | 27.91 % | 16.91 % | 27.91–27.91 % | 10.00 | 1.00 | 1.00 | 0.718 s |
| whisper_base | 32.56 % | 16.43 % | 32.56–32.56 % | 12.00 | 2.00 | 0.00 | 1.517 s |
| whisper_small_q5_1 | 16.28 % | 14.49 % | 16.28–16.28 % | 5.00 | 2.00 | 0.00 | 5.590 s |
| moonshine_tiny_es | 34.88 % | 22.22 % | 34.88–34.88 % | 13.00 | 0.00 | 2.00 | 1.319 s |
| moonshine_small_es | 27.91 % | 15.94 % | 27.91–27.91 % | 11.00 | 0.00 | 1.00 | 2.745 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros cuatro spray comunes de uno coma cinco litros y cinco paquete de ahorro gallo de un kilo medio que las coca colas comunes de dos litros y las esprit comunes de uno coma cinco no las cargues

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `paquetes` → `paquete`; `arroz` → `ahorro`; `1` → `un`; `kg` → `kilo`; `me` → `medio`; `equivoque` → `que`; `cola` → `colas`; `2` → `dos`; `sprite` → `esprit`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`; `uno`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres cola comunes de dos litros cuatro spray comunes de uno coma cinco litros y cinco paquete de ahorro gallo de un kilo medio que las coca colas comunes de dos litros y las esprit comunes de uno coma cinco no las cargues

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `paquetes` → `paquete`; `arroz` → `ahorro`; `1` → `un`; `kg` → `kilo`; `me` → `medio`; `equivoque` → `que`; `cola` → `colas`; `2` → `dos`; `sprite` → `esprit`; `1` → `coma`; `5` → `cinco`
- **Omisiones:** `coca`
- **Agregados:** `uno`; `uno`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Abrega 3 Coca-Cola comunes de 2 litros, 4 sprite comunes de 1,5 litros y 5 pague de arrogayo de un kilo. Me guivo que las Coca-Cola comunes de 2 litros y las sprite comunes de 1,5 no las carres.

- **Sustituciones:** `agregá` → `abrega`; `tres` → `3`; `cuatro` → `4`; `cinco` → `5`; `paquetes` → `pague`; `gallo` → `arrogayo`; `1` → `un`; `kg` → `kilo`; `equivoque` → `que`; `cargues` → `carres`
- **Omisiones:** `arroz`
- **Agregados:** `guivo`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  A agregar 3 cocacolas comunes de 2 litros, 4 sprites comunes de 1,5 litros y 5 paquetes de rogallos de 1 kilo. Me equivoque las cocacolas comunes de 2 litros y las sprites comunes de 1,5 no las cargas.

- **Sustituciones:** `agregá` → `a`; `tres` → `agregar`; `coca` → `3`; `cola` → `cocacolas`; `cuatro` → `4`; `sprite` → `sprites`; `cinco` → `5`; `gallo` → `rogallos`; `kg` → `kilo`; `cola` → `cocacolas`; `sprite` → `sprites`; `cargues` → `cargas`
- **Omisiones:** `arroz`; `coca`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  3 Coca-Cola comunes de 2 litros 4 Sprite comunes de 1,5 litros y 5 paquetes de arroz gallo de 1 kilo. Me equivoque, las Coca-Cola comunes de 2 litros y Sprite comunes de 1,5 no las cargués.

- **Sustituciones:** `tres` → `3`; `cuatro` → `4`; `cinco` → `5`; `kg` → `kilo`; `cargues` → `cargués`
- **Omisiones:** `agregá`; `las`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> agregad tres coca cola comunes de dos litros cuatro sprite comunes de uno coma cinco litros y cinco paquetes de arroga sho de un kilo me equivoqué las coca colas comunes de dos litros y las sprite comunes de uno coma cinco no las cargues

- **Sustituciones:** `agregá` → `agregad`; `2` → `dos`; `1` → `coma`; `5` → `cinco`; `arroz` → `arroga`; `gallo` → `sho`; `1` → `un`; `kg` → `kilo`; `equivoque` → `equivoqué`; `cola` → `colas`; `2` → `dos`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`; `uno`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros cuatro spray comunes de 1,5 litros y cinco paquetes de arroz gallo de un kilo me equivoqué las coca colas comunes de dos litros y las spray comunes de uno coma cinco no las cargues

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `sprite` → `spray`; `1` → `un`; `kg` → `kilo`; `equivoque` → `equivoqué`; `cola` → `colas`; `2` → `dos`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `uno`


## negar_varias_restaciones

**Texto esperado:**

> Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 37.84 % | 31.28 % | 37.84–37.84 % | 11.00 | 2.00 | 1.00 | 1.259 s |
| vosk_250ms | 37.84 % | 31.28 % | 37.84–37.84 % | 11.00 | 2.00 | 1.00 | 1.287 s |
| whisper_tiny | 51.35 % | 25.14 % | 51.35–51.35 % | 14.00 | 2.00 | 3.00 | 0.688 s |
| whisper_base | 32.43 % | 20.11 % | 32.43–32.43 % | 10.00 | 1.00 | 1.00 | 1.436 s |
| whisper_small_q5_1 | 27.03 % | 21.23 % | 27.03–27.03 % | 9.00 | 0.00 | 1.00 | 5.295 s |
| moonshine_tiny_es | 35.14 % | 27.37 % | 35.14–35.14 % | 12.00 | 0.00 | 1.00 | 1.058 s |
| moonshine_small_es | 27.03 % | 23.46 % | 27.03–27.03 % | 9.00 | 0.00 | 1.00 | 2.047 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> presta dos coca-cola cero de dos litros tres paquetes arroyo de un kilo y cuatro en de detergente magistral de setecientos cincuenta mililitros las coca cero y el arroz no se vendieron no los prestes

- **Sustituciones:** `restá` → `presta`; `zero` → `cero`; `2` → `dos`; `gallo` → `arroyo`; `1` → `un`; `kg` → `kilo`; `envases` → `en`; `750` → `cincuenta`; `ml` → `mililitros`; `zero` → `cero`; `restes` → `prestes`
- **Omisiones:** `de`; `arroz`
- **Agregados:** `setecientos`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> presta dos coca-cola cero de dos litros tres paquetes arroyo de un kilo y cuatro en de detergente magistral de setecientos cincuenta mililitros las coca cero y el arroz no se vendieron no los prestes

- **Sustituciones:** `restá` → `presta`; `zero` → `cero`; `2` → `dos`; `gallo` → `arroyo`; `1` → `un`; `kg` → `kilo`; `envases` → `en`; `750` → `cincuenta`; `ml` → `mililitros`; `zero` → `cero`; `restes` → `prestes`
- **Omisiones:** `de`; `arroz`
- **Agregados:** `setecientos`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  presta 2 cocacola 0 de 2 litros, 3 paquetes de arroz vayo de un kilo y 4 en bases de de tergen de magistral de 75 mililitros. Las cocaceros y el arroz no se vendieron, no los restes.

- **Sustituciones:** `dos` → `presta`; `coca` → `2`; `cola` → `cocacola`; `zero` → `0`; `tres` → `3`; `gallo` → `vayo`; `1` → `un`; `kg` → `kilo`; `cuatro` → `bases`; `envases` → `de`; `detergente` → `de`; `750` → `75`; `ml` → `mililitros`; `zero` → `cocaceros`
- **Omisiones:** `restá`; `coca`
- **Agregados:** `4`; `en`; `tergen`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Reesta 2 cocacolla 0 de 2 litros, 3 paquetes de arroz gallo de un kilo y 4 envases de terjén de magistral de 750 ml. Las coca 0 y el arroz no se vendieron, no los restes.

- **Sustituciones:** `dos` → `reesta`; `coca` → `2`; `cola` → `cocacolla`; `zero` → `0`; `tres` → `3`; `1` → `un`; `kg` → `kilo`; `cuatro` → `4`; `detergente` → `de`; `zero` → `0`
- **Omisiones:** `restá`
- **Agregados:** `terjén`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Prestar 2 Coca-Cola 0 de 2 litros, 3 paquetes de arroz gallo de 1 kilo y 4 en base de detergente magistral de 750 mililitros. Las Coca-0 y el arroz no se vendieron, no los restes.

- **Sustituciones:** `restá` → `prestar`; `dos` → `2`; `zero` → `0`; `tres` → `3`; `kg` → `kilo`; `cuatro` → `en`; `envases` → `base`; `ml` → `mililitros`; `zero` → `0`
- **Agregados:** `4`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> presta dos coca colas cero de dos litros tres paquetes de arroja sho de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros las cocas hero y el arroz no se vendieron no los restes

- **Sustituciones:** `restá` → `presta`; `cola` → `colas`; `zero` → `cero`; `2` → `dos`; `arroz` → `arroja`; `gallo` → `sho`; `1` → `un`; `kg` → `kilo`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `cocas`; `zero` → `hero`
- **Agregados:** `setecientos`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> presta dos coca cola cero de dos litros tres paquetes de arroz gallo de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros las cocas cero y el arroz no se vendieron no los restes

- **Sustituciones:** `restá` → `presta`; `zero` → `cero`; `2` → `dos`; `1` → `un`; `kg` → `kilo`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `cocas`; `zero` → `cero`
- **Agregados:** `setecientos`


## negar_agregacion_y_restacion

**Texto esperado:**

> Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 28.57 % | 13.97 % | 28.57–28.57 % | 9.00 | 1.00 | 0.00 | 1.041 s |
| vosk_250ms | 28.57 % | 13.97 % | 28.57–28.57 % | 9.00 | 1.00 | 0.00 | 1.051 s |
| whisper_tiny | 25.71 % | 10.61 % | 25.71–25.71 % | 8.00 | 1.00 | 0.00 | 0.663 s |
| whisper_base | 25.71 % | 8.94 % | 25.71–25.71 % | 9.00 | 0.00 | 0.00 | 1.424 s |
| whisper_small_q5_1 | 22.86 % | 12.85 % | 22.86–22.86 % | 8.00 | 0.00 | 0.00 | 5.367 s |
| moonshine_tiny_es | 28.57 % | 13.97 % | 28.57–28.57 % | 9.00 | 1.00 | 0.00 | 0.907 s |
| moonshine_small_es | 22.86 % | 11.73 % | 22.86–22.86 % | 8.00 | 0.00 | 0.00 | 2.017 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cuatro spray comunes de dos litros y resta dos paquetes de arroz gallo de un kilo perdón la césped no llegaron y el arroz no se vendió nuevas ninguna de esas dos operaciones

- **Sustituciones:** `agregá` → `agrega`; `sprite` → `spray`; `2` → `dos`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `las` → `la`; `sprite` → `césped`; `hagas` → `nuevas`
- **Omisiones:** `no`


### vosk_250ms

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cuatro spray comunes de dos litros y resta dos paquetes de arroz gallo de un kilo perdón la césped no llegaron y el arroz no se vendió nuevas ninguna de esas dos operaciones

- **Sustituciones:** `agregá` → `agrega`; `sprite` → `spray`; `2` → `dos`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `las` → `la`; `sprite` → `césped`; `hagas` → `nuevas`
- **Omisiones:** `no`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega, cuatro sprite comunes de dos litros y restados paquetes de arroz gallos de un kilo. Perdón, las especies no llegaron y el arroz no se vendió. No has ninguna de esas dos operaciones.

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `dos` → `restados`; `gallo` → `gallos`; `1` → `un`; `kg` → `kilo`; `sprite` → `especies`; `hagas` → `has`
- **Omisiones:** `restá`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega, cuatro sprites comunes de dos litros y resta dos paquetes de arroz gallos de un kilo. Perdón, las sprites no llegaron y el arroz no se vendió, no das ninguna de esas dos operaciones.

- **Sustituciones:** `agregá` → `agrega`; `sprite` → `sprites`; `2` → `dos`; `restá` → `resta`; `gallo` → `gallos`; `1` → `un`; `kg` → `kilo`; `sprite` → `sprites`; `hagas` → `das`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega 4 spray comunes de 2 litros y resta 2 paquetes de arroz gallo de 1 kilo. Perdón, las spray no llegaron y el arroz no se vendió, no hagas ninguna de esas 2 operaciones.

- **Sustituciones:** `agregá` → `agrega`; `cuatro` → `4`; `sprite` → `spray`; `restá` → `resta`; `dos` → `2`; `kg` → `kilo`; `sprite` → `spray`; `dos` → `2`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cuatro spray comunes de dos litros y restad dos paquetes de arrojacho de un kilo perdón las spain no llegaron y el arroz no se vendió no das ninguna de esas dos operaciones

- **Sustituciones:** `agregá` → `agrega`; `sprite` → `spray`; `2` → `dos`; `restá` → `restad`; `gallo` → `arrojacho`; `1` → `un`; `kg` → `kilo`; `sprite` → `spain`; `hagas` → `das`
- **Omisiones:** `arroz`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega cuatro sprays comunes de dos litros y restad dos paquetes de arroz gallo de un kilo perdón las espéim no llegaron y el arroz no se vendió no das ninguna de esas dos operaciones

- **Sustituciones:** `agregá` → `agrega`; `sprite` → `sprays`; `2` → `dos`; `restá` → `restad`; `1` → `un`; `kg` → `kilo`; `sprite` → `espéim`; `hagas` → `das`


## caso_integral

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| vosk_full | 37.91 % | 22.82 % | 37.40–38.17 % | 41.00 | 3.67 | 5.00 | 3.570 s |
| vosk_250ms | 38.17 % | 23.16 % | 37.40–38.93 % | 40.33 | 4.67 | 5.00 | 3.588 s |
| whisper_tiny | 52.67 % | 23.65 % | 52.67–52.67 % | 54.00 | 5.00 | 10.00 | 1.926 s |
| whisper_base | 34.35 % | 15.91 % | 34.35–34.35 % | 37.00 | 2.00 | 6.00 | 3.780 s |
| whisper_small_q5_1 | 28.24 % | 16.64 % | 28.24–28.24 % | 27.00 | 7.00 | 3.00 | 12.774 s |
| moonshine_tiny_es | 31.30 % | 19.12 % | 31.30–31.30 % | 33.00 | 3.00 | 5.00 | 4.305 s |
| moonshine_small_es | 25.95 % | 16.06 % | 25.95–25.95 % | 29.00 | 1.00 | 4.00 | 8.845 s |

Los conteos de la tabla son promedios de las repeticiones.

### vosk_full

**Repeticiones 1, 2 — estado: ok**

> agrega tres cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `great`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `1` → `coma`; `5` → `cinco`; `así` → `a`; `que` → `siguen`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarás`; `de` → `al`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `de` → `base`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `co`; `zero` → `caserón`; `ni` → `y`; `detergentes` → `detergente`; `restes` → `es`; `agregá` → `agrega`; `envases` → `envase`; `1` → `un`; `restá` → `resta`; `dos` → `doce`; `sprite` → `spray`; `2` → `dos`; `no` → `express`; `se` → `nace`; `cargues` → `es`; `restes` → `reste`; `esas` → `cesase`; `sprite` → `spray`
- **Omisiones:** `coca`; `dos`; `envases`; `sprite`
- **Agregados:** `a`; `uno`; `uno`; `setecientos`; `resta`

**Repeticiones 3 — estado: ok**

> agrega tres coca cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `great`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `1` → `coma`; `5` → `cinco`; `así` → `a`; `que` → `siguen`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarás`; `de` → `al`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `de` → `base`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `co`; `zero` → `caserón`; `ni` → `y`; `detergentes` → `detergente`; `restes` → `es`; `agregá` → `agrega`; `envases` → `envase`; `1` → `un`; `restá` → `resta`; `dos` → `doce`; `sprite` → `spray`; `2` → `dos`; `no` → `express`; `se` → `nace`; `cargues` → `es`; `restes` → `reste`; `esas` → `cesase`; `sprite` → `spray`
- **Omisiones:** `dos`; `envases`; `sprite`
- **Agregados:** `a`; `uno`; `uno`; `setecientos`; `resta`


### vosk_250ms

**Repeticiones 1 — estado: ok**

> agrega tres coca comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `great`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `1` → `coma`; `5` → `cinco`; `así` → `a`; `que` → `siguen`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarás`; `de` → `al`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `de` → `base`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `co`; `zero` → `caserón`; `ni` → `y`; `detergentes` → `detergente`; `restes` → `es`; `agregá` → `agrega`; `envases` → `envase`; `1` → `un`; `restá` → `resta`; `dos` → `doce`; `sprite` → `spray`; `2` → `dos`; `no` → `express`; `se` → `nace`; `cargues` → `es`; `restes` → `reste`; `esas` → `cesase`; `sprite` → `spray`
- **Omisiones:** `cola`; `dos`; `tres`; `envases`; `sprite`
- **Agregados:** `a`; `uno`; `uno`; `setecientos`; `resta`

**Repeticiones 2 — estado: ok**

> agrega tres cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos así que no los cargues resta dos paquetes de arroz gallo de un kilo y paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no reste es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `great`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `1` → `coma`; `5` → `cinco`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarás`; `de` → `al`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `de` → `base`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `co`; `zero` → `caserón`; `ni` → `y`; `detergentes` → `detergente`; `restes` → `es`; `agregá` → `agrega`; `envases` → `envase`; `1` → `un`; `restá` → `resta`; `dos` → `doce`; `sprite` → `spray`; `2` → `dos`; `no` → `express`; `se` → `nace`; `cargues` → `es`; `restes` → `reste`; `esas` → `cesase`; `sprite` → `spray`
- **Omisiones:** `coca`; `dos`; `tres`; `envases`; `sprite`
- **Agregados:** `a`; `uno`; `uno`; `setecientos`; `reste`

**Repeticiones 3 — estado: ok**

> agrega tres coca cola comunes de dos litros perdón eran dos a great cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llegó ninguno de esos productos a siguen no los cargues resta dos paquetes de arroz gallo de un kilo y paquetes de fideos matarás al quinientos gramos resta cuatro coca cola cero de dos litros y cinco base detergente magistral de setecientos cincuenta mililitros perdón ni las co caserón y los detergente se vendieron no resta es ninguno de esos dos productos agrega seis envase de leche la serenísima de un litro y resta doce spray comunes de dos litros perdón la leche no llegó y esas express nace vendieron no es la leche ni reste cesase spray

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `great`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `1` → `coma`; `5` → `cinco`; `así` → `a`; `que` → `siguen`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarás`; `de` → `al`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `de` → `base`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `co`; `zero` → `caserón`; `ni` → `y`; `detergentes` → `detergente`; `restes` → `es`; `agregá` → `agrega`; `envases` → `envase`; `1` → `un`; `restá` → `resta`; `dos` → `doce`; `sprite` → `spray`; `2` → `dos`; `no` → `express`; `se` → `nace`; `cargues` → `es`; `restes` → `reste`; `esas` → `cesase`; `sprite` → `spray`
- **Omisiones:** `dos`; `tres`; `envases`; `sprite`
- **Agregados:** `a`; `uno`; `uno`; `setecientos`; `resta`


### whisper_tiny

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega, 3 cucacola con 1/2 litros, prón, el andos, agrega 4 prítcomunes de 1,5 litros y 5 tillas de agua visavicencia de 1,5 litros. Prón, no yo hago ni 1 de esos 2 productos, así lleno los carres, resta 2 paquetes de arroz gallo de 1 kilo y 3 paquetes de fíjidos matarasos y 500 gramos. Resta 4 cococola 0 de 2 litros y 5 en bases de de 3 gente magistral de 75 ml. Perdón, ni las cocacelen y los detergentes se vendieron, no resten 1 de esos 2 productos. Agrega 6 en bases de leche y la serenísima, de 1 litro y resta 2 spray comune de 2 litros. Perdón, la leche no llegó y esa se spray no se vendieron, no carrega la leche ni resta y se ases prítos.

- **Sustituciones:** `tres` → `agrega`; `coca` → `3`; `cola` → `cucacola`; `comunes` → `con`; `de` → `1`; `eran` → `prón`; `dos` → `el`; `agregá` → `andos`; `cuatro` → `agrega`; `sprite` → `4`; `comunes` → `prítcomunes`; `cinco` → `5`; `botellas` → `tillas`; `villavicencio` → `visavicencia`; `perdón` → `prón`; `llegó` → `ni`; `ninguno` → `1`; `dos` → `2`; `no` → `lleno`; `cargues` → `carres`; `restá` → `resta`; `dos` → `2`; `kg` → `kilo`; `tres` → `3`; `fideos` → `fíjidos`; `matarazzo` → `matarasos`; `de` → `y`; `restá` → `gramos`; `cuatro` → `resta`; `coca` → `4`; `cola` → `cococola`; `zero` → `0`; `cinco` → `bases`; `envases` → `de`; `detergente` → `gente`; `750` → `75`; `zero` → `cocacelen`; `ni` → `y`; `restes` → `resten`; `ninguno` → `1`; `dos` → `2`; `agregá` → `6`; `seis` → `en`; `envases` → `bases`; `restá` → `resta`; `dos` → `2`; `sprite` → `spray`; `comunes` → `comune`; `esas` → `se`; `sprite` → `spray`; `cargues` → `carrega`; `restes` → `se`; `esas` → `ases`; `sprite` → `prítos`
- **Omisiones:** `agregá`; `perdón`; `que`; `g`; `coca`
- **Agregados:** `yo`; `hago`; `5`; `en`; `3`; `agrega`; `y`; `esa`; `resta`; `y`


### whisper_base

**Repeticiones 1, 2, 3 — estado: ok**

>  Agrega, tres cocacola comunes de dos litros, perdón, eran dos. Agrega, cuatro spray comunes de uno coma cinco litros y cinco dotellas de agua vizabicensio de uno coma cinco litros. Perdón, no llegó ni uno de esos dos productos, así que no en los carreras. Resta a dos paquetes de arroz gayo de un kilo y tres paquetes de fíjidos matarazo de 500 gramos. Resta a cuatro cocacola cero de dos litros y cinco envases de detergente magistral de 750 mililitros. Perdón, ni las cocaceron y los detergentes se vendieron, no restes ninguno de esos dos productos. Agrega, seis envases de leche y la serenísima, de un litro y restas dos spray comunes de dos litros. Perdón, la leche no llegó y esas spray no se vendieron, no carges la leche ni restes esas spray.

- **Sustituciones:** `agregá` → `agrega`; `cola` → `cocacola`; `2` → `dos`; `agregá` → `agrega`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `botellas` → `dotellas`; `villavicencio` → `vizabicensio`; `1` → `coma`; `5` → `cinco`; `ninguno` → `uno`; `cargues` → `resta`; `restá` → `a`; `gallo` → `gayo`; `1` → `un`; `kg` → `kilo`; `fideos` → `fíjidos`; `matarazzo` → `matarazo`; `g` → `gramos`; `restá` → `resta`; `cuatro` → `a`; `coca` → `cuatro`; `cola` → `cocacola`; `zero` → `cero`; `2` → `dos`; `ml` → `mililitros`; `zero` → `cocaceron`; `ni` → `y`; `agregá` → `agrega`; `1` → `un`; `restá` → `restas`; `sprite` → `spray`; `2` → `dos`; `sprite` → `spray`; `cargues` → `carges`; `sprite` → `spray`
- **Omisiones:** `coca`; `coca`
- **Agregados:** `uno`; `uno`; `ni`; `en`; `carreras`; `y`


### whisper_small_q5_1

**Repeticiones 1, 2, 3 — estado: ok**

>  3 Coca-Cola comunes de 2 litros, 4 Sprite comunes de 1,5 litros y 5 botellas de agua viva visencio de 1,5 litros. No llegó ninguno de esos 2 productos, así que no los cargués. Resta 2 paquetes de arroz gallo de 1 kilo y 3 paquetes de fideos matarazos de 500 gramos. Resta 4 Coca-Cola 0 de 2 litros y 5 en bases de detergente magistral de 750 ml. Perdón, ni las Coca-cero ni los detergentes se vendieron, no restes ninguno de esos 2 productos. Agrega 6 en bases de leche lazerenísima de 1 litro y resta 2 Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron. No cargués la leche ni restes esa Sprite.

- **Sustituciones:** `tres` → `3`; `cuatro` → `4`; `cinco` → `5`; `villavicencio` → `visencio`; `dos` → `2`; `cargues` → `cargués`; `restá` → `resta`; `dos` → `2`; `kg` → `kilo`; `tres` → `3`; `matarazzo` → `matarazos`; `g` → `gramos`; `restá` → `resta`; `cuatro` → `4`; `zero` → `0`; `cinco` → `en`; `envases` → `bases`; `zero` → `cero`; `dos` → `2`; `agregá` → `6`; `seis` → `en`; `envases` → `bases`; `serenísima` → `lazerenísima`; `restá` → `resta`; `dos` → `2`; `cargues` → `cargués`; `esas` → `esa`
- **Omisiones:** `agregá`; `perdón`; `eran`; `dos`; `agregá`; `perdón`; `la`
- **Agregados:** `viva`; `5`; `agrega`


### moonshine_tiny_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros perdón eran dos agrega cuatro spray comunes de uno coma cinco litros y cinco botellas de agua bishavicencia de uno coma cinco litros perdón no llego a ninguno de esos dos productos así que no los cargues resta a dos paquetes de arroga sho de un kilo y tres paquetes de fideos matarazos de quinientos gramos resta cuatro coca cola cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros perdón ni las cocaseron ni los detergentes se vendieron no restes ninguno de esos dos productos agrega seis envases de leche la cerenísima un litro y restar dos spray comunes de dos litros perdón la leche nos llevó y esas espeñas se vendieron no cargues la leche ni restes esas sprite

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `agrega`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `villavicencio` → `bishavicencia`; `1` → `coma`; `5` → `cinco`; `llegó` → `a`; `restá` → `a`; `arroz` → `arroga`; `gallo` → `sho`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarazos`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`; `zero` → `cocaseron`; `agregá` → `agrega`; `de` → `cerenísima`; `1` → `un`; `restá` → `restar`; `sprite` → `spray`; `2` → `dos`; `no` → `nos`; `llegó` → `llevó`; `no` → `espeñas`
- **Omisiones:** `coca`; `serenísima`; `sprite`
- **Agregados:** `uno`; `uno`; `llego`; `resta`; `setecientos`


### moonshine_small_es

**Repeticiones 1, 2, 3 — estado: ok**

> agrega tres coca cola comunes de dos litros perdón eran dos agrega cuatro spray comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno coma cinco litros perdón no llevo ninguno de esos dos productos así lleno los cargues restar dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarazos de 500 gramos resta cuatro coca cola cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros perdón ni las coca cero ni los detergentes se vendieron no restes ninguno de esos dos productos agrega a seis envases de leche la serenísima en un litro y restar dos spray comunes de dos litros perdón la leche no llegó y esas espéi no se vendieron no cargues la leche ni restes esas spray

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `agrega`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`; `1` → `coma`; `5` → `cinco`; `llegó` → `llevo`; `no` → `lleno`; `restá` → `restar`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarazos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`; `zero` → `cero`; `agregá` → `a`; `de` → `en`; `1` → `un`; `restá` → `restar`; `sprite` → `spray`; `2` → `dos`; `sprite` → `espéi`; `sprite` → `spray`
- **Omisiones:** `que`
- **Agregados:** `uno`; `uno`; `setecientos`; `agrega`
