# VoiceStock — Guía de documentación

## 1. Objetivo

Este documento define **qué debe documentarse, dónde debe documentarse y con qué nivel de detalle** dentro del proyecto VoiceStock.

La intención es mantener una documentación útil para desarrollo, mantenimiento, integración y transferencia de conocimiento, evitando tanto la falta de información como la documentación excesiva que rápidamente queda desactualizada.

La regla general del proyecto será:

> **Documentar decisiones, interfaces, arquitectura, operación y conocimiento que no resulte evidente leyendo el código.**

La documentación técnica debe tratarse como parte del producto y mantenerse junto con los cambios que la afectan.

---

## 2. Principios generales

### 2.1. Markdown como formato por defecto

La documentación técnica del repositorio debe escribirse en **Markdown (`.md`)** salvo que exista una razón concreta para utilizar otro formato.

Markdown será el formato preferido porque:

- se versiona correctamente con Git;
- permite revisar cambios mediante Pull Requests;
- se renderiza directamente en GitHub;
- es liviano y fácil de mantener;
- permite mantener la documentación cerca del código.

### 2.2. LaTeX solo para documentación formal

LaTeX debe reservarse para documentos cuyo objetivo principal sea la **presentación formal**, por ejemplo:

- informes solicitados por la cátedra;
- informe final;
- documentos académicos extensos;
- documentación que requiera ecuaciones, referencias bibliográficas, numeración formal de figuras/tablas o maquetación estricta.

No utilizar LaTeX para documentación técnica cotidiana del proyecto.

Una especificación de API, una explicación de arquitectura o una guía de instalación pertenecen normalmente a Markdown, aunque puedan formar parte posteriormente de un informe académico.

### 2.3. Evitar duplicación

Una misma información debe tener **una única fuente de verdad**.

Por ejemplo:

- el procedimiento de instalación debe existir en una guía técnica y no copiarse en múltiples informes;
- el contrato JSON debe documentarse una sola vez y referenciarse desde otros documentos;
- una decisión de arquitectura no debe describirse de forma diferente en varios archivos.

Los informes pueden resumir información técnica existente y referenciarla, pero no deben convertirse en la documentación primaria del sistema.

### 2.4. Documentar el porqué, no repetir el código

La documentación no debe describir línea por línea qué hace una implementación evidente.

Debe explicar principalmente:

- por qué existe una decisión;
- cuáles son las restricciones;
- cómo interactúan los componentes;
- qué contrato debe respetarse;
- cómo operar o probar el sistema;
- qué supuestos fueron adoptados.

---

## 3. Ubicación de la documentación

Se recomienda la siguiente estructura mínima:

```text
.
├── README.md
├── CONTRIBUTING.md
├── docs/
│   ├── architecture/
│   ├── bitacora/
│   ├── decisions/
│   ├── guides/
│   ├── images/
│   ├── interfaces/
│   ├── setup/
│   └── testing/
└── reports/
    └── ...
```

La estructura puede crecer si el proyecto lo requiere, pero no deben crearse carpetas vacías o categorías innecesarias.

---

## 4. Qué corresponde al `README.md`

El `README.md` de la raíz debe ser el **punto de entrada al proyecto**.

Debe permitir que una persona externa entienda rápidamente:

- qué problema resuelve VoiceStock;
- cuál es el alcance actual;
- arquitectura general del sistema;
- componentes principales;
- tecnologías utilizadas;
- cómo ejecutar el proyecto en forma básica;
- estado actual del desarrollo;
- enlaces hacia documentación más detallada.

El README **no debe convertirse en una especificación completa**.

Si una sección empieza a crecer demasiado, debe moverse a `docs/` y dejarse un enlace.

---

## 5. Qué corresponde a `docs/`

La carpeta `docs/` contiene documentación técnica que debe permanecer válida durante la vida del proyecto.

### 5.1. Arquitectura — `docs/architecture/`

Utilizar esta carpeta para explicar cómo está construido el sistema y cómo se relacionan sus componentes.

Ejemplos para VoiceStock:

- arquitectura general del sistema;
- responsabilidades de Raspberry Pi, PC y aplicación web;
- flujo de una operación de inventario;
- máquina de estados;
- arquitectura de red;
- persistencia y flujo hacia SQLite.

Ejemplo:

```text
docs/architecture/system-overview.md
docs/architecture/state-machine.md
docs/architecture/network.md
```

Los diagramas deben acompañar una explicación textual breve. Un diagrama sin contexto no reemplaza la documentación.

---

### 5.2. Interfaces y contratos — `docs/interfaces/`

Debe documentarse cualquier interfaz que conecte componentes desarrollados de manera relativamente independiente.

En VoiceStock esto incluye especialmente:

- comunicación Raspberry Pi ↔ PC;
- contrato JSON de interpretación;
- endpoints HTTP relevantes;
- formatos de error;
- versionado de mensajes;
- supuestos de compatibilidad.

