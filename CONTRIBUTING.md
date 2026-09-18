# Guía de Contribución

Este documento define las convenciones de desarrollo, organización del código y flujo de trabajo Git utilizadas en el proyecto VoiceStock.

El objetivo es mantener un repositorio consistente, entendible y fácil de mantener, incluso cuando varias personas trabajan simultáneamente sobre diferentes partes del sistema.

Estas reglas deben ser respetadas por todos los integrantes del equipo.

La guía práctica paso a paso (clonar, entorno, ramas, commits, Pull Requests y CI) está en [docs/guides/development-workflow.md](docs/guides/development-workflow.md).

---

# 1. Principios generales

El proyecto seguirá las siguientes reglas generales:

- El código, los nombres de archivos, variables, funciones, clases, ramas, commits y Pull Requests se escribirán en inglés.
- La documentación podrá escribirse en español o inglés según corresponda, aunque se recomienda mantener un criterio consistente.
- Se priorizarán soluciones simples, legibles y mantenibles.
- Cada cambio deberá tener un objetivo concreto.
- Se evitará mezclar cambios no relacionados dentro de la misma rama o Pull Request.
- No se deberá desarrollar directamente sobre las ramas `main` o `develop`.
- Nunca se deberán subir claves, tokens, contraseñas o credenciales al repositorio.
- Todo código que ingrese a las ramas principales deberá respetar las reglas automáticas de formato, calidad y testing definidas por el proyecto.

---

# 2. Convenciones de código

## 2.1 Python

El código Python seguirá las convenciones estándar de la industria y las recomendaciones de PEP 8.

### Archivos y módulos

Los archivos Python utilizarán `snake_case`.

Ejemplos:

```text
audio_capture.py
speech_to_text.py
inventory_service.py
llm_client.py
database_manager.py
```

Evitar:

```text
AudioCapture.py
speechToText.py
inventory-service.py
```

### Variables

Las variables utilizarán `snake_case`.

```python
recognized_text = ""
product_quantity = 10
confirmation_message = ""
```

Las variables booleanas deberían expresar claramente una condición.

```python
is_connected = True
has_pending_operation = False
should_retry = True
```

Se evitarán nombres poco descriptivos.

Evitar:

```python
x = get_audio()
```

Preferir:

```python
audio_data = get_audio()
```

### Funciones y métodos

Las funciones y métodos utilizarán `snake_case`.

```python
def capture_audio():
    ...

def transcribe_audio():
    ...

def validate_llm_response():
    ...
```

Los nombres deberían representar una acción.

Preferir:

```python
validate_response()
save_operation()
get_inventory()
```

### Clases

Las clases utilizarán `PascalCase`.

```python
class AudioService:
    ...

class InventoryRepository:
    ...

class LLMClient:
    ...
```

### Constantes

Las constantes utilizarán `UPPER_SNAKE_CASE`.

```python
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 10
DATABASE_PATH = "data/inventory.db"
```

### Métodos o atributos internos

Los elementos internos podrán comenzar con `_`.

```python
def _parse_response():
    ...

_cached_connection = None
```

---

## 2.2 JavaScript

Si se utiliza JavaScript en la interfaz web:

### Variables y funciones

Se utilizará `camelCase`.

```javascript
const inventoryItems = [];
const confirmationMessage = "";

function loadInventory() {
    ...
}
```

### Clases

Se utilizará `PascalCase`.

```javascript
class InventoryClient {
    ...
}
```

### Constantes globales

Podrán utilizar `UPPER_SNAKE_CASE`.

```javascript
const API_BASE_URL = "/api";
```

---

## 2.3 HTML y CSS

Los identificadores, clases y nombres relacionados con HTML y CSS utilizarán preferentemente `kebab-case`.

```html
<div class="inventory-container">
    <button id="confirm-operation-button">
        Confirmar
    </button>
</div>
```

Los nombres deberán describir la función del elemento y no solamente su apariencia.

Evitar:

```text
box1
container2
blue-button
```

Preferir:

```text
inventory-card
confirmation-panel
search-button
```

---

# 3. Formato automático y calidad de código

El proyecto utilizará herramientas automáticas para mantener un estilo consistente.

Para Python se utilizará:

- Ruff para formateo.
- Ruff para linting.
- Pytest para testing.

Estas herramientas estarán configuradas en el repositorio.

Los desarrolladores no deberán configurar reglas diferentes en sus máquinas.

Antes de aceptar cambios, el código deberá superar los chequeos definidos por el proyecto.

Los principales comandos serán:

```bash
ruff format .
ruff format --check .
ruff check .
ruff check . --fix
pytest
```

