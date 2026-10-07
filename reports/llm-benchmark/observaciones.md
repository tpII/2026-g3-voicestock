# Observaciones del benchmark de precisión

Este resumen se centra en tres modelos de interés. Distingue los aciertos del modelo de los errores de API: un 100 % sobre las solicitudes exitosas no equivale necesariamente a 10/10 de punta a punta.

## Modelos destacados

| Modelo | Proveedor | Contrato reportado | Resultado en 10 casos | Corrida |
| --- | --- | --- | --- | --- |
| `qwen3:4b-instruct` | Ollama local | `contract-copy.txt` | **10/10** | [20260929_211830](precision_20260929_211830/benchmark_report.md) |
| `openai/gpt-oss-20b` | Groq | `contract.txt` | **10/10** | [20260929_213654](precision_20260929_213654/benchmark_report.md) |
| `gemini-3.6-flash` | Gemini | `contract-copy.txt` | **9/9 respuestas correctas; 1 error de API (503)** | [20260929_202819](precision_20260929_202819/benchmark_report.md) |

Gemini 3.6 Flash no logró 10/10 en una misma corrida completa: obtuvo **9/10 de punta a punta** porque un caso no recibió respuesta. Ese error no demuestra que haya interpretado mal el caso.

## Comparación con modelos más grandes

`openai/gpt-oss-120b`, más grande que GPT-OSS 20B, hizo [8/10 con `contract.txt`](precision_20260929_213303/benchmark_report.md): omitió una resta válida en `negar_varias_restaciones` y una agregación válida en `caso_integral`. GPT-OSS 20B resolvió ambos casos en su corrida de 10/10. Ambos usaron los mismos casos, esquema JSON estricto y `reasoning_effort: low`; el tamaño no garantizó mejores resultados en este test.

Estos tres modelos son el **foco de este resumen, no una lista exhaustiva** de corridas perfectas: [Qwen 3.8 27B también obtuvo 10/10](precision_20260929_212812/benchmark_report.md) en una corrida con otro contrato (`contract-copy-copy.txt`). Omitir ese dato llevaría a una conclusión falsa sobre qué modelos pudieron completar los casos.

## Cómo interpretar estos resultados

El esquema estricto obliga a producir un JSON con la forma pedida, pero no garantiza interpretar correctamente correcciones y cancelaciones. Un error de API tampoco demuestra un fallo de interpretación. Por eso conviene mirar **exactitud total**, **solicitudes exitosas** y **contrato usado** por separado.

Diez ejemplos son una muestra pequeña, y varios contratos se ajustaron durante las pruebas. Para elegir un modelo de Voice Stock hace falta evaluar frases nuevas, no usadas para ajustar el prompt, y repetir corridas con el mismo contrato y configuración. El reporte actual guarda el **nombre** del contrato, no una copia de su contenido en el momento de ejecutar; esto limita la reproducibilidad exacta si el archivo cambia después.
