# Revisión de sentido: Kroko español

10 audios, 10 calentamientos y 30 solicitudes medidas; 30/30 completaron inferencia. Se revisan las tres respuestas medidas por prompt contra el texto de referencia, sin escuchar/verificar el audio ni ejecutar un parser de inventario.

WER 30,42%; CER 20,99%; media 0,75 s; máximo 2,64 s; RSS pico 323,43 MiB; carga del modelo 5,59 s. CPU media 706,59% (100% = un núcleo). Aunque num_threads=4, las sesiones internas consumieron en conjunto aproximadamente siete núcleos; no es un límite global de cuatro. Tiempos exploratorios en PC, no aceptación en Pi 3.

| Prompt | WER % | Media s | Revisión |
| --- | --- | --- | --- |
| solo_agregar | 43.75 | 0.39 | Cantidades conservadas, pero Sprite → «sprays» y termina en «li» en lugar de litros. |
| solo_restar | 44.44 | 0.26 | Conserva restar dos paquetes de un kilo; Gallo → «gaso» deja la marca dudosa. |
| restar_ambos | 41.18 | 0.39 | Crítico: omite «restá dos» y empieza directamente con Coca-Cola; pierde acción y cantidad de la primera operación. |
| corregir_cantidad | 18.18 | 0.38 | Coherente: agrega tres y conserva «perdón, eran dos». |
| negar_agregacion | 35.29 | 0.46 | Villavicencio deformado y final «no las car» truncado. «Esas no llegaron» se conserva, pero la prohibición final queda incompleta. |
| negar_restacion | 37.50 | 0.53 | Verbo inicial deformado como «Pero está», pero conserva claramente «no se vendieron, no los restes». |
| negar_varias_agregaciones | 39.53 | 0.97 | Conserva arroz Gallo (operación pendiente), el verbo de agregar y las cancelaciones; Sprite → «sprays» deja identidad dudosa. |
| negar_varias_restaciones | 32.43 | 0.85 | Crítico: «restá» → «presta», y arroz Gallo → «rosgallo». Mantiene cancelaciones, pero resta de detergente queda ambigua. |
| negar_agregacion_y_restacion | 25.71 | 0.67 | Deforma Sprite con nombres inconsistentes («spys», «spike») y «no hagas» → «Novas». Conserva razones de cancelación; orden final ambigua. |
| caso_integral | 23.66 | 2.60 | Conserva corrección tres → dos, cantidades, unidades y todas las cancelaciones explícitas. Sprite → «sprays» y Matarazzo → «matarazos» dejan identificación dudosa. Es mejor en estructura que Whisper Small Q5 y Moonshine Small en este caso concreto, según comparación textual. |

## solo_agregar

Cantidades conservadas, pero Sprite → «sprays» y termina en «li» en lugar de litros.

**Referencia:** Agregá tres Coca Cola comunes de 2 litros y cuatro Sprite comunes de 1,5 litros.

**Respuesta (repeticiones 1, 2, 3):** Agregar tres Coca-Cola comunes de dos litros y cuatro sprays comunes de uno coma cinco li

## solo_restar

Conserva restar dos paquetes de un kilo; Gallo → «gaso» deja la marca dudosa.

**Referencia:** Restá dos paquetes de arroz Gallo de 1 kg.

**Respuesta (repeticiones 1, 2, 3):** Resta dos paquetes de arroz gaso de un kilo

## restar_ambos

Crítico: omite «restá dos» y empieza directamente con Coca-Cola; pierde acción y cantidad de la primera operación.

**Referencia:** Restá dos Coca Cola Zero de 2 litros y cuatro envases de detergente Magistral de 750 ml.

**Respuesta (repeticiones 1, 2, 3):** Coca-Cola cero de dos litros y cuatro envases de detergente magistral de setecientos cincuenta mililitros

## corregir_cantidad

Coherente: agrega tres y conserva «perdón, eran dos».

**Referencia:** Agregá tres Coca Cola comunes de 2 litros. Perdón, eran dos.

**Respuesta (repeticiones 1, 2, 3):** Agregar tres Coca-Cola comunes de dos litros, perdón, eran dos

## negar_agregacion

Villavicencio deformado y final «no las car» truncado. «Esas no llegaron» se conserva, pero la prohibición final queda incompleta.

**Referencia:** Agregá cinco botellas de agua Villavicencio de 1,5 litros. Perdón, esas no llegaron; no las cargues.

**Respuesta (repeticiones 1, 2, 3):** Agrega cinco botellas de agua visuavicencio de uno coma cinco litros. Perdón, esas no llegaron, no las car

## negar_restacion

Verbo inicial deformado como «Pero está», pero conserva claramente «no se vendieron, no los restes».

**Referencia:** Restá cuatro envases de detergente Magistral de 750 ml. Perdón, no se vendieron; no los restes.

**Respuesta (repeticiones 1, 2, 3):** Pero está cuatro envases de detergentes magistral de setecientos cincuenta mililitros. Perdón, no se vendieron, no los restes

