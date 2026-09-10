# Flujo de trabajo de desarrollo

Esta guía explica cómo trabajar en VoiceStock si todavía no tenés mucha práctica con Git, Pull Requests, pre-commit o CI.

El objetivo es que puedas clonar el repositorio, crear una rama, commitear, abrir una Pull Request y llegar a `develop` sin adivinar el proceso.

Las convenciones (nombres, commits, ramas y versionado) están en [CONTRIBUTING.md](../CONTRIBUTING.md).

## Mapa rápido

```text
clonar repo
    │
    ▼
scripts/setup.*          ← una sola vez
    │
    ▼
rama feature/* o fix/*   ← desde develop
    │
    ▼
editar + commit          ← pre-commit corre solo
    │
    ▼
push + Pull Request      ← hacia develop
    │
    ▼
CI verde + review
    │
    ▼
Squash and Merge
    │
    ▼
borrar la rama y actualizar develop
```

Docker no forma parte de este arranque. Más adelante se puede agregar para servicios de software o para desplegar un modelo de lenguaje local, si eso aporta un beneficio concreto. Las partes que dependen del hardware de la Raspberry Pi (por ejemplo el micrófono) se ejecutarán de forma nativa al principio: meter esos dispositivos en un contenedor agregaría complejidad innecesaria ahora.

---

## A. Preparación inicial

Cloná el repositorio y entrá a la carpeta del proyecto:

```bash
git clone <url-del-repositorio>
cd voicestock
```

### Windows

En PowerShell:

```powershell
.\scripts\setup.ps1
```

Si PowerShell bloquea la ejecución de scripts, podés usar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

En Windows el script busca un CPython oficial (instalador de python.org, Microsoft Store o Anaconda). El Python de MSYS2 no sirve para este proyecto: paquetes como Ruff no publican ruedas para esa plataforma.

### Linux / Raspberry Pi

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Qué hace el script

El script se puede volver a ejecutar sin problema. En cada corrida:

1. Comprueba que exista Python 3.11 o superior.
2. Crea `.venv` si todavía no existe. No instala paquetes de Python de forma global.
3. Actualiza `pip` dentro de ese entorno.
4. Instala el proyecto en modo editable junto con las dependencias de desarrollo (`ruff`, `pytest`, `pytest-cov`, `pre-commit`).
5. Instala los hooks de pre-commit. Esto hay que hacerlo **una vez** después de clonar; a partir de ahí, cada `git commit` los usa automáticamente.

Cuando termine, activá el entorno virtual:

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux / Raspberry Pi:

```bash
source .venv/bin/activate
```

Si el prompt muestra `(.venv)`, los comandos `ruff`, `pytest` y `pre-commit` van a usar las herramientas del proyecto.

---

## B. Empezar una tarea nueva

Nunca trabajes directo sobre `main` ni `develop`. Esas ramas se actualizan con Pull Requests.

Antes de crear tu rama, alineate con `develop`:

```bash
git switch develop
git pull
git switch -c feature/example-feature
```

Por qué se hace así:

- `git switch develop` te pone en la rama de integración.
- `git pull` baja lo último que ya se mergeó. Si te salteás este paso, tu rama nace desactualizada y después aparecen conflictos.
- `git switch -c feature/example-feature` crea una rama tuya. El nombre va en inglés, igual que los commits.

Si la tarea es una corrección y no una funcionalidad nueva, usá `fix/...` en lugar de `feature/...`.

---

## C. Trabajar en el código

Editá los archivos que correspondan a la tarea. No mezcles cambios de temas distintos en la misma rama.

Antes de commitear podés correr, de forma opcional:

```bash
ruff format .
ruff check . --fix
pytest
```

No es obligatorio hacerlo a mano: pre-commit vuelve a revisar formato y lint en el commit. Sí conviene correr `pytest` vos, porque el hook local no ejecuta la suite completa.

---

## D. Crear commits

```bash
git add .
git commit -m "feat(scope): description"
```

El mensaje va en inglés y sigue Conventional Commits. Ejemplos:

```text
feat(stt): add speech-to-text service
fix(database): handle failed connection
docs: explain local setup
```

Al hacer `git commit`, pre-commit corre solo:

```text
git commit
    │
    ▼
pre-commit
    │
    ├─ quita espacios sobrantes
    ├─ asegura salto de línea al final del archivo
    ├─ valida YAML y TOML
    ├─ busca claves privadas y conflictos de merge
    ├─ Ruff lint (--fix)
    └─ Ruff format
    │
    ▼
si todo pasa, el commit se crea
```

Si pre-commit **modifica archivos** (por ejemplo, Ruff reformatea código), el commit se aborta. Eso es normal.

