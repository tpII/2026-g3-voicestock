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
| `VOICESTOCK_PI_URL` | Base HTTP de la Raspberry. Por defecto `http://192.168.50.1:8000` |
| `VOICESTOCK_CATALOG_TIMEOUT_SECONDS` | Timeout del `GET /api/v1/catalog`. Por defecto 5 |
| `VOICESTOCK_GROQ_API_KEY` | Credencial. Si falta, se lee `GROQ_API_KEY` |
| `VOICESTOCK_STT_MODEL` | Por defecto `whisper-large-v3-turbo` |
| `VOICESTOCK_LLM_MODEL` | Por defecto `openai/gpt-oss-20b` |
| `VOICESTOCK_STT_TIMEOUT_SECONDS` | Por defecto 20 |
| `VOICESTOCK_LLM_TIMEOUT_SECONDS` | Por defecto 20 |
| `VOICESTOCK_PC_HOST` | Bind existente de `ServerSettings` |
| `VOICESTOCK_PC_PORT` | Bind existente de `ServerSettings` |

La Raspberry no necesita la clave. El timeout del catálogo
(`VOICESTOCK_CATALOG_TIMEOUT_SECONDS`, 5 por defecto) es solo de ese GET.
Los de STT y del modelo siguen en 20. `VOICESTOCK_PC_TIMEOUT`, en la
Raspberry, tiene que cubrir la transferencia más el catálogo, la
transcripción y la interpretación. El valor por defecto es 10 segundos y
puede no alcanzar. Hay que medirlo con un WAV real; no es un SLA.

La plantilla sin secretos está en
`config/pc-audio-pipeline.env.example`. No commitees la clave.

## Arranque en la PC de la celda

Desde el entorno del proyecto, con la clave ya exportada:

```bash
VOICESTOCK_AUDIO_PIPELINE=groq \
VOICESTOCK_PI_URL=http://192.168.50.1:8000 \
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

En modo `groq`, el proceso abre el cliente de Groq y el cliente del catálogo
cuando el servidor arranca, y cierra ambos al terminar. No descarga el
catálogo en el arranque: la Raspberry puede levantarse después. La primera
interpretación hace `GET /api/v1/catalog` antes de Whisper. Si esa llamada
falla, no hay transcripción ni llamada al modelo, y el resultado es
`catalog_unavailable`. El pedido siguiente vuelve a intentar la sincronización.

Un `200` valida la versión, la revisión, el `ETag`, los productos y que cada
uno sea identificable por sus atributos canónicos. Recién entonces reemplaza
el prompt y el matcher, juntos. Un `304` con el mismo `ETag` reutiliza ese
par. Un snapshot inválido no pisa el anterior, pero el audio de ese pedido
falla igual: no se interpreta con el catálogo viejo. El modo `stub` no abre
ninguno de los dos clientes y no exige la Raspberry ni la clave de Groq.

Whisper y el modelo de interpretación comparten el cliente de Groq. El
timeout del catálogo es independiente. La transcripción y la interpretación
corren fuera del bucle de eventos de HTTP: una llamada lenta no deja muda la
otra ruta.

## Catálogo y contrato

Antes de cada WAV, la PC pide `GET /api/v1/catalog` a `VOICESTOCK_PI_URL`.
El cuerpo es el snapshot de productos activos. El prompt copia `nombre`,
`marca`, `variante`, `presentacion` y la lista `alias`. Un alias le permite
al modelo reconocer una frase, pero el contrato debe llevar los atributos
canónicos, no el alias y no un `product_id`. `map_draft` arma el
`ContractPayload` versión 1. La Raspberry sigue asignando `product_id`.

Si el texto no distingue una fila, el servidor responde error de servicio
`ambiguous_product` y no elige una presentación. «Agregá arroz» sigue siendo
ambiguo cuando hay más de un arroz. Un alias que corresponde a una sola fila
puede hacer que el modelo complete los atributos de esa fila. El matcher
local no resuelve alias por su cuenta: compara los atributos que devolvió el
modelo.

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

- No hay persistencia de inventario ni caché del catálogo en disco.
- Los tests automáticos simulan Groq y la Raspberry. No demuestran la API
  real ni la prueba física de punta a punta.
- El texto `POST /api/v1/interpret` sigue el proveedor de
  `VOICESTOCK_INTERPRETATION_PROVIDER`, que por defecto es `stub`. Ese
  endpoint no sincroniza el catálogo.
- El alcance de esta versión es una sola operación `add_stock` o
  `remove_stock`.
