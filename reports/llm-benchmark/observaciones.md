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

Las notas históricas mencionan corridas adicionales de GPT-OSS 120B y
Qwen 3.8 27B, pero `precision_20260929_213303` y
`precision_20260929_212812` no están versionadas en este repositorio. Sus
resultados no se usan como evidencia verificable de una comparación o ranking.
Los resultados no permiten atribuir la precisión solamente al tamaño del modelo.

## Cómo interpretar estos resultados

El esquema estricto obliga a producir un JSON con la forma pedida, pero no garantiza interpretar correctamente correcciones y cancelaciones. Un error de API tampoco demuestra un fallo de interpretación. Por eso conviene mirar **exactitud total**, **solicitudes exitosas** y **contrato usado** por separado.

`contract.txt` y `contract-copy.txt` se verificaron idénticos byte por byte el 07/10/2026; sus nombres distintos no implican instrucciones distintas para Qwen, GPT-OSS 20B y Gemini. Ambos tienen SHA-256 `6da3c4cdadc485dcb6d39b6eac3c825f2bd7edf11c2b839b1d4cca5ca4c087f5`. No corresponde exigir repetir esas corridas por la diferencia de nombres.

Diez ejemplos son una muestra pequeña. La evaluación de frases nuevas, no usadas para ajustar el prompt, sigue siendo una ampliación posible de la cobertura. El reporte actual guarda el **nombre** del contrato, no una copia de su contenido en el momento de ejecutar; esto limita la reproducibilidad exacta si el archivo cambia después.


## Estrategia para este PR

Se prioriza una API externa (Groq o Gemini según configuración), con local
como segunda opción. Los límites definidos el 09/10/2026 son 8 s por solicitud
para API y 40 s y 3 GB RAM para local. Las medias informadas están por debajo
de los límites de latencia, pero no prueban el límite en cada solicitud.
El pico local histórico de aproximadamente 3,132 MB no demuestra cumplimiento
de 3 GB; el benchmark de precisión no mide RAM.
