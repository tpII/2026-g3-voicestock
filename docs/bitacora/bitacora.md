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

---

## 17/09/2026

### Avance

Se realizó la guía de documentación del proyecto (disponible en [Guía de documentación](../guides/documentation-guide.md)). Además, se organizaron los archivos de documentación ya existentes en el lugar correspondiente del repositorio: el flujo de trabajo quedó en `docs/guides/development-workflow.md` y la bitácora en `docs/bitacora/bitacora.md`. Se comenzó a definir las tareas necesarias para las diferentes áreas del proyecto; se utilizará la plataforma ClickUp como centro de gestión y se adoptó la convención 1 tarea = 1 commit.

---

## 19/09/2026

### Avance

Se descompuso el sistema en features y se organizó el trabajo en ClickUp, separando tareas de **Raspberry Pi, PC, Web & DataBase, documentación y pruebas**.

Se definieron como principales bloques: `PushToTalk`, `SpeechToText`, `RaspberryPiPCCommunication`, `InterpretationService`, `StructuredCommandInterpretation`, `OperationContractValidation`, `PendingOperationFlow` y `PendingOperationWeb`.

---

## 23/09/2026

### Avance

Se comenzaron la mayoría de las tareas iniciales de investigación definidas en ClickUp.

Entre ellas:

- alternativas de STT para Raspberry Pi 3;
- comunicación Raspberry Pi–PC;
- modelo local vs API externa para interpretación;
- captura Push-to-Talk;
- stack para servidor HTTP e interfaz web;
- definición del contrato entre componentes.

Se decidió mantener los módulos desacoplados mediante interfaces para poder reemplazar tecnologías sin modificar todo el sistema.

---

## 24/09/2026

### Avance

Se terminó de definir de forma preliminar el flujo principal:

**pulsador → audio → STT → PC → interpretación → validación → operación pendiente → confirmación web**

Se estableció que una interpretación válida **no modifica directamente el inventario**, sino que primero genera una operación pendiente que debe ser confirmada.

También se comenzó a trabajar sobre un **contrato JSON versionado** con validación estructural y semántica.

---

## 25/09/2026

### Avance

Se continuó refinando el backlog y las tareas de implementación en ClickUp.

Se avanzó en la definición de:

- comunicación cliente/servidor entre Raspberry Pi y PC;
- `InterpretationService` desacoplado del proveedor;
- validación de productos y operaciones;
- estado `WAIT_CONFIRMATION`;
- interfaz web para consultar, confirmar o cancelar operaciones pendientes.

Como parte de la investigación del modelo local, se realizaron pruebas con **Qwen 3.5 4B** clasificando productos en categorías de supermercado.

Los resultados fueron correctos en los casos probados, con un tiempo aproximado de **15 segundos por consulta**, por lo que se considera una alternativa viable para seguir evaluando frente al uso de APIs externas.

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

### Cliente de comunicación en la Raspberry Pi

Se implementó el cliente que usa la Raspberry Pi para enviar el texto
reconocido a la PC (`RaspberryPiPCCommunication-03`). Con él queda completo en
código el viaje Raspberry → PC → Raspberry; falta probarlo en el hardware real.

Decisiones:

- El resto del sistema depende del protocolo `InterpretationClient`, con un
  único método `interpret(text) -> TransportEnvelope`. No conoce HTTP, de modo
  que el transporte se puede cambiar sin tocar a quien lo usa.
- El cliente nunca lanza excepciones por problemas de comunicación: todo
  resultado es un `TransportEnvelope`. Así aparece un tercer nivel de error,
  detectado en la propia Raspberry cuando no llega una respuesta usable:
  `timeout`, `connection_failed`, `unexpected_status`,
  `invalid_response_encoding`, `invalid_envelope` y
  `request_encoding_failure`. Estos códigos no se superponen con los del
  servidor, y los errores que informa el servidor llegan sin cambios.
- El cliente no valida el texto ni inspecciona el payload, y no hace
  reintentos: esas decisiones corresponden a capas superiores.
- Destino y timeout se configuran con `VOICESTOCK_PC_URL` (por defecto
  `http://127.0.0.1:8000`) y `VOICESTOCK_PC_TIMEOUT` (por defecto 10 segundos).
  La IP definitiva de la PC depende de `LocalNetworkInfra`, que todavía no fijó
  el plan de direcciones.
- `httpx` pasó de dependencia de desarrollo a dependencia de ejecución, porque
  ahora la usa el cliente.

### Pruebas del cliente

Se agregaron tests con un transporte simulado (`httpx.MockTransport`) para cada
respuesta rota posible, y tests con sockets reales en localhost: un viaje
completo contra el servidor real, un puerto cerrado y un socket que acepta la
conexión pero nunca responde, que debe terminar en `timeout`. La suite alcanzó
**94 tests aprobados** y **97 % de cobertura**; el cliente tiene 100 %.

Tras actualizar el repositorio hay que reinstalar el paquete
(`pip install -e ".[dev]"`), porque `httpx` pasó a ser dependencia de
ejecución.

### Documentación de la comunicación Raspberry Pi–PC

Se completó la documentación de la interfaz de comunicación
(`RaspberryPiPCCommunication-04`) para que cualquier integrante pueda levantar
servidor y cliente y reproducir el viaje completo solo con el repositorio:

- Se agregó el comando `voicestock-pi-client "texto"`, que envía un texto a la
  PC e imprime el `TransportEnvelope` resultante. Es el equivalente del lado de
  la Raspberry a `voicestock-pc-server` y sirve para pruebas manuales.
- Se documentó cómo operar en la red local: el servidor escuchando en
  `0.0.0.0`, cómo obtener la IP de la PC y cómo apuntar el cliente desde la
  Raspberry. La IP definitiva queda a cargo de `LocalNetworkInfra`.
- Se armó un catálogo único de errores de comunicación (del servidor y del
  cliente), con un comando para reproducir cada uno y la salida obtenida al
  ejecutarlo. Los que el proveedor stub no puede provocar se enlazan a su test.
- Se dejó explícito que la capa de comunicación no inspecciona operación,
  producto, cantidad ni unidad.

Queda pendiente la prueba física entre la PC y la Raspberry, que depende de la
red de `LocalNetworkInfra`.

### Reorganización del código en `pc`, `pi` y `shared`

Siguiendo lo acordado en el equipo, se reorganizó `src/` según la máquina donde
corre cada parte, en lugar del paquete único `voicestock` dividido por
funcionalidad:

- `src/pc`: servidor HTTP, `InterpretationService` y proveedores, y el comando
  `voicestock-pc-server`.
- `src/pi`: cliente de comunicación y el comando `voicestock-pi-client`. Más
  adelante se sumarán Push-to-Talk, SpeechToText, operaciones pendientes, base
  de datos y web.
- `src/shared`: el contrato que intercambian ambas máquinas
  (`TransportEnvelope`, `InterpretationRequest`), con una sola definición para
  que la PC y la Raspberry no se desincronicen.

Se eligió `src/pc` y `src/pi` como paquetes de primer nivel, tal como se había
planteado, en lugar de `src/voicestock/pc`. La decisión, sus alternativas y sus
consecuencias quedaron en el ADR-0002. Un nuevo test de arquitectura verifica
que `pc` y `pi` no se importen entre sí y que `shared` no importe a ninguno. Los
tests se reorganizaron con la misma división.

No cambió el comportamiento: los comandos conservan su nombre y la suite pasó
de 97 a **101 tests aprobados** (por los nuevos chequeos de imports), con
**97 % de cobertura**. Tras actualizar el repositorio hay que reinstalar el
paquete (`pip install -e ".[dev]"`).
