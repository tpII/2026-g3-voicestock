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

### Investigación de Push-to-Talk

Se avanzó en la investigación del stack necesario para implementar la primera parte del flujo en la Raspberry Pi: detección del pulsador y captura de audio desde un micrófono USB.

Para GPIO se compararon alternativas de acceso desde Python y se eligió **GPIO Zero**, utilizando un modelo orientado a eventos en lugar de polling. El pulsador se conectará entre un GPIO configurable y GND utilizando el pull-up interno de la Raspberry Pi.

El estado eléctrico será:

- pulsador liberado → GPIO HIGH;
- pulsador presionado → GPIO LOW.

GPIO Zero abstraerá estos niveles mediante eventos semánticos de pulsación y liberación.

Se estableció además que los callbacks GPIO deben ser mínimos y no bloqueantes: únicamente notificarán cambios de estado. La captura de audio se ejecutará fuera de estos callbacks.

### Investigación de audio

Para la adquisición desde el micrófono USB se evaluaron alternativas como `arecord`, PyAudio y `python-sounddevice`.

Se eligió **python-sounddevice** sobre PortAudio y ALSA, utilizando `RawInputStream` para disponer de control explícito sobre el inicio y finalización de la captura. `arecord` se conservará como herramienta de diagnóstico, pero no como backend de la aplicación.

Se definió como contrato de audio para las siguientes etapas:

- contenedor WAV;
- PCM lineal sin compresión;
- 16 kHz;
- mono;
- signed 16-bit.

No se asumirá que cualquier micrófono USB soporte directamente esta configuración. La implementación deberá comprobar las capacidades del dispositivo seleccionado y fallar explícitamente si no puede cumplir el contrato. El resampling queda fuera del alcance inicial.

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

### Implementación inicial de Push-to-Talk

Se implementó la detección de pulsación y liberación mediante `PushToTalkButton`.

El componente encapsula GPIO Zero y se limita a adaptar el hardware físico a dos eventos de aplicación: press y release. No contiene lógica de captura de audio, Speech-to-Text ni conocimiento del pipeline general.

El pin BCM y el tiempo de debounce son configurables. La polaridad queda fijada mediante el pull-up interno (`pull_up=True`) y el pulsador conectado a GND.

Se agregaron tests utilizando los mock pins de GPIO Zero para verificar:

- pulsación;
- liberación;
- orden de los eventos;
- ciclos repetidos;
- debounce;
- aceptación de una transición válida posterior al debounce;
- liberación de recursos mediante `close()`.

De esta forma, la lógica GPIO puede validarse automáticamente sin disponer de una Raspberry Pi física durante CI.

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

### Implementación de captura de audio USB

Se implementó la captura de audio desde micrófono USB, manteniéndola desacoplada tanto del GPIO como del futuro motor de Speech-to-Text.

`AudioCapture` expone un ciclo explícito `start()` / `stop()` y depende de una interfaz `AudioInputBackend`. La implementación de producción utiliza `SoundDeviceBackend`, mientras que los tests pueden sustituirla por un backend simulado.

La captura se realiza progresivamente, evitando mantener toda la grabación en memoria. Esto reduce el uso de RAM y resulta apropiado para la Raspberry Pi 3 utilizada por el proyecto.

### Lifecycle del artifact

Cada captura utiliza un identificador UUID y comienza escribiendo sobre un archivo temporal:

`<uuid>.recording`

Al detenerse la captura se finaliza el WAV, se validan sus parámetros y sólo entonces se publica mediante una operación atómica como:

`<uuid>.wav`

Por lo tanto, un archivo con extensión `.wav` representa un artifact correctamente finalizado.

`AudioArtifact` mantiene un identificador independiente del path y expone `cleanup()` para que el propietario pueda eliminar el archivo cuando deje de necesitarlo.

### Selección del micrófono

