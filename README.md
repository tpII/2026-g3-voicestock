# VoiceStock

Sistema de gestión de inventario asistido por voz, pensado para ejecutarse en una Raspberry Pi.

La Raspberry Pi capturará audio, hará Speech-to-Text, se comunicará con un modelo de lenguaje a través de una interfaz independiente del proveedor, validará respuestas estructuradas, administrará el inventario, persistirá datos en SQLite y expondrá una interfaz web.

El proyecto está en una etapa inicial. Ya incluye el servidor de comunicación
de la PC conectado a un servicio de interpretación con proveedor intercambiable
(por ahora un stub), mientras que captura de audio, STT, el modelo de lenguaje,
inventario e interfaz web continúan en desarrollo.

## Requisitos

- Python 3.11 o superior
- Git

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

La Raspberry Pi envía el texto con `HttpInterpretationClient`. El destino y el
timeout se configuran con variables de entorno (por defecto
`http://127.0.0.1:8000` y 10 segundos):

```bash
VOICESTOCK_PC_URL=http://<ip-de-la-pc>:8123 VOICESTOCK_PC_TIMEOUT=10
```

El contrato, el uso del cliente y los ejemplos están en la
[interfaz de comunicación Raspberry Pi–PC](docs/interfaces/pc-communication.md).

## Documentación

- [Guía de contribución](CONTRIBUTING.md)
- [Guía de documentación](docs/guides/documentation-guide.md)
- [Flujo de trabajo de desarrollo](docs/guides/development-workflow.md)
- [Comunicación Raspberry Pi–PC](docs/interfaces/pc-communication.md)
- [Servicio de interpretación](docs/interfaces/interpretation-service.md)
- [Bitácora](docs/bitacora/bitacora.md)

## Licencia

[MIT](LICENSE)
