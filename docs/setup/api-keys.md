# Claves de API para desarrollo y benchmarks

## Preparación

Desde la raíz del repositorio:

```bash
cp config/api-keys.env.example config/api-keys.env
chmod 600 config/api-keys.env
```

Completá el archivo local con `GEMINI_API_KEY`, `GROQ_API_KEY` y, cuando
corresponda, `LLM_API_KEY`. Usá valores entre comillas y en una sola línea.
La plantilla vacía se versiona; `config/api-keys.env` está ignorado por Git.
No commitees primero el archivo real: `.gitignore` no deja de seguir archivos
que ya estén versionados.

## Carga automática

Estos scripts llaman a `load_api_keys()` al arrancar:

- `scripts/benchmarks/precision_benchmark.py`
- `scripts/benchmarks/gemini_benchmark.py`
- `scripts/benchmarks/audio_stt_llm_benchmark.py`
- `scripts/benchmarks/audio_stt_gemini_benchmark.py`
- `scripts/benchmarks/audio_stt_groq_benchmark.py`
- `scripts/integration/audio_stt_llm_ssh.py` (coordinador en PC)

El cargador compartido es [api_keys.py](../../scripts/benchmarks/api_keys.py).
Busca `config/api-keys.env` respecto de la ubicación del repositorio, no respecto
de la carpeta actual. Funciona tanto con Conda como con venv; activar un entorno
por sí solo no carga este archivo.

Las variables existentes y no vacías del entorno tienen prioridad. El archivo
completa las ausentes o vacías; los valores vacíos del archivo no borran claves
del entorno. Si el archivo no existe, se conservan las variables del entorno y
cada proveedor valida si tiene la clave necesaria.

Para actualizar una clave, editá el archivo y reiniciá el script. Si también
está definida en la terminal, quitá esa variable antes de ejecutar para usar el
valor nuevo del archivo:

```bash
unset GEMINI_API_KEY
python scripts/benchmarks/gemini_benchmark.py --help
```

Python acepta comentarios, asignaciones simples y el prefijo opcional `export`.
No ejecuta comandos, expande variables ni admite valores multilínea. Los errores
indican el número de línea sin mostrar la clave.

## Nuevas implementaciones

Los nuevos scripts de benchmarks deben reutilizar el cargador al inicio de
`main()`, antes de consultar las claves o crear clientes de API:

```python
def main():
    from api_keys import load_api_keys

    load_api_keys()
    # Leer os.environ y crear el cliente después de la carga.
```

Ese import corresponde a scripts ubicados en `scripts/benchmarks/`. Para agregar
otra variable, actualizá `ALLOWED_KEYS` en el cargador y la plantilla vacía.
No guardes claves en logs, reportes, prompts ni volcados completos de variables.
La lectura de este archivo es una ayuda local para benchmarks; no establece
automáticamente un mecanismo de configuración de producción en `src/`.

## Comandos que todavía no integran el cargador

El wrapper Bash permite cargar las claves antes de cualquier comando:

```bash
./scripts/run_with_api_keys.sh python scripts/benchmarks/llm_benchmark.py
```

Conserva el Python del Conda o venv activo y ejecuta desde la raíz del repo.
El wrapper usa `source`, por lo que el archivo también debe ser compatible con
Bash. A diferencia del cargador Python, las asignaciones del archivo reemplazan
las variables existentes para ese comando. El wrapper no modifica la terminal
desde la que se lo ejecuta.