El dispositivo de entrada se selecciona mediante una descripción configurable y no mediante un índice PortAudio persistente, ya que esos índices pueden cambiar al reiniciar o reconectar dispositivos.

Se definieron errores específicos para distinguir:

- dispositivo no encontrado;
- selector ambiguo;
- configuración de audio no soportada;
- fallos del stream;
- operaciones inválidas según el estado de la captura.

Antes de abrir el stream se valida que el dispositivo seleccionado pueda utilizar el contrato actual de 16 kHz, mono y signed 16-bit. No se agregó resampling automático.

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

### Integración completa de Push-to-Talk

Sobre la nueva estructura `pc`, `pi` y `shared`, se integraron los componentes
de Push-to-Talk dentro del runtime de la Raspberry Pi:

- `src/pi/input` contiene la adaptación del pulsador físico;
- `src/pi/audio` contiene configuración, backend, captura y artifacts de audio;
- `src/pi/push_to_talk` contiene la orquestación del gesto Push-to-Talk y el
  resultado entregado al siguiente componente.

Estos módulos permanecen dentro de `pi` y no en `shared`, ya que son
responsabilidades específicas de la Raspberry Pi.

`PushToTalkController` conecta los eventos del pulsador con `AudioCapture`.
Los callbacks GPIO no realizan operaciones de audio directamente: `PRESSED`,
`RELEASED` y los eventos de timeout ingresan a una cola y son procesados
secuencialmente por un único worker.

El flujo implementado queda:

**pulsación → `PRESSED` → inicio de captura → liberación → `RELEASED` → finalización del WAV → `AudioCaptureResult`**

`AudioCaptureResult` contiene el artifact generado, la duración real obtenida
desde el WAV, el formato de audio y el motivo de finalización.

### Duración máxima y máquina de estados

Se incorporó una duración máxima configurable, con un valor por defecto de
**60 segundos**, para evitar grabaciones indefinidas ante un pulsador trabado o
una liberación no detectada.

El controlador utiliza los estados:

- `IDLE`;
- `RECORDING`;
- `WAITING_FOR_RELEASE`.

Si vence el timeout mientras el botón continúa presionado, se finaliza la
captura y se entrega un artifact válido con
`TerminationReason.MAX_DURATION`. El controlador pasa entonces a
`WAITING_FOR_RELEASE` y no permite comenzar otra captura hasta detectar la
liberación física del pulsador.

El timer no ejecuta `stop()` directamente: únicamente coloca el evento en la
misma cola utilizada por el resto del controlador. Cada ciclo utiliza además
una identificación interna para impedir que un timeout atrasado perteneciente
a una grabación anterior detenga una captura posterior.

### Ownership del audio

Durante una grabación, `AudioCapture` es responsable del archivo temporal.

Después de finalizar correctamente el WAV y construir `AudioArtifact`, el
artifact se incorpora a `AudioCaptureResult` y se entrega mediante el callback
de finalización.

A partir de ese momento el ownership pertenece al consumidor. El controlador
Push-to-Talk no elimina automáticamente artifacts entregados exitosamente.

Esta separación permite que el futuro orquestador de Speech-to-Text decida
cuándo procesar, conservar o eliminar el archivo sin acoplar esa política a la
captura.

### Pruebas de Push-to-Talk

Se agregaron tests automatizados para los principales escenarios del
controlador:

- ciclo normal press–talk–release;
- timeout por duración máxima;
- eventos redundantes;
- errores al iniciar la captura;
- errores al detenerla;
- carreras entre release y timeout;
- timeouts atrasados pertenecientes a ciclos anteriores;
- cierre durante una grabación activa;
- excepciones producidas por el consumidor;
- lifecycle y ownership del artifact.

Los componentes GPIO y audio pueden sustituirse por implementaciones simuladas,
por lo que la suite no requiere una Raspberry Pi, un pulsador ni un micrófono
USB.

### Documentación de Push-to-Talk

Se completó la documentación estable de la feature.

