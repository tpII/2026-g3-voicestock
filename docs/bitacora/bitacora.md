# Bitácora

Este documento registra el proceso de diseño, implementación, pruebas e iteraciones de VoiceStock: decisiones técnicas, dudas planteadas a la cátedra y problemas encontrados con sus soluciones, a lo largo del desarrollo.

---

## 01/09/2026

### Avance

Se creó el repositorio del proyecto **VoiceStock**, un sistema de gestión de inventario asistido por voz pensado para ejecutarse en una Raspberry Pi.

---

## 10/09/2026

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

## 17/09/2026

### Avance

Se realizó la guía de documentación del proyecto (disponible en [Guía de documentación](../guides/documentation-guide.md)). Además, se organizaron los archivos de documentación ya existentes en el lugar correspondiente del repositorio: el flujo de trabajo quedó en `docs/guides/development-workflow.md` y la bitácora en `docs/bitacora/bitacora.md`. Se comenzó a definir las tareas necesarias para las diferentes áreas del proyecto; se utilizará la plataforma ClickUp como centro de gestión y se adoptó la convención 1 tarea = 1 commit.

---

## 30/09/2026

### Avance

Se evaluaron las alternativas para la comunicación entre la Raspberry Pi y la PC
en la red local aislada. La comparación incluyó HTTP, WebSocket, gRPC y un
protocolo TCP propio, considerando simplicidad, recursos, latencia, manejo de
errores, testabilidad y desacoplamiento respecto de `InterpretationService`.

La investigación quedó registrada en
[Raspberry Pi–PC communication protocol comparison](../research/raspberry-pi-pc-communication.md)
y la decisión estable en
[ADR-0001](../decisions/0001-use-http-json-for-pi-pc-communication.md).

### Decisiones técnicas

- Se eligió **HTTP/1.1 con JSON UTF-8** para el intercambio request/response del
  MVP.
- La Raspberry Pi actuará como cliente y la PC como servidor dentro de la red
  local.
- La capa de transporte será responsable únicamente de
  `TransportEnvelope<T>`; el payload permanecerá opaco y podrá transportar
  `ServiceResult<ContractPayload>` sin que la comunicación conozca su semántica.
- El framework HTTP, el endpoint y el esquema ejecutable definitivo se
  resolverán en la tarea de implementación del servidor.

### Implementación

Se implementó el primer servidor de comunicación de la PC con **FastAPI** y
**Uvicorn**. El endpoint versionado `POST /api/v1/interpret` recibe texto
reconocido, invoca un handler sustituible y devuelve un
`TransportEnvelope<T>` sin inspeccionar la semántica del payload.

El servidor incluye un stub ejecutable, configuración de host y puerto mediante
variables de entorno y respuestas tipadas para JSON inválido, request inválido,
tipo de contenido no soportado, fallos del handler y errores de serialización.

Se agregaron 20 tests del nuevo módulo, además del test de humo existente. La
suite completa alcanzó **21 tests aprobados** y **92 % de cobertura**. También se
realizó una prueba HTTP real contra el servidor local, verificando una respuesta
exitosa y el rechazo de un request inválido.

---

## 01/10/2026

### Implementación

Se implementó el núcleo de `InterpretationService`, independiente del proveedor
que realice la interpretación. El servicio resuelve el proveedor activo desde un
registro, le delega el texto reconocido y siempre devuelve un `ServiceResult`
tipado, incluso cuando la entrada es inválida o el proveedor falla.

La interfaz está documentada en
[InterpretationService interface](../interfaces/interpretation-service.md).

### Decisiones técnicas

- Los proveedores implementan un único método `interpret(text)`. Un modelo
  local y una API externa entran en el mismo puerto, porque cada proveedor
  maneja su propia configuración, red y timeouts.
- `ServiceResult` distingue éxito y tres categorías de error estables:
  `invalid_input`, `provider_not_configured` y `provider_failure`. El campo
  `detail` es solo diagnóstico.
- Cualquier excepción inesperada del proveedor se informa como
  `provider_failure` sin exponer el mensaje interno.
- Un error del servicio es un resultado transportado con éxito: la capa HTTP no
  lo convierte en error de transporte.
- El proveedor activo se elige con `VOICESTOCK_INTERPRETATION_PROVIDER`
  (por defecto `stub`). Un nombre vacío o no registrado no rompe el arranque:
  cada llamada devuelve `provider_not_configured`.
- El servicio todavía no está conectado al servidor HTTP; eso corresponde a
  `InterpretationService-02`.

### Pruebas

Se agregaron 25 tests que usan solamente proveedores en memoria, sin acceso a
red, incluyendo la sustitución de proveedor y un chequeo de imports que
garantiza que el módulo no depende de HTTP ni de otro transporte. La suite
completa alcanzó **46 tests aprobados** y **96 % de cobertura**.

### Problemas encontrados

- Al agregar `tests/interpretation/test_settings.py`, Pytest falló porque ya
  existía un archivo con el mismo nombre en `tests/communication/` y las
  carpetas de tests no son paquetes. Se resolvió usando nombres de archivo
  únicos.
- El servidor MCP oficial de ClickUp devolvió un error de límite de uso al
  conectarlo desde Claude Code. Se optó por acceder a la API REST de ClickUp
  con un token personal guardado fuera del repositorio.

### Integración servidor–servicio

Se conectó `InterpretationService` al servidor de comunicación de la PC. Ahora
una solicitud `POST /api/v1/interpret` recorre el camino completo servidor →
servicio → proveedor, y la respuesta tiene dos niveles:

- el `TransportEnvelope` externo indica si el mensaje viajó correctamente;
- el `ServiceResult` interno indica si el texto pudo interpretarse.

Un error del servicio, como `provider_not_configured`, viaja dentro de un sobre
exitoso con HTTP 200. Un error de transporte, como un texto vacío, se rechaza
antes de llegar al servicio.

La unión de ambas capas se hace en un único módulo nuevo,
`src/voicestock/pc_server.py`, que pasa a ser el punto de entrada del comando
`voicestock-pc-server`. Se eliminó el stub que vivía dentro de la capa de
comunicación, que ahora no importa nada del paquete de interpretación.

Se agregaron 7 tests del camino integrado, incluyendo chequeos de imports que
verifican que la comunicación no conoce la interpretación y que no existe un
segundo servidor HTTP. La suite alcanzó **53 tests aprobados** y **96 % de
cobertura**. Además se levantó el servidor real y se verificó con `curl` un
éxito, un rechazo de transporte (`422`) y un error de servicio dentro de un
sobre exitoso (`200`).

Tras actualizar el repositorio hay que reinstalar el paquete
(`pip install -e ".[dev]"`), porque cambió el módulo del comando
`voicestock-pc-server`.
