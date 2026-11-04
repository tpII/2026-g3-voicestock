# Revisión de resultados

Se completaron los veinte recorridos: diez audios por modelo. No quedaron
solicitudes fallidas. Los límites TPM se resolvieron esperando dos segundos
entre intentos, sin repetir el STT cuando el límite provenía del LLM.

| Modelo STT | JSON exacto | STT medio | LLM medio | Total medio con esperas |
|---|---:|---:|---:|---:|
| Whisper Large V3 | 9/10 | 1,034 s | 0,782 s | 4,168 s |
| Whisper Large V3 Turbo | 10/10 | 0,980 s | 0,567 s | 5,813 s |

Los intentos exitosos incluyen red y respuesta, no sólo inferencia remota.
Turbo acumuló 20 reintentos y 40 s de espera; V3, 11 y 22 s. Por eso el total
con esperas no permite afirmar que Turbo sea más lento como modelo.

## Transcripciones y error observado

Comparadas con las referencias de texto, ambas alternativas preservaron las
acciones, cantidades, correcciones y cancelaciones de los diez audios.
Se observaron diferencias menores como “Coca Cola Cola Zero” en V3 o
“Sprites”, “Cero”, números en palabras y variantes de puntuación.
Esta revisión no reemplaza la escucha y verificación humana de las referencias.

En caso_integral, Large V3 conservó “perdón, eran dos” y la cancelación de
Sprite/agua. Sin embargo, GPT devolvió agregar cinco aguas y omitió agregar dos
Coca Cola comunes. El error visible corresponde a la interpretación LLM de una
transcripción que contenía la información necesaria. Con Turbo, GPT produjo las
tres operaciones esperadas: agregar dos Coca Cola, restar dos arroces y tres
fideos. Una única corrida no establece una ventaja de precisión general.

Los seis casos básicos y habituales produjeron JSON correctos con ambos STT.
