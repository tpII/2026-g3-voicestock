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

- **Python 3.11+** con entorno virtual y scripts de setup para Linux/Raspberry Pi y Windows.
- **Ruff**, **Pytest**, **pytest-cov** y **pre-commit** para calidad y pruebas.
- **CI en GitHub Actions** sobre `main` y `develop`.
- Se documentó el flujo de branching, commits y merges.
- Se dejó `docs/architecture.md` como documento vivo.
- Se agregó `.env.example` para la futura integración con el LLM.

### Decisiones técnicas

- **Docker queda fuera del arranque inicial**, principalmente para no complicar el acceso al hardware de la Raspberry Pi.
- **SQLite** como motor de persistencia.

### Preguntas

- Se consultó sobre alimentación fija o portable. Por ahora se apunta a alimentación fija, dejando portabilidad como objetivo secundario.
- Se planteó el trade-off entre **LLM local y API externa**, a discutir con la cátedra por ser una decisión central de arquitectura.
- El parlante se deja como objetivo secundario; la confirmación podrá realizarse inicialmente mediante la web.

---

# 19/09/2026

### Avance

Se descompuso el sistema en features y se organizó el trabajo en ClickUp, separando tareas de **Raspberry Pi, PC, Web & DataBase, documentación y pruebas**.

Se definieron como principales bloques: `PushToTalk`, `SpeechToText`, `RaspberryPiPCCommunication`, `InterpretationService`, `StructuredCommandInterpretation`, `OperationContractValidation`, `PendingOperationFlow` y `PendingOperationWeb`.

---

# 23/09/2026

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

# 24/09/2026

### Avance

Se terminó de definir de forma preliminar el flujo principal:

**pulsador → audio → STT → PC → interpretación → validación → operación pendiente → confirmación web**

Se estableció que una interpretación válida **no modifica directamente el inventario**, sino que primero genera una operación pendiente que debe ser confirmada.

También se comenzó a trabajar sobre un **contrato JSON versionado** con validación estructural y semántica.

---

# 25/09/2026

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