`ruff format .` aplica el formato. `ruff format --check .` solo verifica y falla si hace falta formatear. `ruff check . --fix` intenta corregir problemas de lint de forma automática.

Después de clonar el repositorio hay que instalar los hooks de pre-commit **una vez**. Los scripts `scripts/setup.sh` y `scripts/setup.ps1` lo hacen. A partir de ese momento, cada `git commit` ejecuta formato, lint y validaciones básicas antes de crear el commit.

Si pre-commit modifica archivos, hay que revisarlos, volver a hacer `git add` y commitear de nuevo. El detalle de ese ciclo está en [docs/guides/development-workflow.md](docs/guides/development-workflow.md).

---

# 4. Documentación y comentarios

El código deberá ser lo suficientemente claro como para no depender de comentarios innecesarios.

Los comentarios deberían explicar principalmente el motivo de una decisión cuando no sea evidente.

Evitar:

```python
# Incrementa counter en uno
counter += 1
```

Preferir:

```python
# Se reintenta porque el servicio del modelo puede fallar
# temporalmente sin representar un error permanente.
retry_request()
```

Las funciones, clases y módulos no triviales deberán incluir documentación cuando su comportamiento no resulte evidente.

Ejemplo:

```python
def validate_llm_response(response: dict) -> bool:
    """Valida que la respuesta del modelo respete el esquema esperado."""
```

La documentación del proyecto deberá actualizarse cuando cambie:

- la arquitectura;
- la configuración;
- el entorno;
- las interfaces;
- el comportamiento visible del sistema.

---

# 5. Uso de tipos en Python

Se recomienda utilizar type hints en funciones, métodos y estructuras importantes.

Ejemplo:

```python
def add_stock(
    product_id: int,
    quantity: int,
) -> InventoryOperation:
    ...
```

En lugar de:

```python
def add_stock(product_id, quantity):
    ...
```

El uso de tipos facilita la lectura, detección de errores y mantenimiento del código.

---

# 6. Flujo de trabajo Git

El proyecto utilizará un flujo similar a Gitflow, simplificado para el tamaño del equipo.

Las ramas principales serán:

```text
main
develop
```

Y las ramas de trabajo serán:

```text
feature/*
fix/*
release/*
hotfix/*
```

Esquema general:

```text
feature/* ──┐
feature/* ──┼──> develop ──> release/* ──> main
fix/* ──────┘                         │
                                     └──> develop

hotfix/* ────────────────────────────> main
       └────────────────────────────> develop
```

---

# 7. Rama main

`main` representa versiones estables del proyecto.

Reglas:

- No desarrollar directamente sobre `main`.
- No realizar commits normales directamente sobre `main`.
- Los cambios llegarán normalmente mediante una Pull Request desde una rama de release.
- Cada versión estable deberá poseer un tag.
- El código en `main` deberá representar una versión funcional del sistema.

Ejemplos de tags:

```text
v0.1.0
v0.2.0
v1.0.0
```

---

# 8. Rama develop

`develop` será la rama principal de integración.

Las nuevas funcionalidades y correcciones normales deberán integrarse en esta rama.

Antes de crear una nueva rama:

```bash
git switch develop
git pull
```

Luego se crea la rama correspondiente:

```bash
git switch -c feature/audio-capture
```

No se deberá trabajar directamente sobre `develop`.

Los cambios deberán incorporarse mediante Pull Requests.

---

# 9. Ramas feature

Las ramas `feature` se utilizarán para nuevas funcionalidades.

Formato:

```text
feature/<descripcion>
```

Ejemplos:

```text
feature/audio-capture
feature/speech-to-text
feature/llm-client
feature/inventory-database
feature/web-dashboard
```

Se crearán desde `develop`.

Al finalizar la funcionalidad, se abrirá una Pull Request hacia `develop`.

Luego del merge, la rama deberá eliminarse.

---

# 10. Ramas fix

Las ramas `fix` se utilizarán para errores encontrados durante el desarrollo.

Formato:

```text
fix/<descripcion>
```

Ejemplos:

```text
fix/stt-timeout
fix/invalid-json-response
fix/database-connection
```

Se crearán desde `develop` y volverán a integrarse en `develop`.

---

# 11. Ramas release

Las ramas `release` se utilizarán para preparar una versión estable.

Formato:

```text
release/<version>
```

Ejemplo:

```text
release/0.2.0
```

Se crearán desde `develop`.

Durante una release solamente deberían realizarse:

- correcciones de errores;
- actualizaciones de documentación;
- ajustes de configuración;
- cambios de versión.

No deberían incorporarse nuevas funcionalidades importantes.

Cuando la release esté lista se integrará en:

```text
main
```

