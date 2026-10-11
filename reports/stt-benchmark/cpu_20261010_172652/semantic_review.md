# Revisión de sentido: Moonshine en español

Pruebas en PC, no en Raspberry Pi. Diez audios por modelo, un calentamiento por audio y tres repeticiones medidas: 60/60 solicitudes medidas correctas en ejecución. Esto no significa 60 transcripciones correctas en contenido.

Evaluación cualitativa comparando todas las respuestas medidas contra el texto del prompt, sin escucha/verificación humana del audio ni ejecución contra un parser de inventario. Las tres respuestas medidas fueron idénticas para cada combinación de modelo y prompt. No se calcula un porcentaje de éxito semántico automático.

## Resultados generales

| Modelo | WER % | CER % | Media s | Máximo s | RSS pico MiB | CPU media % |
| --- | --- | --- | --- | --- | --- | --- |
| moonshine_tiny_es | 32.23 | 21.58 | 1.08 | 5.13 | 288.47 | 1233.54 |
| moonshine_small_es | 27.71 | 18.87 | 2.33 | 9.01 | 501.81 | 1322.91 |

WER estricto incluye diferencias como «2»/«dos», «750 ml»/«setecientos cincuenta mililitros» y tildes; esos errores de escritura no necesariamente alteran el sentido. Moonshine usa CPUExecutionProvider con hilos internos por defecto y consumió el equivalente aproximado de 12–13 núcleos. Whisper usa cuatro hilos. Los tiempos no representan una comparación con igual paralelismo ni predicen el rendimiento en Pi 3. RSS es memoria residente del proceso, no el tamaño del modelo: archivos Tiny 30,82 MiB y Small 116,16 MiB.

## Revisión por prompt

| Prompt | WER Tiny / Small % | Tiny: sentido | Small: sentido |
| --- | --- | --- | --- |
| solo_agregar | 37.50 / 37.50 | Identidad dudosa: Sprite → «pryt». Cantidades y volúmenes conservados. | Identidad dudosa: Sprite → «sprays». Cantidades y volúmenes conservados. |
| solo_restar | 33.33 / 33.33 | Coherente: restar dos paquetes de arroz Gallo de un kilo. | Coherente: restar dos paquetes de arroz Gallo de un kilo. |
| restar_ambos | 52.94 / 35.29 | Crítico: «dos Coca Cola» → «tosco cacola»; se pierde la cantidad dos de la primera resta. La segunda operación se conserva. | Coherente: conserva ambas restas y cantidades; «cero» y unidades escritas con palabras elevan el WER. |
| corregir_cantidad | 18.18 / 18.18 | Corrección conservada: tres → dos. «agregad» es una variante reconocible del verbo. | Coherente: agrega tres y corrige a dos. |
| negar_agregacion | 29.41 / 35.29 | Nombre de agua deformado: «visualicencia». Conserva «esas no llegaron no las cargues», por lo que la cancelación es clara. | Nombre de agua deformado: «a visodicencio». Conserva la cancelación completa. |
| negar_restacion | 18.75 / 31.25 | Coherente: conserva cuatro envases y «no se vendieron no los restes». | Coherente: conserva cuatro envases y la cancelación. «detergentes» cambia la forma del nombre. |
| negar_varias_agregaciones | 34.88 / 27.91 | Crítico para identificar la operación sobreviviente: arroz Gallo → «arroga sho». Mantiene el verbo de agregar y las cancelaciones de Coca Cola y Sprite. | Mantiene el verbo, el arroz Gallo y las cancelaciones. Sprite → «spray» deja identidad dudosa, aunque la referencia de cancelación es consistente. |
| negar_varias_restaciones | 35.14 / 27.03 | Crítico: «restá» → «presta» y arroz Gallo → «arroja sho». La cancelación de Coca Cola y arroz se conserva; restar detergente queda ambiguo por el verbo. | Crítico: «restá» → «presta». Conserva nombres y cancelaciones, pero la resta de detergente queda ambigua por el verbo. |
| negar_agregacion_y_restacion | 28.57 / 22.86 | Ambiguo: Sprite → «spray» / «spain», arroz Gallo → «arrojacho» y «no hagas» → «no das». Las razones de cancelación son reconocibles; no es una orden final limpia. | Ambiguo: Sprite → «sprays» / «espéim» y «no hagas» → «no das». Conserva arroz Gallo y las razones de cancelación, pero deforma la orden final. |
| caso_integral | 31.30 / 25.95 | Conserva «perdón eran dos» y la mayoría de órdenes, pero arroz Gallo y otros nombres se deforman. «esas Sprite no se vendieron» → «esas espeñas se vendieron» pierde una negación; la instrucción posterior «ni restes esas sprite» conserva la cancelación. No es confiable sin interpretación adicional. | Conserva la corrección a dos, arroz Gallo y más nombres que Tiny. Crítico: «así que no los cargues» → «así lleno los cargues» pierde la prohibición de cargar Sprite y agua. La cláusula previa «no llevo ninguno» sigue sugiriendo falta de llegada, pero no permite considerar la orden inequívoca. |

## Conclusión

Small mejora la transcripción literal global frente a Tiny (WER 27,71% vs 32,23%), tarda más y ocupa más RSS. Ambos preservan la corrección inicial del caso integral que Whisper Small Q5_1 había omitido, pero agregan otros errores críticos. Small no supera el WER de Whisper Small Q5_1 (26,81%) ni su CER (16,75%). Whisper Base conserva el menor CER entre estos candidatos (15,93%). Ninguno permite afirmar que todas las órdenes sean inequívocas.

Recomendación: mantener Moonshine Small como candidato adicional de precisión y Tiny como candidato de consumo; antes de elegir para Pi 3, limitar/comprobar paralelismo y medir allí. La prueba con nombres reales, correcciones y negaciones sigue siendo decisiva.

[Transcripciones completas y alineación de errores](prompt_analysis.md)
[Datos originales de todas las solicitudes](raw_transcriptions.json)