La decisión arquitectónica quedó registrada en el **ADR-0003**, documentando:

- GPIO Zero con detección orientada a eventos;
- callbacks GPIO mínimos;
- cola y worker único para la orquestación;
- `python-sounddevice` sobre PortAudio y ALSA;
- `RawInputStream` para captura;
- WAV PCM de 16 kHz, mono y 16 bits como contrato actual.

La interfaz de Push-to-Talk documenta las responsabilidades de
`PushToTalkButton`, `AudioCapture` y `PushToTalkController`, además de
`AudioArtifact`, `AudioCaptureResult`, `AudioFormat`, `TerminationReason`, la
máquina de estados y las reglas de ownership.

También se agregó una guía de setup y prueba manual para conectar el pulsador,
seleccionar el micrófono USB y ejecutar el nuevo comando:

`voicestock-pi-ptt`

El comando permite configurar pin BCM, debounce, dispositivo de entrada,
directorio de salida y duración máxima.

La guía incluye procedimientos para comprobar el WAV generado y reproducir el
caso `MAX_DURATION`, además de diagnóstico para dispositivos inexistentes,
selectores ambiguos, formatos no soportados y problemas de wiring o debounce.

### Problemas encontrados en CI

Al ejecutar la suite de Push-to-Talk en GitHub Actions, Pytest falló durante
collection por imports internos de tests que utilizaban rutas del tipo
`tests.pi...`.

Estos imports funcionaban en el entorno local utilizado durante el desarrollo,
pero dependían de que `tests` fuese importable como paquete raíz, condición que
no estaba garantizada en un checkout limpio de CI.

Se corrigió la organización/importación de los helpers de tests para eliminar
esa dependencia del entorno local, sin modificar el workflow ni agregar
`tests` artificialmente a `PYTHONPATH`.

### Estado de Push-to-Talk

Con la investigación, implementación, integración, tests y documentación
completados, Push-to-Talk queda preparado a nivel de software para conectarse
posteriormente con Speech-to-Text.

Queda pendiente la validación física sobre la Raspberry Pi 3 del proyecto con
el pulsador y el micrófono USB reales. Se deberá comprobar:

- detección física de pulsación y liberación;
- debounce con el pulsador real;
- disponibilidad de PortAudio/ALSA en la imagen utilizada;
- detección del micrófono USB;
- soporte real de captura a 16 kHz, mono y 16 bits;
- calidad del WAV resultante;
- ciclo press–talk–release;
- finalización por duración máxima.

---

## 04/10/2026

### Red local: investigación (`LocalNetworkInfra-01`)

Se reconsideró el enfoque original de usar la Raspberry Pi como punto de
acceso Wi-Fi. La arquitectura elegida es un enlace Ethernet directo entre la
PC y la Raspberry Pi 3. El Wi-Fi de la PC queda libre para Internet.

El plan quedó así:

- subred dedicada `192.168.50.0/24`;
- Raspberry Pi en `192.168.50.1/24`;
- PC en `192.168.50.2/24`;
- direcciones estáticas;
- sin puerta de enlace ni DNS en la Ethernet de VoiceStock;
- sin DHCP, sin NAT y sin reenvío IP;
- la Raspberry Pi no actúa como punto de acceso Wi-Fi.

La decisión y sus motivos están en
[estrategia de red local](../research/local-network-strategy.md).

### Configuración Ethernet estática (`LocalNetworkInfra-02`)

Se agregaron scripts reproducibles para aplicar esas direcciones en cada
máquina. Se pueden ejecutar más de una vez. Cada script guarda la
configuración con el mecanismo persistente de su sistema; el reinicio en el
hardware real todavía no se probó.

En la Raspberry Pi, `scripts/setup_pi_ethernet.sh` usa NetworkManager
(`nmcli`). Crea o actualiza el perfil persistente `voicestock-ethernet` con
`192.168.50.1/24`, sin puerta de enlace, sin DNS y con `ipv4.never-default`.
Solo modifica la interfaz Ethernet elegida: si hay una sola, la usa; si hay
más de una, hay que indicarla.

