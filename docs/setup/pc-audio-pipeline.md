# Pipeline de audio en la PC

El servidor de la PC puede seguir en el stub de diagnóstico o transcribir un
WAV, interpretarlo y devolver un contrato versión 1. La confirmación en la
Raspberry sigue usando `ProvisionalOperationExecutor`: informa éxito y no
persiste stock.

## Selección

`VOICESTOCK_AUDIO_PIPELINE=stub` es el valor por defecto. `interpret-audio`
responde con `received_audio` y no llama a Groq.

`VOICESTOCK_AUDIO_PIPELINE=groq` usa Whisper en Groq y después
`openai/gpt-oss-20b`. La ruta HTTP no cambia:
`POST /api/v1/interpret-audio` con `Content-Type: audio/wav`.

## Variables

| Variable | Uso |
| --- | --- |
| `VOICESTOCK_AUDIO_PIPELINE` | `stub` o `groq` |
| `VOICESTOCK_CATALOG_PATH` | JSON del catálogo. Obligatorio en `groq` |
| `VOICESTOCK_GROQ_API_KEY` | Credencial. Si falta, se lee `GROQ_API_KEY` |
| `VOICESTOCK_STT_MODEL` | Por defecto `whisper-large-v3-turbo` |
| `VOICESTOCK_LLM_MODEL` | Por defecto `openai/gpt-oss-20b` |
| `VOICESTOCK_STT_TIMEOUT_SECONDS` | Por defecto 20 |
| `VOICESTOCK_LLM_TIMEOUT_SECONDS` | Por defecto 20 |
| `VOICESTOCK_PC_HOST` | Bind existente de `ServerSettings` |
| `VOICESTOCK_PC_PORT` | Bind existente de `ServerSettings` |

La Raspberry no necesita la clave. El timeout del cliente,
`VOICESTOCK_PC_TIMEOUT`, tiene que cubrir la transferencia más la
transcripción y la interpretación. Diez segundos puede no alcanzar cuando
cada etapa espera hasta 20. Hay que medirlo con un WAV real; no es un SLA.

La plantilla sin secretos está en
`config/pc-audio-pipeline.env.example`. No commitees la clave.

## Arranque en la PC de la celda

Desde el entorno del proyecto, con la clave ya exportada:

```bash
VOICESTOCK_AUDIO_PIPELINE=groq \
VOICESTOCK_CATALOG_PATH=/ruta/catalogo.json \
VOICESTOCK_PC_HOST=192.168.50.2 \
VOICESTOCK_PC_PORT=8000 \
voicestock-pc-server
```

El stub:

```bash
VOICESTOCK_AUDIO_PIPELINE=stub \
VOICESTOCK_PC_HOST=192.168.50.2 \
VOICESTOCK_PC_PORT=8000 \
voicestock-pc-server
```

En modo `groq`, el proceso abre un solo cliente HTTP cuando el servidor
arranca y lo cierra al terminar. Whisper y el modelo de interpretación lo
comparten. El modo `stub` no lo crea. La transcripción y la interpretación
corren fuera del bucle de eventos de HTTP: una llamada lenta no deja muda la
otra ruta.

## Catálogo y contrato

El modelo debe copiar `nombre`, `marca`, `variante` y `presentacion` del
catálogo. `map_draft` arma el `ContractPayload` versión 1. La Raspberry
sigue siendo quien asigna `product_id`.

Si el texto no distingue una fila, el servidor responde error de servicio
`ambiguous_product` y no elige una presentación. Con el catálogo de las dos
presentaciones de Arroz Marolio, «agregá dos paquetes de arroz» es ambiguo.
Un pedido que nombra la presentación de 1 kg puede identificarse solo si el
modelo copia `presentacion` igual a `1 kg`.

Un comando con cero operaciones o con más de una no se recorta: el resultado
es `unsupported_command`.

Una falla de STT o del modelo no produce un contrato exitoso. Los detalles
no incluyen la clave ni el cuerpo del audio.

## Probar un WAV local

```bash
curl -sS -D - \
  -H "Content-Type: audio/wav" \
  --data-binary @grabacion.wav \
  http://127.0.0.1:8000/api/v1/interpret-audio
```

El sobre exterior es el transporte. Adentro, `payload.status` es el
resultado del servicio. En éxito, el contrato y `recognized_text` viajan
juntos. `PcResponseInterpreter` separa ese texto antes de validar.

## Límites

- No hay persistencia de inventario.
- Los tests automáticos simulan Groq. No demuestran la API real ni la
  prueba física de punta a punta.
- El texto `POST /api/v1/interpret` sigue el proveedor de
  `VOICESTOCK_INTERPRETATION_PROVIDER`, que por defecto es `stub`.
- El alcance de esta versión es una sola operación `add_stock` o
  `remove_stock`.