Ejemplo:

```text
docs/interfaces/interpretation-api.md
docs/interfaces/operation-schema.md
```

Cada interfaz debería indicar como mínimo:

1. propósito;
2. entrada;
3. salida;
4. ejemplos válidos;
5. errores esperados;
6. restricciones;
7. versión, cuando corresponda.

Cuando sea posible, complementar la documentación manual con formatos ejecutables o verificables como JSON Schema, OpenAPI u otros equivalentes.

---

### 5.3. Decisiones de arquitectura — `docs/decisions/`

Las decisiones técnicas importantes deben registrarse como **Architecture Decision Records (ADR)**.

Un ADR debe utilizarse cuando una decisión:

- afecta significativamente la arquitectura;
- tiene alternativas razonables;
- puede ser difícil de entender meses después;
- condiciona futuras implementaciones.

Ejemplos:

```text
docs/decisions/0001-use-sqlite.md
docs/decisions/0002-raspberry-as-access-point.md
docs/decisions/0003-stt-engine-selection.md
```

Formato recomendado:

```markdown
# ADR-000X: Título

## Status
Accepted / Superseded / Deprecated

## Context
¿Qué problema o restricción motivó la decisión?

## Decision
¿Qué se decidió?

## Alternatives considered
¿Qué alternativas se evaluaron?

## Consequences
¿Qué ventajas, limitaciones o compromisos introduce?
```

Los ADR no deben utilizarse para decisiones triviales de implementación.

---

### 5.4. Configuración y operación — `docs/setup/`

Esta carpeta debe permitir que otro integrante pueda preparar y ejecutar el sistema sin depender de conocimiento oral.

Ejemplos:

```text
docs/setup/raspberry-pi.md
docs/setup/pc-service.md
docs/setup/development-environment.md
```

Documentar:

- dependencias;
- versiones relevantes;
- variables de entorno;
- configuración de red;
- pasos de instalación;
- comandos de ejecución;
- configuración específica de hardware;
- problemas conocidos relevantes.

No incluir secretos, tokens, contraseñas ni claves reales.

---

### 5.5. Pruebas — `docs/testing/`

No es necesario documentar manualmente cada test unitario.

Esta carpeta se reserva para estrategias, procedimientos o pruebas que requieran contexto adicional.

Ejemplos:

- procedimiento de prueba end-to-end;
- prueba de comunicación Raspberry Pi ↔ PC;
- medición de latencia;
- procedimiento para validar pérdida de conexión;
- pruebas presenciales de hardware;
- criterios para una demo de entrega.

Ejemplo:

```text
docs/testing/end-to-end.md
docs/testing/latency-test.md
```

Cada prueba manual importante debería indicar:

1. objetivo;
2. precondiciones;
3. procedimiento;
4. resultado esperado;
5. evidencia o métrica a registrar.

---

### 5.6. Guías de proceso — `docs/guides/`

Esta carpeta reúne guías de trabajo del equipo que no describen el sistema en sí, sino cómo documentar y desarrollar.

Ejemplos:

```text
docs/guides/documentation-guide.md
docs/guides/development-workflow.md
```

---

### 5.7. Bitácora — `docs/bitacora/`

La bitácora registra el proceso de diseño, implementación, pruebas e iteraciones: decisiones técnicas, dudas planteadas a la cátedra y problemas encontrados con sus soluciones.

No reemplaza la documentación técnica de `docs/architecture/`, `docs/decisions/` u otras carpetas estables. Es un registro cronológico del proyecto.

```text
docs/bitacora/bitacora.md
```

---

## 6. Qué NO corresponde a `docs/`

No debe utilizarse `docs/` para:

- notas personales;
- borradores temporales;
- listas de tareas;
- planificación diaria;
- fechas administrativas;
- información que ya se gestiona en ClickUp;
- conversaciones o conclusiones informales sin validar;
- documentación generada automáticamente que pueda regenerarse fácilmente.

Las tareas, responsables, fechas y prioridades pertenecen a **ClickUp**.

La documentación técnica estable pertenece al **repositorio**.

---

## 7. Documentación dentro del código

### 7.1. Comentarios

Los comentarios deben utilizarse para explicar:

- decisiones no obvias;
- workarounds;
- restricciones externas;
- comportamiento excepcional;
- razones por las cuales una implementación aparentemente más simple no es válida.

Evitar comentarios que repitan literalmente el código.

Ejemplo incorrecto:

```python
# Increment stock
stock += quantity
```

Ejemplo válido:

```python
# Stock and movement history must be updated in the same transaction
# to prevent partial inventory updates after a failure.
```

### 7.2. Docstrings

Funciones, clases o módulos que formen parte de una interfaz relevante deben incluir docstrings cuando su contrato no sea evidente.

Priorizar la documentación de:

- parámetros;
- valores retornados;
- errores/excepciones;
- efectos laterales;
- restricciones importantes.

No es necesario agregar docstrings extensos a funciones privadas triviales.

