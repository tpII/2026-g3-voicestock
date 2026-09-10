# VoiceStock

Sistema de gestión de inventario asistido por voz, pensado para ejecutarse en una Raspberry Pi.

La Raspberry Pi capturará audio, hará Speech-to-Text, se comunicará con un modelo de lenguaje a través de una interfaz independiente del proveedor, validará respuestas estructuradas, administrará el inventario, persistirá datos en SQLite y expondrá una interfaz web.

Este repositorio está en la etapa inicial: todavía no hay lógica de aplicación. Lo que hay es la base del monorepo (Python 3.11, Ruff, Pytest, pre-commit, CI y la guía de contribución).

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

## Documentación

- [Guía de contribución](CONTRIBUTING.md)
- [Flujo de trabajo de desarrollo](docs/development-workflow.md)
- [Arquitectura](docs/architecture.md)
- [Bitácora](docs/bitacora.md)

## Licencia

[MIT](LICENSE)
