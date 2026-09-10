# Bitácora

Este documento registra el proceso de diseño, implementación, pruebas e iteraciones de VoiceStock: decisiones técnicas, dudas planteadas a la cátedra y problemas encontrados con sus soluciones, a lo largo del desarrollo.

---

# 01/09/2026

### Avance

Se creó el repositorio del proyecto **VoiceStock**, un sistema de gestión de inventario asistido por voz pensado para ejecutarse en una Raspberry Pi.

---

# 10/09/2026

### Avance

Se armó la base del monorepo, dejando preparado el entorno de desarrollo antes de escribir lógica de aplicación:

- **Python 3.11+** como versión mínima, gestionado con un entorno virtual (`.venv`) creado por `scripts/setup.sh` (Linux / Raspberry Pi) y `scripts/setup.ps1` (Windows).
- **Ruff** para lint y formateo (reglas `E`, `F`, `I`; `line-length = 88`; comillas dobles).
- **Pytest** + **pytest-cov**, con un test de humo (`tests/test_smoke.py`) que valida que el paquete `voicestock` se pueda importar.
- **pre-commit**, con hooks de `pre-commit-hooks` (trailing whitespace, end-of-file, YAML/TOML, detección de claves privadas, conflictos de merge) y de `ruff-pre-commit` (`ruff-check --fix`, `ruff-format`).
- **CI en GitHub Actions** (`.github/workflows/ci.yml`): corre en pushes y Pull Requests hacia `main` y `develop`, instala el proyecto con `pip install -e ".[dev]"` y ejecuta `pre-commit run --all-files` y `pytest --cov=voicestock`. Todavía no hay un umbral mínimo de cobertura.
- Se documentó el flujo de trabajo completo (branching `feature/*` / `fix/*` / `release/*` / `hotfix/*` desde `develop`, Conventional Commits, Squash and Merge) en `CONTRIBUTING.md` y `docs/development-workflow.md`.
- Se dejó `docs/architecture.md` como documento vivo para registrar decisiones de arquitectura a medida que se tomen.
- Se agregó `.env.example` con las variables previstas para la integración con el LLM (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`), todavía sin valores porque el proveedor no está definido.

### Decisiones técnicas

- **Docker queda fuera del arranque inicial.** Las partes que dependen del hardware de la Raspberry Pi (por ejemplo el micrófono) se van a ejecutar de forma nativa al principio, para no sumar la complejidad de contenedores sobre dispositivos físicos. Se podría reconsiderar más adelante para servicios de software o para un LLM local, si aporta un beneficio concreto.
- **SQLite** como motor de persistencia, acorde a un sistema pensado para correr en un único dispositivo (Raspberry Pi), sin necesidad de un servidor de base de datos separado.

### Preguntas

- **En cuanto a la alimentación del prototipo, ¿se busca que sea portable (alimentado por ejemplo a pilas o baterías) o un sistema fijo alimentado por una fuente de pared?**
  La idea es que, al ser algo estático (sin movimiento) por ahora, puede ser alimentación fija. Como objetivo secundario, se puede contemplar que sea portable con powerbank o pilas.

- **En la estructura pensada, la Raspberry Pi se encarga de servir la web, manejar la base de datos, capturar el audio del micrófono y pasarlo a texto, para luego enviarlo a un LLM que procese ese texto y genere un output formateado en JSON que se procesa en la placa (además de un string de confirmación que la placa traduce a audio para pedir confirmación al usuario). En cuanto al LLM, ¿recomiendan usar un modelo local corriendo en alguna de nuestras computadoras con acceso SSH, o utilizar una API de un modelo estilo GPT/Gemini?**
  Ese trade-off se charla en la clase, porque es el corazón de la arquitectura del proyecto.

- **¿Contamos con un parlante o con un buzzer? Con parlante se pediría la confirmación por audio; con buzzer simplemente se emitiría un sonido indicando que se registró y luego se pediría la confirmación por la web.**
  En principio no sería necesario el parlante. Se deja como objetivo secundario.