En la PC, `scripts/setup_pc_ethernet.ps1` exige el `InterfaceAlias` exacto y
no elige un adaptador por su cuenta. En ese adaptador deja `192.168.50.2/24`,
desactiva el DHCP IPv4, no configura puerta de enlace y no modifica el Wi-Fi.

Al revisar el script de Windows se corrigió el DNS. `ResetServerAddresses`
volvía a los servidores que entrega DHCP. Ahora el adaptador dedicado guarda
una lista DNS IPv4 estática y vacía, de modo que no queda ningún servidor DNS
en esa interfaz.

### Documentación operativa (`LocalNetworkInfra-03`)

Se completó la guía de operación en
[setup de la red Ethernet](../setup/local-network.md). Cubre la topología
esperada, la preparación del hardware, la configuración de la Raspberry Pi y
de Windows, la verificación local de direcciones y rutas, el orden de
arranque, el diagnóstico de fallos habituales y una lista de comprobación
antes de una demo.

También se actualizó
[la interfaz de comunicación Raspberry Pi–PC](../interfaces/pc-communication.md)
para usar la dirección fija de la PC, `192.168.50.2`, y dejar de indicar el
punto de acceso Wi-Fi que se había considerado antes.

### Estado de LocalNetworkInfra

- `LocalNetworkInfra-01` completada.
- `LocalNetworkInfra-02` completada.
- `LocalNetworkInfra-03` completada.
- `LocalNetworkInfra-04` pendiente: falta la validación física con la PC, la
  Raspberry Pi y el cable Ethernet reales. Todavía no se comprobó en hardware
  la conectividad de punta a punta, el aislamiento de Internet ni que la
  configuración sobreviva a un reinicio.

---

## 06/10/2026

### Interfaz web de la operación pendiente (`PendingOperationWeb-01`)

Se eligió el stack y la topología del servidor que va a mostrar la operación
pendiente en el navegador de la PC. La PC llega a la Raspberry Pi por el
enlace Ethernet ya definido (`192.168.50.1` y `192.168.50.2`). No se vuelve a
usar un punto de acceso Wi-Fi.

La decisión quedó así:

- FastAPI como framework HTTP y Uvicorn como servidor ASGI;
- HTML, CSS y JavaScript vanilla, servidos como archivos estáticos por la
  misma aplicación;
- un solo proceso Python en la Raspberry Pi, dueño del orquestador, de la
  máquina de estados y de `PendingOperation`;
- HTTP solo como adaptador: consulta y resolución pasan por puertos de
  aplicación, sin modificar la FSM desde las rutas.

FastAPI se eligió por el contrato HTTP explícito (modelos, validación y un
API que las tareas siguientes pueden implementar), no por rendimiento. El
proceso único se eligió para no introducir IPC ni un segundo dueño del
estado.

Quedaron fuera de este incremento React, Vue, Angular, un frontend
separado, Node.js, un segundo proceso HTTP, Redis, SQLite como canal entre
HTTP y el orquestador, WebSockets, nginx y Docker para publicar esta
interfaz.

La comparación está en
[pending operation web stack](../research/pending-operation-web-stack.md)
y la decisión en
[ADR-0004](../decisions/0004-use-in-process-fastapi-and-static-web-ui.md).
Esta tarea no implementa el servidor, el API ni la página.

---

## 07/10/2026

### Puertos de la operación pendiente (`PendingOperationWeb-02`)

Se definió la frontera que va a usar la web para consultar y resolver la
operación pendiente, sin implementar `PendingOperationFlow`. Esa feature sigue
siendo la dueña futura de la operación y de la máquina de estados. Acá no se
creó un segundo modelo de dominio ni una FSM paralela.

El código quedó en `pi.pending_operation`:

- `PendingOperationQueryPort.get_current()` devuelve un
  `PendingOperationView` o nada;
- `PendingOperationResolutionPort` expone `confirm(operation_id)` y
  `cancel(operation_id)`, con `ResolutionResult` en lugar de un booleano;
- `PendingOperationGateway` aplica esa política con un único lock;
- `ProvisionalOperationExecutor` responde éxito y no toca inventario;
- el estado real entra por `PendingOperationSlot`, que Flow tiene que
  implementar.

Confirmar solo cierra la pendiente después de una ejecución exitosa. Cancelar
no ejecuta inventario. Un reintento de la misma acción devuelve
`already_resolved` y no vuelve a ejecutar; la acción contraria devuelve
`conflict`. Esa memoria es solo la resolución anterior en el proceso y se
pierde al reiniciar.

El registro para integrar Flow está en
[pending operation web flow contract](../research/pending-operation-web-flow-contract.md).
No se agregó un ADR nuevo: la topología y el rol de HTTP ya están en ADR-0004,
y este contrato es el hand-off hasta que Flow exista.

---

## 08/10/2026

### Servidor web inicial (`PendingOperationWeb-03`)

Se agregó la capa `pi.web`: FastAPI en `create_app`, Uvicorn en `run_server`,
y la página estática de marcador de posición. `GET /health` solo indica que
el servidor HTTP responde. `GET /` sirve el HTML local, y `/static/*` los
archivos CSS y JavaScript. No hay API de operación pendiente, CORS, HTTPS ni
login.

El comando `voicestock-pi-web` arranca ese servidor para desarrollo y
validación. En la Raspberry Pi el default es `192.168.50.1:8000`. En otra
máquina se puede usar `VOICESTOCK_WEB_HOST=127.0.0.1`. No es un segundo
proceso productivo: ADR-0004 sigue pidiendo un único proceso cuando exista el
orquestador. Cómo se componen ambos queda pendiente.

La guía está en [servidor web de la Raspberry Pi](../setup/pi-web.md).
Los frameworks HTTP siguen permitidos solo en el servidor de la PC y en
`pi/web`.

### API de la operación pendiente (`PendingOperationWeb-04`)

Se agregó el API versionado en `pi.web`: `GET /api/v1/pending-operation`,
`POST .../confirm` y `POST .../cancel`. Las rutas llaman a los puertos de
aplicación y traducen `ResolutionResult` a HTTP. No hay body en confirm ni
cancel. Un GET sin pendiente responde `204`. Un reintento de la misma acción
responde `200` con `already_resolved`. Conflicto y id viejo responden `409`.
Un fallo de ejecución responde `503` sin texto de excepción.

Si `voicestock-pi-web` arranca sin puertos, `/health` sigue en `200` y el
API responde `503` con `application_not_ready`. Un `operation_id` en blanco
responde `422`.

El contrato está en
[API de la operación pendiente](../interfaces/pending-operation-web-api.md).
No se creó un ADR: el mapeo es el contrato HTTP, y la decisión de que HTTP
es un adaptador ya está en ADR-0004.

### Interfaz de la operación pendiente (`PendingOperationWeb-05`)

La página dejó de ser un marcador de posición. Muestra la frase de
confirmación, los datos estructurados y el texto reconocido. Si no hay
operación, pide usar el botón físico. Confirmar y cancelar llaman al API
con el `operation_id` visible.

La consulta se repite cerca de una vez por segundo, esperando a que termine
la anterior. Un reintento exitoso se muestra como confirmación o
cancelación, no como error. Si la operación cambió, la página se actualiza.
Si la ejecución falla, la tarjeta sigue y se pueden reintentar los botones.
Si la aplicación no está lista o se corta la red, el encabezado dice que no
está disponible y sigue reintentando.

El comportamiento está en
[página de la operación pendiente](../interfaces/pending-operation-web-ui.md).