Y cualquier corrección realizada durante la release deberá volver también a:

```text
develop
```

---

# 12. Ramas hotfix

Las ramas `hotfix` se utilizarán solamente para errores urgentes encontrados en una versión ya publicada.

Formato:

```text
hotfix/<descripcion>
```

Ejemplo:

```text
hotfix/database-corruption
```

Se crearán desde `main`.

Luego deberán integrarse en:

```text
main
develop
```

---

# 13. Convención de commits

El proyecto utilizará Conventional Commits.

Formato general:

```text
<tipo>(<scope>): <descripcion>
```

El `scope` es opcional, aunque recomendado cuando ayuda a identificar el módulo afectado.

Ejemplos:

```text
feat(stt): add speech-to-text service
fix(database): handle failed connection
docs(readme): add installation instructions
refactor(llm): extract provider interface
test(inventory): add repository tests
chore(deps): update dependencies
```

---

# 14. Tipos de commit

## feat

Nueva funcionalidad.

```text
feat(audio): add USB microphone capture
```

## fix

Corrección de comportamiento.

```text
fix(stt): handle empty transcription
```

## docs

Cambios únicamente de documentación.

```text
docs: update architecture documentation
```

## refactor

Cambio interno que no modifica el comportamiento esperado.

```text
refactor(llm): extract provider abstraction
```

## test

Agregado o modificación de tests.

```text
test(database): add persistence tests
```

## chore

Tareas de mantenimiento.

```text
chore(deps): update dependencies
```

## build

Cambios relacionados con build o dependencias.

```text
build: configure project dependencies
```

## ci

Cambios relacionados con integración continua.

```text
ci: add pull request checks
```

## perf

Mejoras de rendimiento.

```text
perf(stt): reduce transcription latency
```

---

# 15. Reglas para los commits

Los mensajes deberán:

- escribirse en inglés;
- ser claros;
- ser breves;
- describir el cambio realizado;
- evitar terminar con punto.

Correcto:

```text
feat(web): add inventory search
fix(llm): reject malformed responses
refactor(audio): separate capture from transcription
```

Evitar:

```text
changes
fix
update
working
final
final-final
now it works
```

Cada commit debería representar un cambio lógico.

Durante el desarrollo de una rama se permiten varios commits intermedios.

Al integrar la Pull Request se utilizará Squash and Merge.

---

# 16. Pull Requests

Toda funcionalidad o corrección deberá ingresar mediante una Pull Request.

Ejemplo:

```text
feature/speech-to-text
        │
        ▼
   Pull Request
        │
        ▼
      develop
```

---

# 17. Título de una Pull Request

El título de la Pull Request deberá seguir Conventional Commits.

Ejemplo:

```text
feat(stt): implement speech-to-text pipeline
```

Otros ejemplos:

```text
fix(database): prevent duplicate operations
docs: add development setup guide
refactor(llm): introduce provider abstraction
```

El título es especialmente importante porque será utilizado como mensaje del commit final luego de realizar Squash and Merge.

---

# 18. Descripción de una Pull Request

Una Pull Request deberá incluir:

## Resumen

Qué se modificó.

## Cambios

Lista de cambios principales.

## Testing

Cómo se verificó que el cambio funciona.

## Información adicional

Limitaciones, decisiones técnicas, screenshots o información relevante.

Plantilla:

```markdown
## Resumen

Breve descripción del cambio.

## Cambios

- Cambio 1
- Cambio 2
- Cambio 3

## Testing

Explicar cómo se verificó.

## Información adicional

Cualquier detalle relevante.
```

---

# 19. Revisión de Pull Requests

Antes de realizar el merge se deberá verificar:

- que la funcionalidad opere correctamente;
- que la PR tenga un alcance claro;
- que el código respete las convenciones;
- que Ruff no reporte errores;
- que los tests relevantes pasen;
- que no existan credenciales o secretos;
- que no exista código temporal de debugging;
- que la documentación esté actualizada;
- que la rama destino sea correcta;
- que el título siga Conventional Commits.

Siempre que sea posible, otra persona del equipo deberá revisar la PR antes del merge.

---

# 20. Estrategia de merge

La estrategia por defecto será:

```text
Squash and Merge
```

Ejemplo de una rama:

```text
feat(stt): add audio capture
feat(stt): integrate transcription
fix(stt): handle empty audio
refactor(stt): extract service
```

Luego del Squash and Merge, `develop` recibirá solamente:

```text
feat(stt): implement speech-to-text pipeline
```

De esta manera se permite trabajar con varios commits durante el desarrollo manteniendo un historial principal limpio.

Después del merge deberá eliminarse la rama utilizada.

---

# 21. Versionado

