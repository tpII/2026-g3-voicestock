# Prueba de prompts: STT en Raspberry y LLM desde PC

## Alcance y estado

El nuevo ejecutor usa los seis audios básicos/habituales existentes. Desde la
PC transfiere únicamente sus WAV, ejecuta Whisper Small Q5_1 en la Raspberry
por SSH, recibe transcripciones y métricas, y llama a `openai/gpt-oss-20b` vía
Groq desde la PC. Una transcripción y una llamada por caso, sin calentamiento
ni reintentos. No requiere micrófono, pulsador ni terminal remota interactiva.

Implementado pero **todavía no ejecutado en Raspberry Pi**. La compilación ARM,
instalación y viabilidad de Small siguen pendientes de comprobar. Este ejecutor
no reemplaza la prueba de audio real PTT requerida por SpeechToText-06.
Los benchmarks y tests existentes no fueron modificados por este incremento.

```mermaid
flowchart LR
    A[PC: WAV de prompts] -->|Archivo por SSH| B[Raspberry: Whisper]
    B -->|Texto y métricas por SSH| C[PC: coordinador]
    C -->|Texto por API| D[Groq GPT OSS 20B]
    D -->|JSON| E[PC: evaluación e informe]
```

SSH es el transporte de este experimento. La comunicación HTTP del sistema
existente no se modifica. No se aplica ninguna operación al inventario.

## 1. Preparar la Raspberry una vez

Subí el código del repo incluyendo los archivos nuevos de este incremento.
`git pull` sólo trae cambios ya publicados: un commit local sin push o archivos
sin commit no aparecen automáticamente en la Pi. No transfieras el archivo de
claves ni el entorno Conda/venv de la PC.

Se requiere Python 3.11+, Git, CMake, g++, tar y SSH. Confirmá primero el modelo
real de Pi, RAM disponible, OS y arquitectura. En la terminal de la Pi, desde
el repo (adaptá las rutas y el ejecutable Python instalado):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[stt-integration]'
bash scripts/integration/build_whisper_worker.sh
```

El build usa la revisión de whisper.cpp fijada en el proyecto y un job por
defecto para limitar consumo de compilación. Se compila **en la Raspberry**;
el binario x86 de la PC no sirve para ARM. Si no está instalado el código fuente
del motor, el build requiere Internet durante la instalación. En operación,
Whisper no usa red. Si la Pi no tiene acceso durante instalación, prepará y
copiá el checkout de esa revisión bajo `.tools/stt/whisper.cpp` desde la PC,
además de disponer de las dependencias de compilación.

Los pesos están ignorados por Git. Copialos una vez desde tu PC, usando tu alias
SSH y la ruta real del repo remoto (los siguientes son ejemplos):

```bash
ssh raspberry 'mkdir -p /home/pi/voicestock/models/stt/whisper'
scp models/stt/whisper/ggml-small-q5_1.bin raspberry:/home/pi/voicestock/models/stt/whisper/
```

El worker debe quedar en `.tools/stt/whisper-benchmark-worker`. Su configuración
es CPU, español, greedy, temperatura cero, sin contexto entre solicitudes y sin
VAD. La conversión PCM16 a float32 se realiza dentro del adaptador STT.

## 2. Preparar la PC una vez

Activá tu Conda o venv e instalá el proyecto con el extra de instrumentación:

```bash
conda activate voicestock
python -m pip install -e '.[stt-integration]'
```

Completá `GROQ_API_KEY` en `config/api-keys.env`, sólo en la PC; el ejecutor la
carga automáticamente siguiendo [la guía de claves](../setup/api-keys.md).
La PC necesita Internet para Groq. La Raspberry sólo necesita acceso SSH desde
la PC y sus archivos locales.

Configurá un alias en `~/.ssh/config` o usá `usuario@direccion`. SSH debe estar
habilitado. Por defecto se usa autenticación por clave sin pedir contraseña.
Para usar contraseña, agregá `--ssh-password` y ejecutá desde una terminal
interactiva en la PC. OpenSSH pide la contraseña directamente en esa terminal;
el script no la recibe ni la guarda. Puede pedirla dos veces: para transferir
los audios y para iniciar el worker. El servidor debe permitir este método.
Verificá manualmente `ssh raspberry` una vez para registrar la identidad del
host. Ambos modos mantienen la comprobación de identidad del host.

## 3. Ejecutar desde la PC

Un solo comando, sin abrir otra terminal para cada audio:

```bash
python scripts/integration/audio_stt_llm_ssh.py \
  --host raspberry \
  --remote-repo /home/pi/voicestock \
  --remote-python /home/pi/voicestock/.venv/bin/python
