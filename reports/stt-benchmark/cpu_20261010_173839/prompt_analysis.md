# Análisis STT por prompt

Repeticiones medidas agrupadas por configuración; calentamientos excluidos.
Los textos esperados vienen de los prompts y requieren revisión humana del audio.
WER estricto: números en palabras/dígitos, acentos y marcas cuentan como diferencias.
Las alineaciones explican diferencias textuales, no evalúan el significado.
Una alineación mínima puede tener otras alternativas igualmente válidas.

## WER medio por prompt (%)

| Prompt | kroko_es |
| --- | --- |
| solo_agregar | 43.75 |
| solo_restar | 44.44 |
| restar_ambos | 41.18 |
| corregir_cantidad | 18.18 |
| negar_agregacion | 35.29 |
| negar_restacion | 37.50 |
| negar_varias_agregaciones | 39.53 |
| negar_varias_restaciones | 32.43 |
| negar_agregacion_y_restacion | 25.71 |
| caso_integral | 23.66 |

## Casos con mayor WER por configuración

- **kroko_es:** solo_restar (44.44 %); solo_agregar (43.75 %); restar_ambos (41.18 %)

## solo_agregar

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 43.75 % | 26.58 % | 43.75–43.75 % | 6.00 | 0.00 | 1.00 | 0.391 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Agregar tres Coca-Cola comunes de dos litros y cuatro sprays comunes de uno coma cinco li

- **Sustituciones:** `agregá` → `agregar`; `2` → `dos`; `sprite` → `sprays`; `1` → `coma`; `5` → `cinco`; `litros` → `li`
- **Agregados:** `uno`


## solo_restar

**Texto esperado:**

> Restá dos paquetes de arroz Gallo de 1 kg.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 44.44 % | 19.51 % | 44.44–44.44 % | 4.00 | 0.00 | 0.00 | 0.264 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Resta dos paquetes de arroz gaso de un kilo

- **Sustituciones:** `restá` → `resta`; `gallo` → `gaso`; `1` → `un`; `kg` → `kilo`


## restar_ambos

**Texto esperado:**

> Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 41.18 % | 49.43 % | 41.18–41.18 % | 4.00 | 2.00 | 1.00 | 0.393 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Coca-Cola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

- **Sustituciones:** `zero` → `cero`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`
- **Omisiones:** `restá`; `dos`
- **Agregados:** `setecientos`


## corregir_cantidad

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 18.18 % | 8.77 % | 18.18–18.18 % | 2.00 | 0.00 | 0.00 | 0.381 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Agregar tres Coca-Cola comunes de dos litros, perdón, eran dos

- **Sustituciones:** `agregá` → `agregar`; `2` → `dos`


## negar_agregacion

**Texto esperado:**

> Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 35.29 % | 20.83 % | 35.29–35.29 % | 5.00 | 0.00 | 1.00 | 0.462 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Agrega cinco botellas de agua visuavicencio de uno coma cinco litros. Perdón, esas no llegaron, no las car

- **Sustituciones:** `agregá` → `agrega`; `villavicencio` → `visuavicencio`; `1` → `coma`; `5` → `cinco`; `cargues` → `car`
- **Agregados:** `uno`


## negar_restacion

**Texto esperado:**

> Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 37.50 % | 37.36 % | 37.50–37.50 % | 4.00 | 0.00 | 2.00 | 0.527 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Pero está cuatro envases de detergentes magistral de setecientos cincuenta mililitros. Perdón, no se vendieron, no los restes

- **Sustituciones:** `restá` → `está`; `detergente` → `detergentes`; `750` → `cincuenta`; `ml` → `mililitros`
- **Agregados:** `pero`; `setecientos`


## negar_varias_agregaciones

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 39.53 % | 23.67 % | 39.53–39.53 % | 14.00 | 0.00 | 3.00 | 0.971 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Agrega tres Coca-Cola común es de dos litros, cuatro sprays comunes de uno comas cinco litros y cinco paquetes de arroz gallo de un kilo. Me equivoqué, las Coca-Colas comunes de dos litros y las spray comunes, de uno coma cinco, no las cargues

- **Sustituciones:** `agregá` → `agrega`; `comunes` → `es`; `2` → `dos`; `sprite` → `sprays`; `1` → `comas`; `5` → `cinco`; `1` → `un`; `kg` → `kilo`; `equivoque` → `equivoqué`; `cola` → `colas`; `2` → `dos`; `sprite` → `spray`; `1` → `coma`; `5` → `cinco`
- **Agregados:** `común`; `uno`; `uno`


## negar_varias_restaciones

**Texto esperado:**

> Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 32.43 % | 25.70 % | 32.43–32.43 % | 10.00 | 1.00 | 1.00 | 0.846 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Presta dos Coca-Cola cero de dos litros, tres paquetes de rosgallo de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros. Las cocas cero y el arroz no se vendieron, no los restes.

- **Sustituciones:** `restá` → `presta`; `zero` → `cero`; `2` → `dos`; `gallo` → `rosgallo`; `1` → `un`; `kg` → `kilo`; `750` → `cincuenta`; `ml` → `mililitros`; `coca` → `cocas`; `zero` → `cero`
- **Omisiones:** `arroz`
- **Agregados:** `setecientos`


## negar_agregacion_y_restacion

**Texto esperado:**

> Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 25.71 % | 11.17 % | 25.71–25.71 % | 8.00 | 1.00 | 0.00 | 0.666 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Agrega cuatro spys comunes de dos litros y resta dos paquetes de arroz gallo de un kilo. Perdón, las spike no llegaron y el arroz no se vendió. Novas ninguna de esas dos operaciones

- **Sustituciones:** `agregá` → `agrega`; `sprite` → `spys`; `2` → `dos`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `sprite` → `spike`; `hagas` → `novas`
- **Omisiones:** `no`


## caso_integral

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| kroko_es | 23.66 % | 16.20 % | 23.66–23.66 % | 28.00 | 0.00 | 3.00 | 2.601 s |

Los conteos de la tabla son promedios de las repeticiones.

### kroko_es

**Repeticiones 1, 2, 3 — estado: ok**

> Agrega tres Coca-Cola comunes de dos litros, perdón, eran dos. Agrega cuatro sprays comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno comas cinco litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargués. Resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarazos de quinientos gramos. Resta cuatro Coca-Cola, cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros. Perdón, ni las coca ceros ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agrega seis envases de leche la serenísima, de un litro y resta dos spray comunes de dos litros. Perdón, la leche no llegó y esas sprays no se vendieron. No cargues la leche ni restes esas sprays.

- **Sustituciones:** `agregá` → `agrega`; `2` → `dos`; `agregá` → `agrega`; `sprite` → `sprays`; `1` → `coma`; `5` → `cinco`; `1` → `comas`; `5` → `cinco`; `cargues` → `cargués`; `restá` → `resta`; `1` → `un`; `kg` → `kilo`; `matarazzo` → `matarazos`; `500` → `quinientos`; `g` → `gramos`; `restá` → `resta`; `zero` → `cero`; `2` → `dos`; `750` → `cincuenta`; `ml` → `mililitros`; `zero` → `ceros`; `agregá` → `agrega`; `1` → `un`; `restá` → `resta`; `sprite` → `spray`; `2` → `dos`; `sprite` → `sprays`; `sprite` → `sprays`
- **Agregados:** `uno`; `uno`; `setecientos`