El proyecto seguirá Semantic Versioning.

Formato:

```text
MAJOR.MINOR.PATCH
```

Ejemplo:

```text
1.4.2
```

Significado:

```text
MAJOR = cambios incompatibles o importantes
MINOR = nuevas funcionalidades compatibles
PATCH = correcciones compatibles
```

Durante el desarrollo inicial se utilizarán versiones menores a `1.0.0`.

Ejemplo:

```text
v0.1.0
v0.2.0
v0.2.1
```

La versión:

```text
v1.0.0
```

representará la primera versión estable que cumpla los objetivos primarios del proyecto.

---

# 22. Releases

Cada versión estable deberá integrarse en `main` y poseer un tag.

Flujo:

```text
feature/*
    │
    ▼
develop
    │
    ▼
release/x.y.z
    │
    ▼
main
    │
    ▼
vx.y.z
```

Ejemplo:

```text
release/0.1.0
```

Luego:

```text
v0.1.0
```

Las releases deberán incluir una descripción de los cambios principales incorporados.

---

# 23. Testing

Las funcionalidades deberán ser probadas antes de integrarse.

Se utilizará Pytest para las pruebas automatizadas de Python.

Se priorizarán tests en:

- validación de respuestas del LLM;
- operaciones de inventario;
- persistencia;
- endpoints web;
- máquina de estados;
- parsing y transformación de datos.

Las funcionalidades relacionadas directamente con hardware podrán requerir pruebas manuales o de integración.

Cuando un comportamiento no pueda automatizarse fácilmente, la Pull Request deberá indicar cómo fue probado.

---

# 24. Dependencias

Las dependencias deberán incorporarse solamente cuando aporten una ventaja clara al proyecto.

Antes de agregar una dependencia deberá verificarse:

- que esté mantenida;
- que sea compatible con la versión de Python usada;
- que sea compatible con Raspberry Pi;
- que sus requerimientos de recursos sean razonables.

Las dependencias deberán declararse en la configuración del proyecto y no depender de instalaciones manuales realizadas en una máquina particular.

---

# 25. Secrets y configuración

Nunca se deberán subir al repositorio:

```text
API keys
tokens
passwords
private keys
credentials
```

Los secretos deberán manejarse mediante variables de entorno.

Ejemplo:

```text
OPENAI_API_KEY
GEMINI_API_KEY
```

El archivo:

```text
.env
```

deberá estar incluido en `.gitignore`.

Se podrá incluir:

```text
.env.example
```

Ejemplo:

```env
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=
```

---

# 26. Limpieza del repositorio

No deberán subirse archivos generados localmente que no formen parte del proyecto.

Ejemplos:

```text
__pycache__/
*.pyc
.venv/
.env
.idea/
*.log
```

Los archivos temporales de debugging deberán eliminarse antes de abrir una Pull Request.

---

# 27. Flujo de trabajo recomendado

La primera vez, después de clonar:

```bash
# Windows
.\scripts\setup.ps1

# Linux / Raspberry Pi
./scripts/setup.sh
```

Eso crea `.venv`, instala el proyecto con las dependencias de desarrollo e instala los hooks de pre-commit.

Actualizar `develop`:

```bash
git switch develop
git pull
```

Crear una rama:

```bash
git switch -c feature/speech-to-text
```

Trabajar normalmente.

Agregar cambios:

```bash
git add .
```

Crear commit:

```bash
git commit -m "feat(stt): add transcription service"
```

Subir la rama:

```bash
git push -u origin feature/speech-to-text
```

Abrir Pull Request hacia:

```text
develop
```

Esperar:

```text
Ruff
Pytest
Review
```

Si todo está correcto:

```text
Squash and Merge
```

Eliminar la rama.

Actualizar nuevamente:

```bash
git switch develop
git pull
```

Y comenzar la siguiente tarea.

---

# 28. Resumen rápido

## Python

```text
Archivos       snake_case.py
Variables      snake_case
Funciones      snake_case
Clases         PascalCase
Constantes     UPPER_SNAKE_CASE
```

## JavaScript

```text
Variables      camelCase
Funciones      camelCase
Clases         PascalCase
```

## HTML/CSS

```text
kebab-case
```

## Ramas

```text
main
develop

feature/<descripcion>
fix/<descripcion>
release/<version>
hotfix/<descripcion>
```

## Commits

```text
feat(scope): description
fix(scope): description
docs(scope): description
refactor(scope): description
test(scope): description
chore(scope): description
build(scope): description
ci(scope): description
perf(scope): description
```

## Merge

```text
Squash and Merge
```

## Versionado

```text
Semantic Versioning

vMAJOR.MINOR.PATCH
```
