# VoiceStock

Sistema de gestión de inventario asistido por voz, pensado para ejecutarse en una Raspberry Pi.

La Raspberry Pi captura audio y lo envía a la PC. El reconocimiento de voz y
la interpretación con un modelo de lenguaje corren, conceptualmente, en la PC.
La Raspberry Pi valida el contrato, mantiene una sola operación pendiente en
memoria y muestra la página para confirmarla o cancelarla. El inventario en
SQLite todavía no se modifica.

El proyecto ya incluye la captura push-to-talk, el cliente HTTP, el ciclo
`PendingOperationFlow`, el comando `voicestock-pi` y la página de
confirmación. El servidor de la PC sigue usando un handler de audio
provisional. Confirmar en la página no modifica el inventario. El recorrido
completo de voz, desde el micrófono hasta un contrato real, no está cerrado.

## Requisitos

- Python 3.11 o superior
- Git

## Estructura del código

El código está dividido según la máquina donde corre
([ADR-0002](docs/decisions/0002-split-source-by-runtime-pc-pi-shared.md)):

```text
src/
├── pc/       lo que corre en la PC: servidor HTTP e interpretación
├── pi/       lo que corre en la Raspberry Pi: push-to-talk, cliente y web
└── shared/   contratos que intercambian ambas (TransportEnvelope)
```

`pc` y `pi` no se importan entre sí y `shared` no importa a ninguno; un test lo
verifica. Los tests siguen la misma división (`tests/pc`, `tests/pi`,
`tests/shared`, más `tests/integration` para pruebas que usan ambos lados).

## Arranque rápido

Si usás Conda, activá tu entorno antes de ejecutar setup; se instalará ahí.
Sin Conda activo, los scripts crean o reutilizan `.venv`.

```bash
git clone <url-del-repositorio>
cd voicestock
```

Windows:

```powershell
.\scripts\setup.ps1
.venv\Scripts\Activate.ps1
```

Linux / Raspberry Pi:

```bash
./scripts/setup.sh
source .venv/bin/activate
```

Luego:

```bash
ruff check .
pytest
```

### Servidor de comunicación de la PC

El servidor recibe por HTTP texto, que pasa al servicio de interpretación, y
grabaciones WAV del push-to-talk, que pasa a un handler de audio sustituible
(hoy un stub, después la transcripción por API). Por defecto usa el proveedor
`stub` y escucha solamente en localhost:

```bash
voicestock-pc-server
```

Para exponerlo en la red local y elegir otro puerto:

```bash
VOICESTOCK_PC_HOST=0.0.0.0 VOICESTOCK_PC_PORT=8123 voicestock-pc-server
```

### Cliente de la Raspberry Pi

La Raspberry Pi envía el texto con `HttpInterpretationClient`. Para probar el
viaje completo desde una terminal, con el servidor corriendo:

```bash
voicestock-pi-client "agregá dos paquetes de arroz"
```

El destino y el timeout se configuran con variables de entorno (por defecto
`http://127.0.0.1:8000` y 10 segundos):

```bash
VOICESTOCK_PC_URL=http://<ip-de-la-pc>:8123 VOICESTOCK_PC_TIMEOUT=10 \
  voicestock-pi-client "agregá dos paquetes de arroz"
```

Para enviar una grabación en lugar de texto:

```bash
voicestock-pi-client --audio grabacion.wav
```

El contrato, la puesta en marcha en la red local y el catálogo de errores con
ejemplos están en la
[interfaz de comunicación Raspberry Pi–PC](docs/interfaces/pc-communication.md)
y, para el audio, en la
[interfaz de audio Raspberry Pi–PC](docs/interfaces/pc-audio-communication.md).

### Push-to-talk

La Raspberry Pi graba un WAV al pulsar y soltar un botón. La decisión de stack,
el contrato de audio y la prueba en la placa están separados:

- [Decisión de arquitectura](docs/decisions/0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md)
- [Interfaz de captura](docs/interfaces/push-to-talk-capture.md)
- [Conexión, configuración y prueba manual](docs/setup/push-to-talk.md)

