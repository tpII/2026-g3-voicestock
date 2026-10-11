# Claves locales de API

Copiá `api-keys.env.example` a `api-keys.env` en esta carpeta y completá
las claves. El archivo local está ignorado por Git; la plantilla queda
disponible para versionar sin credenciales.

Los benchmarks de precisión, Gemini y audio → STT → LLM cargan este archivo
automáticamente, sin importar el directorio desde el que se ejecuten.
Las variables ya definidas en el entorno tienen prioridad. Reiniciá el
benchmark para cargar cambios del archivo; si una variable está definida en
tu terminal, actualizala o quitála para usar el valor del archivo.

Usá asignaciones de una sola línea con valores entre comillas. La carga desde
Python no ejecuta comandos ni expande variables.

Ver [la guía completa de claves de API](../docs/setup/api-keys.md) para
integrar el cargador en nuevos scripts y usar el wrapper Bash.