## negar_varias_agregaciones

Conserva arroz Gallo (operación pendiente), el verbo de agregar y las cancelaciones; Sprite → «sprays» deja identidad dudosa.

**Referencia:** Agregá tres Coca Cola comunes de 2 litros, cuatro Sprite comunes de 1,5 litros y cinco paquetes de arroz Gallo de 1 kg. Me equivoque las Coca Cola comunes de 2 litros y las Sprite comunes de 1,5 no las cargues.

**Respuesta (repeticiones 1, 2, 3):** Agrega tres Coca-Cola común es de dos litros, cuatro sprays comunes de uno comas cinco litros y cinco paquetes de arroz gallo de un kilo. Me equivoqué, las Coca-Colas comunes de dos litros y las spray comunes, de uno coma cinco, no las cargues

## negar_varias_restaciones

Crítico: «restá» → «presta», y arroz Gallo → «rosgallo». Mantiene cancelaciones, pero resta de detergente queda ambigua.

**Referencia:** Restá dos Coca Cola Zero de 2 litros, tres paquetes de arroz Gallo de 1 kg y cuatro envases de detergente Magistral de 750 ml. Las Coca Zero y el arroz no se vendieron; no los restes.

**Respuesta (repeticiones 1, 2, 3):** Presta dos Coca-Cola cero de dos litros, tres paquetes de rosgallo de un kilo y cuatro envases de detergente magistral de setecientos cincuenta mililitros. Las cocas cero y el arroz no se vendieron, no los restes.

## negar_agregacion_y_restacion

Deforma Sprite con nombres inconsistentes («spys», «spike») y «no hagas» → «Novas». Conserva razones de cancelación; orden final ambigua.

**Referencia:** Agregá cuatro Sprite comunes de 2 litros y restá dos paquetes de arroz Gallo de 1 kg. Perdón, las Sprite no llegaron y el arroz no se vendió; no hagas ninguna de esas dos operaciones.

**Respuesta (repeticiones 1, 2, 3):** Agrega cuatro spys comunes de dos litros y resta dos paquetes de arroz gallo de un kilo. Perdón, las spike no llegaron y el arroz no se vendió. Novas ninguna de esas dos operaciones

## caso_integral

Conserva corrección tres → dos, cantidades, unidades y todas las cancelaciones explícitas. Sprite → «sprays» y Matarazzo → «matarazos» dejan identificación dudosa. Es mejor en estructura que Whisper Small Q5 y Moonshine Small en este caso concreto, según comparación textual.

**Referencia:** Agregá tres Coca Cola comunes de 2 litros; perdón, eran dos. Agregá cuatro Sprite comunes de 1,5 litros y cinco botellas de agua Villavicencio de 1,5 litros; perdón, no llegó ninguno de esos dos productos, así que no los cargues. Restá dos paquetes de arroz Gallo de 1 kg y tres paquetes de fideos Matarazzo de 500 g. Restá cuatro Coca Cola Zero de 2 litros y cinco envases de detergente Magistral de 750 ml; perdón, ni las Coca Zero ni los detergentes se vendieron. No restes ninguno de esos dos productos. Agregá seis envases de leche La Serenísima de 1 litro y restá dos Sprite comunes de 2 litros. Perdón, la leche no llegó y esas Sprite no se vendieron; no cargues la leche ni restes esas Sprite.

**Respuesta (repeticiones 1, 2, 3):** Agrega tres Coca-Cola comunes de dos litros, perdón, eran dos. Agrega cuatro sprays comunes de uno coma cinco litros y cinco botellas de agua villavicencio de uno comas cinco litros. Perdón, no llegó ninguno de esos dos productos, así que no los cargués. Resta dos paquetes de arroz gallo de un kilo y tres paquetes de fideos matarazos de quinientos gramos. Resta cuatro Coca-Cola, cero de dos litros y cinco envases de detergente magistral de setecientos cincuenta mililitros. Perdón, ni las coca ceros ni los detergentes se vendieron, no restes ninguno de esos dos productos. Agrega seis envases de leche la serenísima, de un litro y resta dos spray comunes de dos litros. Perdón, la leche no llegó y esas sprays no se vendieron. No cargues la leche ni restes esas sprays.

## Conclusión

Kroko agrega una alternativa lista para usar y rápida en esta PC. No mejora el WER global de Whisper Small Q5 (26,81%) ni Moonshine Small (27,71%). Preserva bien la estructura del caso integral, pero falla en acción/cantidad en restar_ambos y deforma otras órdenes. Conviene mantenerlo como candidato; no seleccionarlo sólo por velocidad ni por un único prompt.

No se afinó el padding, la búsqueda ni el vocabulario para mejorar resultados. La configuración utiliza 300 ms de silencio final; algunos finales truncados justifican investigar el cierre del stream en otra prueba, sin atribuir el fallo exclusivamente a los pesos del modelo.

[Alineación de errores y todas las métricas por prompt](../cpu_20261010_173839/prompt_analysis.md)