Qué hacer:

1. Revisá el diff: `git diff`.
2. Si los cambios están bien: `git add .`
3. Volvé a commitear con el mismo mensaje.

No hace falta pelear contra el formateo. Dejá que Ruff unifique el estilo.

Si el hook **falla** (lint, YAML inválido, clave privada, etc.), hay que corregir el problema a mano y commitear de nuevo. Git no va a dejar pasar ese commit.

---

## E. Subir la rama

```bash
git push -u origin feature/example-feature
```

`-u origin ...` guarda el seguimiento la primera vez. Después alcanza con `git push`.

---

## F. Abrir una Pull Request hacia `develop`

En GitHub, abrí una Pull Request con:

- **base:** `develop`
- **compare:** tu rama `feature/...` o `fix/...`

El título también sigue Conventional Commits, porque Squash and Merge lo usa como mensaje final en `develop`.

Completá la plantilla:

- Resumen
- Cambios
- Testing
- Información adicional

Pedí revisión a alguien del equipo y esperá a que CI termine.

---

## G. Checks locales y checks remotos

Hay dos capas. Usan la misma configuración (`.pre-commit-config.yaml`), pero no dependen una de la otra.

**Local.** Al hacer `git commit`, pre-commit corre solo en tu máquina (formato, lint, YAML, TOML, etc.). Pytest no forma parte de ese hook: conviene correrlo vos antes de pushear.

**Remoto.** Al hacer push o abrir una Pull Request, GitHub Actions vuelve a correr los checks. Así GitHub no asume que cada persona instaló los hooks ni que su entorno local está bien configurado.

```text
Developer
   |
   | git commit
   v
pre-commit
   |
   v
commit
   |
   | git push
   v
GitHub Actions
   |
   +-- pre-commit run --all-files
   +-- pytest --cov=voicestock
   |
   v
Pull Request can be merged only if required checks pass
```

CI corre en pushes y Pull Requests hacia `main` y `develop`. Hoy no hay umbral mínimo de coverage: se genera el reporte, pero un porcentaje bajo no hace fallar el job.

Si CI está en rojo, no mergees. Corregí en tu rama, hacé commit y push. La PR se actualiza sola y CI vuelve a correr.

---

## H. Merge

Usamos **Squash and Merge**.

Si en tu rama hiciste varios commits:

```text
feat(stt): add capture helper
feat(stt): wire transcription
fix(stt): handle empty audio
```

`develop` recibe un solo commit, con el título de la PR:

```text
feat(stt): implement speech-to-text pipeline
```

Así se puede commitear seguido en la rama de trabajo y el historial de `develop` queda corto y legible.

---

## I. Limpieza después del merge

GitHub puede borrar la rama remota al mergear. En tu máquina:

```bash
git switch develop
git pull
git branch -d feature/example-feature
```

`git pull` trae el commit squash a `develop`. Recién ahí conviene arrancar la siguiente tarea.

---

## J. Flujo de corrección (`fix`)

Igual que una feature, pero la rama nace para un bug encontrado durante el desarrollo:

```bash
git switch develop
git pull
git switch -c fix/stt-timeout
```

La Pull Request también apunta a `develop`.

```text
develop
   │
   └── fix/stt-timeout ── PR ──► develop
```

---

## K. Flujo de release

Cuando `develop` tiene un conjunto de cambios listo para publicar:

```text
develop
   │
   └── release/x.y.z
            │
            ├── PR ──► main      ← versión estable
            ├── PR ──► develop   ← si hubo arreglos en la release
            └── tag  vx.y.z      ← sobre main
```

En la rama `release/x.y.z` no se agregan funcionalidades nuevas. Solo correcciones, documentación, versión y preparación del tag.

---

## L. Flujo de hotfix

Si un error aparece en una versión ya publicada en `main`:

```text
main
  │
  └── hotfix/database-corruption
              │
              ├── PR ──► main
              └── PR ──► develop
```

El hotfix nace de `main` porque el problema está en lo publicado. Después hay que llevar el mismo arreglo a `develop` para que no se pierda en la siguiente release.

---

## Resumen de comandos frecuentes

```bash
# entorno
source .venv/bin/activate          # Linux / Raspberry Pi
.venv\Scripts\Activate.ps1         # Windows

# calidad local
ruff format .
ruff check . --fix
pytest

# lo mismo que corre CI
pre-commit run --all-files
pytest --cov=voicestock

# git
git switch develop
git pull
git switch -c feature/nombre-en-ingles
git add .
git commit -m "feat(scope): description"
git push -u origin feature/nombre-en-ingles
```
