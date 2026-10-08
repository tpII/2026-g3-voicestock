# VoiceStock

Sistema de gestión de inventario asistido por voz, pensado para ejecutarse en una Raspberry Pi.

La Raspberry Pi capturará audio, hará Speech-to-Text, se comunicará con un modelo de lenguaje a través de una interfaz independiente del proveedor, validará respuestas estructuradas, administrará el inventario, persistirá datos en SQLite y expondrá una interfaz web.

El proyecto está en una etapa inicial. Ya incluye la captura push-to-talk en la
Raspberry Pi y el servidor de comunicación de la PC, conectado a un servicio de
interpretación con proveedor intercambiable (por ahora un stub). STT, el modelo
de lenguaje, inventario e interfaz web continúan en desarrollo. La prueba física
del pulsador y del micrófono USB todavía no se hizo.

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

El servidor recibe texto por HTTP y lo pasa al servicio de interpretación. Por
defecto usa el proveedor `stub` y escucha solamente en localhost:

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

El contrato, la puesta en marcha en la red local y el catálogo de errores con
ejemplos están en la
[interfaz de comunicación Raspberry Pi–PC](docs/interfaces/pc-communication.md).

### Push-to-talk

La Raspberry Pi graba un WAV al pulsar y soltar un botón. La decisión de stack,
el contrato de audio y la prueba en la placa están separados:

- [Decisión de arquitectura](docs/decisions/0003-use-event-driven-gpio-and-sounddevice-for-ptt-capture.md)
- [Interfaz de captura](docs/interfaces/push-to-talk-capture.md)
- [Conexión, configuración y prueba manual](docs/setup/push-to-talk.md)

### Web en la Raspberry Pi

`voicestock-pi-web` levanta la página de marcador de posición y `GET /health`.
En la Raspberry Pi escucha en `192.168.50.1:8000`. En una máquina de desarrollo:

```bash
VOICESTOCK_WEB_HOST=127.0.0.1 voicestock-pi-web
```

El comando es temporal, para desarrollo y validación, hasta que el orquestador
exista. Sin ese runtime el API responde que la aplicación no está lista. La
guía está en [servidor web de la Raspberry Pi](docs/setup/pi-web.md) y el
contrato en [API de la operación pendiente](docs/interfaces/pending-operation-web-api.md).

## Documentación

- [Guía de contribución](CONTRIBUTING.md)
- [Guía de documentación](docs/guides/documentation-guide.md)
- [Flujo de trabajo de desarrollo](docs/guides/development-workflow.md)
- [Comunicación Raspberry Pi–PC](docs/interfaces/pc-communication.md)
- [Servicio de interpretación](docs/interfaces/interpretation-service.md)
- [Captura push-to-talk](docs/interfaces/push-to-talk-capture.md)
- [Prueba manual de push-to-talk](docs/setup/push-to-talk.md)
- [Red Ethernet local](docs/setup/local-network.md)
- [Servidor web de la Raspberry Pi](docs/setup/pi-web.md)
- [API de la operación pendiente](docs/interfaces/pending-operation-web-api.md)
- [Bitácora](docs/bitacora/bitacora.md)

## Licencia

[MIT](LICENSE)