---

## 8. Diagramas

Los diagramas deben utilizarse cuando reduzcan significativamente la complejidad de una explicación textual.

Son especialmente útiles para:

- arquitectura del sistema;
- comunicación entre componentes;
- máquinas de estados;
- secuencias de interacción;
- topología de red.

Siempre que sea razonable, preferir formatos versionables como Mermaid, PlantUML u otros equivalentes basados en texto.

Imágenes estáticas (`.png`, `.svg`) pueden utilizarse cuando provengan de herramientas externas o cuando el formato visual lo justifique.

Los archivos fuente de los diagramas deben conservarse siempre que sea posible.

---

## 9. Informes y documentos académicos

Los informes solicitados por la cátedra deben mantenerse separados de la documentación técnica del proyecto.

Por ejemplo:

```text
reports/
├── october/
│   └── report.tex
└── november/
    └── report.tex
```

Los informes pueden utilizar LaTeX y tomar información de la documentación técnica existente.

La regla es:

> **El informe describe el estado del proyecto en un momento determinado; `docs/` describe cómo funciona el proyecto.**

Por lo tanto, un informe puede quedar históricamente congelado mientras la documentación técnica continúa evolucionando.

---

## 10. Documentación de investigaciones y comparaciones

Cuando sea necesario investigar tecnologías antes de tomar una decisión —por ejemplo STT, modelo local vs API externa o librerías— la documentación debe distinguir entre **investigación temporal** y **decisión permanente**.

Una comparación puede documentarse inicialmente como:

```text
docs/research/stt-comparison.md
```

Debe incluir:

- alternativas evaluadas;
- criterios de comparación;
- resultados o mediciones;
- limitaciones de la prueba;
- conclusión técnica.

Si la investigación conduce a una decisión arquitectónica relevante, crear posteriormente un ADR que registre la decisión final.

El documento de investigación conserva la evidencia; el ADR conserva la decisión.

---

## 11. Convenciones de nombres

Los archivos deben utilizar nombres descriptivos en **kebab-case** y preferentemente en inglés.

Ejemplos:

```text
system-overview.md
network-architecture.md
interpretation-api.md
operation-schema.md
raspberry-pi-setup.md
end-to-end-testing.md
```

Evitar nombres como:

```text
documentacion.md
notas.md
varios.md
final-final.md
cosas-importantes.md
```

---

## 12. Actualización de documentación

Una tarea no debería considerarse completamente terminada si modifica una interfaz, una decisión o un procedimiento documentado y la documentación correspondiente quedó desactualizada.

La documentación debe actualizarse dentro del mismo cambio o Pull Request siempre que sea posible.

Ejemplos de cambios que normalmente requieren actualización documental:

- modificación de un endpoint;
- cambio en el contrato JSON;
- cambio de arquitectura;
- nueva variable de entorno;
- modificación del procedimiento de instalación;
- cambio en la máquina de estados;
- sustitución del motor STT;
- cambio en la topología de red.

---

## 13. Criterio práctico: ¿dónde documento esto?

| Información | Lugar recomendado |
|---|---|
| Descripción general del proyecto | `README.md` |
| Cómo ejecutar el proyecto | `README.md` o `docs/setup/` |
| Flujo de trabajo Git y entorno local | `docs/guides/development-workflow.md` |
| Convenciones de documentación | `docs/guides/documentation-guide.md` |
| Bitácora del proyecto | `docs/bitacora/bitacora.md` |
| Arquitectura general | `docs/architecture/` |
| Máquina de estados | `docs/architecture/` |
| Contrato Raspberry Pi ↔ PC | `docs/interfaces/` |
| Esquema JSON | `docs/interfaces/` + schema verificable si aplica |
| Endpoint HTTP | `docs/interfaces/` o especificación OpenAPI |
| Decisión SQLite vs alternativa | ADR |
| Selección de STT | investigación + ADR si la decisión es relevante |
| Configuración de Raspberry Pi | `docs/setup/` |
| Procedimiento de prueba presencial | `docs/testing/` |
| Test unitario individual | código del test, no `docs/` |
| Comentario sobre implementación no obvia | código |
| Fechas, responsables y tareas | ClickUp |
| Informe de octubre/noviembre | LaTeX en `reports/` |
| Presentación académica | herramienta correspondiente, fuera de `docs/` |

---

## 14. Regla de cierre

Antes de crear documentación nueva, responder estas tres preguntas:

1. **¿Esta información seguirá siendo útil dentro de varios meses?**
2. **¿Una persona que no participó de la conversación necesitaría conocerla para desarrollar, operar o mantener el sistema?**
3. **¿Existe ya otro lugar que sea la fuente de verdad de esta información?**

Si las respuestas son **sí, sí, no**, probablemente debe documentarse.

Si la información es temporal, administrativa o ya está representada correctamente en ClickUp, Git o el código, probablemente no necesita un nuevo documento.