Con `--send-to-pc`, `voicestock-pi-ptt` envía cada grabación a la PC y muestra
la respuesta
([interfaz de audio](docs/interfaces/pc-audio-communication.md#sending-push-to-talk-recordings)).

### Ciclo de operación en la Raspberry Pi

`voicestock-pi` es el proceso que junta el botón, el micrófono, el cliente
hacia la PC, la validación del contrato y la página. El pin, el micrófono, el
directorio de grabaciones y el catálogo JSON son obligatorios. En desarrollo:

```bash
VOICESTOCK_PC_URL=http://127.0.0.1:8000 \
VOICESTOCK_WEB_HOST=127.0.0.1 \
VOICESTOCK_WEB_PORT=8123 \
  voicestock-pi \
  --pin 17 \
  --bounce-time 0.05 \
  --input-device "USB Audio" \
  --output-directory recordings \
  --catalog path/to/catalog.json
```

`USB Audio` es un ejemplo de nombre de dispositivo, no un valor fijo.

- [Arquitectura del ciclo](docs/architecture/pending-operation-flow.md)
- [Cómo ejecutarlo](docs/setup/pi-runtime.md)
- [ADR-0008: un solo orquestador](docs/decisions/0008-use-a-single-raspberry-pi-operation-workflow.md)

### Web en la Raspberry Pi

Con `voicestock-pi`, la página queda en el mismo proceso. En la Raspberry Pi
escucha en `192.168.50.1:8000`. Desde la PC: `http://192.168.50.1:8000/`.
Esas direcciones son las de la red Wi-Fi aislada; el procedimiento está en
la [guía de red local](docs/setup/local-network.md). La validación física de
esa red sigue pendiente. El plan para hacerla, todavía sin ejecuciones, está
en la [campaña de validación de la Raspberry Pi](docs/testing/raspberry-validation/README.md).

`voicestock-pi-web` sigue disponible para abrir la página sin el ciclo. En
ese caso `GET /health` responde y el API dice que la aplicación no está
lista. `GET /health` solo indica que el servidor HTTP está vivo.

```bash
VOICESTOCK_WEB_HOST=127.0.0.1 VOICESTOCK_WEB_PORT=8123 voicestock-pi-web
```

- [Cómo instalar y abrir solo la página](docs/setup/pi-web.md)
- [Contrato HTTP](docs/interfaces/pending-operation-web-api.md)
- [Qué muestra la página](docs/interfaces/pending-operation-web-ui.md)

## Estado de la evaluación de voz

El ciclo implementado envía el WAV a la PC. El reconocimiento corre,
conceptualmente, en la PC; el servidor todavía usa el handler provisional.
La evaluación de Whisper en la Raspberry Pi y de los modelos de lenguaje queda
como registro:

- [Integración de captura e interpretación](docs/architecture/audio-interpretation-integration.md)
- [Evaluación de Speech-to-Text](docs/research/speech-to-text-engine-evaluation.md)
- [ADR-0005](docs/decisions/0005-use-whisper-small-q5-for-offline-stt.md)

## Documentación

- [Claves locales de API y carga automática](docs/setup/api-keys.md)
- [Modelos para evaluación de Speech-to-Text](docs/setup/speech-to-text-models.md)
- [Benchmark de Speech-to-Text en CPU](docs/testing/speech-to-text-benchmark.md)
- [Benchmark audio → STT → LLM → JSON](docs/testing/audio-stt-llm-benchmark.md)
- [Prueba de prompts con STT en Raspberry por SSH](docs/testing/raspberry-stt-ssh.md)
- [Interfaz pública de Speech-to-Text](docs/interfaces/speech-to-text.md)
- [ADR-0005: Whisper Small Q5 pendiente de validación en Pi](docs/decisions/0005-use-whisper-small-q5-for-offline-stt.md)
- [Integración de captura, STT e interpretación](docs/architecture/audio-interpretation-integration.md)
- [Ciclo de operación en la Raspberry Pi](docs/architecture/pending-operation-flow.md)
- [ADR-0008: un solo orquestador del ciclo](docs/decisions/0008-use-a-single-raspberry-pi-operation-workflow.md)
- [Runtime integrado de la Raspberry Pi](docs/setup/pi-runtime.md)

- [Guía de contribución](CONTRIBUTING.md)
- [Guía de documentación](docs/guides/documentation-guide.md)
- [ADR-0004: API inicial y alternativa local sustituible](docs/decisions/0004-use-api-provider-for-stock-interpretation.md)
- [Investigación: estrategia y evaluación de interpretación](docs/research/stock-interpretation-strategy-and-evaluation.md)
- [Flujo de trabajo de desarrollo](docs/guides/development-workflow.md)
- [Comunicación Raspberry Pi–PC](docs/interfaces/pc-communication.md)
- [Envío de audio Raspberry Pi–PC](docs/interfaces/pc-audio-communication.md)
- [Servicio de interpretación](docs/interfaces/interpretation-service.md)
- [ADR-0006: Identificación de productos por coincidencia única de atributos](docs/decisions/0006-identify-products-by-unique-attribute-match.md)
- [ADR-0007: Envío del audio push-to-talk como WAV crudo por HTTP](docs/decisions/0007-send-push-to-talk-audio-as-raw-wav-over-http.md)
- [Contrato de operación (JSON versionado y validación)](docs/interfaces/operation-contract.md)
- [Captura push-to-talk](docs/interfaces/push-to-talk-capture.md)
- [Prueba manual de push-to-talk](docs/setup/push-to-talk.md)
- [Red local VoiceStock](docs/setup/local-network.md)
- [Servidor web de la Raspberry Pi](docs/setup/pi-web.md)
- [API de la operación pendiente](docs/interfaces/pending-operation-web-api.md)
- [Página de la operación pendiente](docs/interfaces/pending-operation-web-ui.md)
- [Bitácora](docs/bitacora/bitacora.md)
- [Campaña de validación de la Raspberry Pi](docs/testing/raspberry-validation/README.md)

## Licencia

[MIT](LICENSE)