```

Reemplazá el alias, usuario y rutas. `--remote-repo` debe ser absoluto.
`--port` permite un puerto SSH diferente. `--threads` vale 4 por defecto;
`--timeout` vale 600 segundos y limita esperas de transferencia, STT y API.
El timeout es una protección, no un umbral de aceptación de latencia.
El coordinador actual está preparado para PC Linux/WSL: usa selectores sobre
pipes y requiere los ejecutables `ssh` y `tar` en los equipos correspondientes.

El ejecutor transfiere un archivo tar con los WAV por stdin de SSH a una carpeta
única `.cache/integration/pi_ssh_*` en la Pi. No copia claves ni pesos. Luego
inicia `stt_remote_worker.py` con otra conexión SSH y usa mensajes JSON por
stdin/stdout. El modelo permanece cargado durante los seis casos. Los hashes de
cada WAV se comprueban en ambos extremos; el hash del modelo remoto también se
compara con el local cuando la PC conserva una copia.

## 4. Resultados y métricas

En la PC: `reports/audio-stt-llm/pi_ssh_TIMESTAMP_ID/`:

- `benchmark_report.md`: referencia, transcripción remota, JSON esperado y real,
  evaluación y métricas por caso.
- `results.json`: respuestas originales, prompts efectivos y errores.
- `benchmark_cases.csv`: exactitud y RAM por caso.
- `environment.json`: hardware/OS/arquitectura remotos, carga, hashes y parámetros.
- `ssh.log`: diagnóstico de SSH/worker, ignorado por Git.

Se mide carga inicial aparte del procesamiento. El procesamiento medido por
solicitud incluye validación/lectura del WAV, conversión y STT; no es el mismo
intervalo de inferencia pura de los benchmarks anteriores. RSS/CPU se miden en
el proceso Whisper, con muestreo objetivo cada 10 ms; Python remoto, sistema y
caché no están incluidos en ese RSS. También se registra duración de la etapa
completa. En la PC se mide RSS del coordinador durante la llamada API, no RAM
del modelo remoto. Picos breves pueden escapar al muestreo.

El comando devuelve código 0 sólo si los seis casos terminan y sus JSON
coinciden exactamente con lo esperado; cualquier fallo devuelve código 1.

Los errores de API se conservan, sin convertirlos en errores semánticos. Un
error de STT no dispara una llamada al LLM. Una desconexión o timeout conserva
el reporte parcial. Los audios y el log permanecen en la carpeta remota registrada
para inspección; no se borran automáticamente. La conexión del worker se cierra
normalmente al terminar.

Antes de considerar aceptado el STT, verificá los textos esperados escuchando
los audios y fijá umbrales específicos para Pi. Esta prueba no cubre silencio,
PTT físico ni integración HTTP con InterpretationService.

## Archivos e integración posterior

- `src/pi/speech_to_text/contracts.py`: puerto `SpeechToText` y `TranscriptionError`.
- `src/pi/speech_to_text/whisper_adapter.py`: `WhisperAdapter.transcribe(Path)`.
- `scripts/integration/stt_remote_worker.py`: instrumentación y protocolo SSH.
- `scripts/integration/audio_stt_llm_ssh.py`: transferencia, llamada Groq y reporte.
- `scripts/integration/build_whisper_worker.sh`: compilación para el equipo destino.

El adaptador no importa benchmarks ni accede a GPIO/red. El worker de prueba
reutiliza instrumentación de benchmarks y el coordinador reutiliza su contrato
experimental; ninguno define el contrato de producción. El llamador de aplicación
puede reutilizar `WhisperAdapter` después, conectándolo a `AudioCaptureResult`.
Las implementaciones del proveedor LLM de producción y la orquestación física
siguen pendientes. El adaptador es secuencial; no comparte una instancia entre
transcripciones concurrentes.

## Elegir modelo y contexto STT

`--stt-model` acepta el nombre del archivo instalado en
`models/stt/whisper/` de la Raspberry; por defecto `ggml-small-q5_1.bin`.
`--stt-prompt` acepta una o varias rutas locales en la PC de TXT UTF-8 no vacíos.
Se concatenan en el orden indicado, separados por una línea en blanco.
El coordinador copia ese texto a la Pi y registra contenido y SHA-256 en el
informe. Sin este parámetro no se usa contexto. El catálogo contiene sólo
vocabulario de productos, sin cantidades ni respuestas esperadas.

Ejemplo con Base y catálogo:

```bash
python scripts/integration/audio_stt_llm_ssh.py \
  --host usuario@IP_RASPBERRY \
  --remote-repo /ruta/al/repositorio \
  --remote-python /ruta/al/repositorio/.venv/bin/python \
  --ssh-password \
  --stt-model ggml-base.bin \
  --stt-prompt scripts/benchmarks/prompts/contexto-stt.txt scripts/benchmarks/prompts/productos-stt.txt
```

Descargá previamente `ggml-base.bin` en la carpeta de modelos de la Pi.
Después de actualizar el código, recompilá allí con
`bash scripts/integration/build_whisper_worker.sh`. El worker de integración
usa `initial_prompt` de whisper.cpp en cada solicitud y lo mantiene en cada
ventana del mismo audio; no conserva contexto entre audios. El contexto puede
sesgar la transcripción y no garantiza reconocimiento correcto.
Los workers y ejecutores de benchmarks anteriores permanecen sin cambios.

El reporte incluye tasa de JSON exacto general y por nivel, tabla por prompt
con tiempos STT/API y RAM, promedios, rangos, sumas y carga inicial.
El CSV incluye tiempos y CPU. `environment.json` registra las rutas y hashes
de ambos TXT y el contexto combinado enviado a Whisper. El catálogo anterior
se llama ahora `productos-stt.txt`; no hay que recompilar por cambiar estos TXT.
