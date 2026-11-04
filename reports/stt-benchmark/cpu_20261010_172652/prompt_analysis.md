# Análisis STT por prompt

Repeticiones medidas agrupadas por configuración; calentamientos excluidos.
Los textos esperados vienen de los prompts y requieren revisión humana del audio.
WER estricto: números en palabras/dígitos, acentos y marcas cuentan como diferencias.
Las alineaciones explican diferencias textuales, no evalúan el significado.
Una alineación mínima puede tener otras alternativas igualmente válidas.

## WER medio por prompt (%)

| Prompt | moonshine_tiny_es | moonshine_small_es |
| --- | --- | --- |
| solo_agregar | 37.50 | 37.50 |
| solo_restar | 33.33 | 33.33 |
| restar_ambos | 52.94 | 35.29 |
| corregir_cantidad | 18.18 | 18.18 |
| negar_agregacion | 29.41 | 35.29 |
| negar_restacion | 18.75 | 31.25 |
| negar_varias_agregaciones | 34.88 | 27.91 |
| negar_varias_restaciones | 35.14 | 27.03 |
| negar_agregacion_y_restacion | 28.57 | 22.86 |
| caso_integral | 31.30 | 25.95 |

## Casos con mayor WER por configuración

- **moonshine_tiny_es:** restar_ambos (52.94 %); solo_agregar (37.50 %); negar_varias_restaciones (35.14 %)
- **moonshine_small_es:** solo_agregar (37.50 %); restar_ambos (35.29 %); negar_agregacion (35.29 %)

## solo_agregar

**Texto esperado:**

> Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

| Configuración | WER medio | CER medio | WER min–max | Sustituciones | Omisiones | Agregados | Tiempo medio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| moonshine_tiny_es | 37.50 % | 25.32 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 0.634 s |
| moonshine_small_es | 37.50 % | 25.32 % | 37.50–37.50 % | 5.00 | 0.00 | 1.00 | 1.274 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 0.233 s |
| moonshine_small_es | 33.33 % | 14.63 % | 33.33–33.33 % | 3.00 | 0.00 | 0.00 | 0.562 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 52.94 % | 43.68 % | 52.94–52.94 % | 7.00 | 1.00 | 1.00 | 0.451 s |
| moonshine_small_es | 35.29 % | 39.08 % | 35.29–35.29 % | 5.00 | 0.00 | 1.00 | 1.233 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 18.18 % | 8.77 % | 18.18–18.18 % | 2.00 | 0.00 | 0.00 | 0.612 s |
| moonshine_small_es | 18.18 % | 7.02 % | 18.18–18.18 % | 2.00 | 0.00 | 0.00 | 1.216 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 29.41 % | 18.75 % | 29.41–29.41 % | 4.00 | 0.00 | 1.00 | 0.626 s |
| moonshine_small_es | 35.29 % | 20.83 % | 35.29–35.29 % | 4.00 | 0.00 | 2.00 | 1.862 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 18.75 % | 31.87 % | 18.75–18.75 % | 2.00 | 0.00 | 1.00 | 0.639 s |
| moonshine_small_es | 31.25 % | 34.07 % | 31.25–31.25 % | 4.00 | 0.00 | 1.00 | 1.460 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 34.88 % | 22.22 % | 34.88–34.88 % | 13.00 | 0.00 | 2.00 | 1.319 s |
| moonshine_small_es | 27.91 % | 15.94 % | 27.91–27.91 % | 11.00 | 0.00 | 1.00 | 2.745 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 35.14 % | 27.37 % | 35.14–35.14 % | 12.00 | 0.00 | 1.00 | 1.058 s |
| moonshine_small_es | 27.03 % | 23.46 % | 27.03–27.03 % | 9.00 | 0.00 | 1.00 | 2.047 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 28.57 % | 13.97 % | 28.57–28.57 % | 9.00 | 1.00 | 0.00 | 0.907 s |
| moonshine_small_es | 22.86 % | 11.73 % | 22.86–22.86 % | 8.00 | 0.00 | 0.00 | 2.017 s |

Los conteos de la tabla son promedios de las repeticiones.

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
| moonshine_tiny_es | 31.30 % | 19.12 % | 31.30–31.30 % | 33.00 | 3.00 | 5.00 | 4.305 s |
| moonshine_small_es | 25.95 % | 16.06 % | 25.95–25.95 % | 29.00 | 1.00 | 4.00 | 8.845 s |

Los conteos de la tabla son promedios de las repeticiones.

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
