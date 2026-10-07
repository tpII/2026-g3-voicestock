# Benchmark de LLMs para extracción de inventario

## Ejecución

Desde la raíz del repositorio, instalá la dependencia opcional para medir RAM:

```bash
pip install ".[benchmark]"
```

Con Ollama ejecutándose y los modelos descargados, corré el benchmark:

```bash
python scripts/benchmarks/llm_benchmark.py
```

Los resultados de cada corrida se guardan en `reports/llm-benchmark/`. El script también genera el informe Markdown; para regenerarlo manualmente:

```bash
python scripts/benchmarks/analyze_llm_benchmark.py --results-directory reports/llm-benchmark/NOMBRE_DE_LA_CORRIDA
```

Para incluir la comparación con Groq se requiere definir `GROQ_API_KEY` en el entorno; esa clave nunca debe incluirse en el repositorio.

---

## 1. Objetivo

Crear un programa de benchmark que compare distintos LLMs locales
ejecutados mediante Ollama en la misma computadora.

El objetivo principal es determinar qué modelo ofrece la mejor relación
entre:

-   latencia;
-   velocidad de generación;
-   consumo de memoria RAM;
-   cumplimiento estricto del formato JSON;
-   identificación correcta de productos;
-   identificación correcta de cantidades;
-   capacidad de interpretar instrucciones, negaciones y referencias
    dentro de una frase larga.

Este benchmark está pensado para un sistema de inventario por voz cuyo
flujo futuro será aproximadamente:

``` text
Micrófono
   ↓
STT
   ↓
Texto
   ↓
LLM local
   ↓
JSON estructurado
   ↓
Validación
   ↓
API
   ↓
Base de datos remota
```

En este benchmark NO se evalúa el STT, la API ni la base de datos. Se
evalúa únicamente el paso:

``` text
Texto → LLM → JSON
```

La computadora utilizada tiene 8 GB de RAM y los modelos se ejecutan
principalmente por CPU, por lo que la latencia y el consumo de memoria
son especialmente importantes.

------------------------------------------------------------------------

## 2. Modelos a comparar

El programa debe permitir configurar fácilmente la lista de modelos,
pero inicialmente se quieren probar los siguientes:

1.  `llama3.2:1b`
    -   Clase aproximada: 1B parámetros.
    -   Objetivo: establecer una referencia de muy baja latencia.
2.  `qwen3:1.7b`
    -   Clase aproximada: 1.7B.
    -   Objetivo: evaluar el equilibrio entre velocidad y capacidad.
3.  `granite3.1-dense:2b`
    -   Clase aproximada: 2B.
    -   Objetivo: evaluar un modelo orientado a instrucciones y tareas
        estructuradas.
4.  `qwen3.5:2b`
    -   Clase aproximada: 2B.
    -   Objetivo: comparar una generación más nueva de Qwen con otros
        modelos pequeños.
5.  `qwen2.5:3b-instruct`
    -   Clase aproximada: 3B.
    -   Objetivo: comprobar cuánto mejora la precisión al subir de
        tamaño.
6.  `qwen3:4b-instruct`
    -   Clase aproximada: 4B.
    -   Este modelo ya se está utilizando y funcionará como referencia
        de mayor tamaño.

El código NO debe asumir que todos los modelos están instalados. Antes
de ejecutar el benchmark debe verificar cuáles están disponibles en
Ollama e informar claramente los faltantes.

------------------------------------------------------------------------

## 3. Condición fundamental del benchmark

Todos los modelos deben recibir EXACTAMENTE el mismo prompt.

No modificar, resumir, adaptar ni optimizar el prompt dependiendo del
modelo.

La finalidad es comparar los modelos bajo las mismas condiciones.

También deben mantenerse iguales, en la medida en que Ollama y cada
modelo lo permitan:

-   contexto;
-   temperatura;
-   parámetros de generación;
-   prompt;
-   hardware;
-   método de medición;
-   formato esperado.

Usar temperatura baja o determinista, idealmente `temperature = 0`, si
el modelo/API lo permite.

No incluir conversación previa.

Cada prueba debe ser independiente.

------------------------------------------------------------------------

## 4. Prompt literal de prueba

Este es el prompt que debe enviarse literalmente a cada modelo:

``` text
Sos un sistema de extracción de datos para un inventario.

Tu única tarea es leer el mensaje del usuario, identificar todos los productos mencionados y devolverlos en formato JSON.

Respondé ÚNICAMENTE con JSON válido.
No saludes.
No expliques.
No agregues comentarios.
No muestres tu razonamiento.
No escribas nada antes ni después del JSON.

BASE DE DATOS DE PRODUCTOS:

- Coca Cola 2L
- Coca Cola 1.5L
- Coca Cola Zero 2L
- Sprite 2L
- Sprite 1.5L
- Agua Villavicencio 1.5L
- Arroz Gallo 1kg
- Fideos Matarazzo 500g
- Detergente Magistral 750ml
- Leche La Serenísima 1L

REGLAS:

- Detectá TODOS los productos mencionados en el mensaje.
- "producto" debe contener EXACTAMENTE el nombre correspondiente de la base de datos.
- Interpretá nombres coloquiales, abreviaciones y formas naturales de hablar.
- Usá marca, tamaño, tipo y presentación para distinguir productos.
- Convertí cantidades escritas con palabras a números.
- Cada producto debe aparecer como un objeto separado.
- No combines productos diferentes.
- Nunca inventes productos que no estén en la base de datos.
- Ignorá información que no corresponda a producto o cantidad.
- Si un producto no puede identificarse con seguridad, usá null.
- Si falta la cantidad de un producto, usá null.

FORMATO OBLIGATORIO:

{
  "productos": [
    {
      "producto": "nombre exacto",
      "cantidad": 0
    }
  ]
}

MENSAJE DEL USUARIO:

"Bueno, anotame lo que acaba de llegar porque fueron varias cosas. Primero bajaron veinte cocas comunes de dos litros y también dejaron doce Coca Zero, las grandes de dos litros. Después trajeron ocho Sprite de litro y medio y otras seis Sprite grandes de dos litros. De almacén llegaron quince paquetes de arroz Gallo de un kilo y veinticuatro paquetes de fideos Matarazzo de medio kilo. También dejaron nueve detergentes Magistral de 750 y, antes de que me olvide, llegaron dieciocho leches La Serenísima de un litro. Las aguas que estaban en el camión al final no las bajaron, así que esas no las cargues."
```

------------------------------------------------------------------------

## 5. Resultado correcto esperado

La respuesta semánticamente correcta contiene exactamente estos ocho
productos:

``` json
{
  "productos": [
    {
      "producto": "Coca Cola 2L",
      "cantidad": 20
    },
    {
      "producto": "Coca Cola Zero 2L",
      "cantidad": 12
    },
    {
      "producto": "Sprite 1.5L",
      "cantidad": 8
    },
    {
      "producto": "Sprite 2L",
      "cantidad": 6
    },
    {
      "producto": "Arroz Gallo 1kg",
      "cantidad": 15
    },
    {
      "producto": "Fideos Matarazzo 500g",
      "cantidad": 24
    },
    {
      "producto": "Detergente Magistral 750ml",
      "cantidad": 9
    },
    {
      "producto": "Leche La Serenísima 1L",
      "cantidad": 18
    }
  ]
}
```

El orden de los elementos no debería afectar la evaluación de precisión,
siempre que estén presentes exactamente los mismos pares
producto/cantidad.

### Caso negativo importante

NO debe aparecer:

``` text
Agua Villavicencio 1.5L
```

El texto menciona agua, pero explícitamente dice:

> "Las aguas que estaban en el camión al final no las bajaron, así que
> esas no las cargues."

Esto sirve para comprobar si el modelo entiende una negación/instrucción
contextual en vez de limitarse a detectar palabras clave.

------------------------------------------------------------------------

## 6. Métricas obligatorias

Para cada ejecución registrar como mínimo:

### 6.1 Latencia hasta el primer token

Medir el tiempo desde que se envía la solicitud a Ollama hasta que se
recibe el primer fragmento/token generado.

Nombre sugerido:

``` text
time_to_first_token_ms
```

Para medirlo correctamente se debe utilizar streaming.

### 6.2 Tiempo total

Tiempo desde el envío de la solicitud hasta recibir la respuesta
completa.

``` text
total_latency_ms
```

### 6.3 Velocidad de generación

Registrar los tokens generados por segundo.

``` text
tokens_per_second
```

Siempre que sea posible, utilizar las métricas nativas devueltas por
Ollama (por ejemplo, conteo de evaluación y duración de evaluación) en
lugar de estimaciones basadas en palabras.

### 6.4 Tokens

Registrar:

``` text
prompt_tokens
output_tokens
```

si Ollama devuelve esa información.

### 6.5 Memoria RAM

Intentar registrar el consumo de memoria asociado a Ollama /
`llama-server` durante la ejecución.

Como mínimo:

``` text
ram_before_mb
ram_peak_mb
ram_after_mb
```

Si es posible, diferenciar:

-   RAM total del sistema;
-   RAM disponible;
-   working set de `llama-server`;
-   pico observado durante la inferencia.

Documentar claramente qué definición de RAM se está utilizando.

### 6.6 JSON válido

Comprobar programáticamente si la respuesta completa puede parsearse
como JSON sin realizar reparaciones.

``` text
valid_json = true/false
```

No limpiar Markdown, quitar \`\`\`json, extraer objetos con regex ni
corregir la salida antes de esta evaluación.

Queremos saber si el modelo obedeció realmente la instrucción de
devolver únicamente JSON.

### 6.7 Cumplimiento del esquema

Comprobar que exista:

``` json
{
  "productos": []
}
```

y que cada elemento tenga exclusivamente/al menos los campos requeridos:

``` text
producto
cantidad
```

Registrar:

``` text
schema_valid = true/false
```

### 6.8 Productos correctos

Comparar los productos devueltos contra el resultado esperado.

Registrar, como mínimo:

``` text
expected_products
correct_products
missing_products
extra_products
```

### 6.9 Cantidades correctas

Comparar las cantidades producto por producto.

Registrar:

``` text
correct_quantities
incorrect_quantities
```

### 6.10 Negación del agua

Registrar específicamente:

``` text
excluded_water_correctly = true/false
```

Debe ser `true` solamente si el modelo NO carga Agua Villavicencio.

### 6.11 Exactitud completa

Crear:

``` text
exact_match = true/false
```

Debe ser `true` únicamente cuando:

-   el JSON sea válido;
-   el esquema sea correcto;
-   estén los 8 productos correctos;
-   todas las cantidades sean correctas;
-   no haya productos extra;
-   no aparezca el agua.

------------------------------------------------------------------------

## 7. Repeticiones

Una sola ejecución no es suficiente para medir latencia.

Ejecutar varias repeticiones por modelo.

Valor inicial sugerido:

``` text
5 ejecuciones medidas por modelo
```

Debe existir una variable configurable, por ejemplo:

``` python
RUNS_PER_MODEL = 5
```

Antes de las ejecuciones medidas realizar una ejecución de
calentamiento:

``` text
1 warm-up
```

La ejecución de calentamiento NO debe incluirse en los promedios
finales.

Esto permite reducir el efecto de:

-   carga inicial del modelo;
-   cachés;
-   inicialización;
-   diferencias entre primera ejecución y ejecuciones posteriores.

------------------------------------------------------------------------

## 8. Carga y descarga de modelos

Como la máquina tiene solamente 8 GB de RAM, evitar mantener varios
modelos cargados simultáneamente.

El benchmark debe procesarlos secuencialmente:

``` text
Modelo A
↓
warm-up
↓
5 pruebas
↓
guardar resultados
↓
liberar/descargar modelo si corresponde
↓
Modelo B
↓
...
```

No ejecutar inferencias de varios modelos en paralelo.

El objetivo es que la comparación no quede contaminada por competencia
de RAM/CPU entre modelos.

------------------------------------------------------------------------

## 9. Resultados por ejecución

Guardar cada ejecución individual.

Ejemplo conceptual:

``` json
{
  "model": "qwen3:1.7b",
  "run": 1,
  "time_to_first_token_ms": 520,
  "total_latency_ms": 1180,
  "tokens_per_second": 35.2,
  "prompt_tokens": 650,
  "output_tokens": 105,
  "ram_peak_mb": 1700,
  "valid_json": true,
  "schema_valid": true,
  "correct_products": 8,
  "correct_quantities": 8,
  "excluded_water_correctly": true,
  "exact_match": true,
  "raw_response": "..."
}
```

Conservar SIEMPRE `raw_response` para poder inspeccionar posteriormente
qué hizo mal cada modelo.

------------------------------------------------------------------------

## 10. Resumen final por modelo

Calcular para cada modelo:

-   promedio de TTFT;
-   mediana de TTFT;
-   promedio de latencia total;
-   mediana de latencia total;
-   mínimo y máximo de latencia;
-   promedio de tokens/s;
-   RAM pico;
-   porcentaje de JSON válido;
-   porcentaje de schema válido;
-   porcentaje de productos correctos;
-   porcentaje de cantidades correctas;
-   porcentaje de exact match.

La salida en consola debería incluir una tabla similar a:

``` text
Modelo                 Params   TTFT     Total    tok/s   RAM pico   JSON   Exact
----------------------------------------------------------------------------------
llama3.2:1b             ~1B      ...      ...      ...      ...       ...    ...
qwen3:1.7b              ~1.7B    ...      ...      ...      ...       ...    ...
granite3.1-dense:2b     ~2B      ...      ...      ...      ...       ...    ...
qwen3.5:2b              ~2B      ...      ...      ...      ...       ...    ...
qwen2.5:3b-instruct     ~3B      ...      ...      ...      ...       ...    ...
qwen3:4b-instruct       ~4B      ...      ...      ...      ...       ...    ...
```

No asignar automáticamente un "ganador" basándose únicamente en
velocidad.

El propósito es poder observar el trade-off entre tamaño, latencia y
precisión.

------------------------------------------------------------------------

## 11. Archivos de salida

Generar al menos:

``` text
results/
    benchmark_runs.csv
    benchmark_summary.csv
    raw_responses.json
```

### benchmark_runs.csv

Una fila por ejecución.

### benchmark_summary.csv

Una fila por modelo con las métricas agregadas.

### raw_responses.json

Guardar todas las respuestas originales completas y la información
necesaria para saber a qué modelo/ejecución corresponden.

Opcionalmente también generar un archivo:

``` text
benchmark_report.md
```

con una tabla legible de resultados.

------------------------------------------------------------------------

## 12. Gráficos opcionales

Si se implementan gráficos, generar como mínimo:

1.  parámetros/tamaño del modelo vs latencia total;
2.  modelo vs TTFT;
3.  modelo vs tokens por segundo;
4.  modelo vs RAM pico;
5.  modelo vs porcentaje de exact match.

Los gráficos deben generarse a partir de los datos guardados, no de
valores hardcodeados.

------------------------------------------------------------------------

## 13. Requisitos de implementación

Preferentemente implementar el benchmark en Python.

Utilizar la API local de Ollama en vez de automatizar la interfaz de
terminal.

El programa debe:

-   funcionar en Windows;
-   asumir Ollama ejecutándose localmente;
-   usar streaming para medir TTFT;
-   manejar errores de conexión;
-   manejar timeouts;
-   detectar modelos no instalados;
-   continuar con los demás modelos si uno falla;
-   guardar resultados aunque una ejecución falle;
-   no modificar el prompt entre modelos;
-   no ocultar respuestas incorrectas;
-   no "reparar" automáticamente el JSON antes de evaluar `valid_json`;
-   evitar dependencias innecesariamente pesadas;
-   mostrar progreso en consola.

La configuración principal debería estar centralizada para poder cambiar
fácilmente:

``` text
MODELS
RUNS_PER_MODEL
WARMUP_RUNS
TEMPERATURE
CONTEXT_SIZE
TIMEOUT
OUTPUT_DIRECTORY
```

------------------------------------------------------------------------

## 14. Importante sobre el tiempo de carga

Conviene distinguir dos conceptos:

### Cold start

Tiempo necesario cuando el modelo todavía no está cargado.

### Inferencia con modelo cargado

Latencia de una petición cuando el modelo ya está residente.

Para la aplicación final de voz interesa especialmente la segunda,
porque probablemente el modelo elegido permanezca cargado mientras el
sistema está funcionando.

Si es posible, registrar el tiempo de cold start por separado, pero NO
mezclarlo con las cinco ejecuciones utilizadas para calcular la latencia
normal.

------------------------------------------------------------------------

## 15. Criterio del experimento

No se busca demostrar que el modelo con más parámetros es mejor.

La pregunta que queremos responder es:

> ¿Cuál es el modelo local más pequeño y rápido que puede realizar de
> manera confiable nuestra tarea de extracción de inventario?

Por ejemplo, si un modelo 1B responde mucho más rápido pero falla
frecuentemente en productos, cantidades o negaciones, esa reducción de
latencia puede no ser aceptable.

En cambio, si un modelo de 1.7B o 2B consigue prácticamente la misma
exactitud que el modelo 4B con una latencia significativamente menor,
puede ser un candidato más apropiado para el sistema final.

------------------------------------------------------------------------

## 16. Primera fase

Esta primera fase debe utilizar únicamente el prompt literal definido en
este documento.

No generar todavía decenas de prompts diferentes.

Primero queremos una prueba controlada donde todos los modelos resuelvan
exactamente la misma tarea.

Una fase posterior podrá incorporar un dataset de 20, 50 o más órdenes
de inventario con:

-   productos únicos;
-   múltiples productos;
-   cantidades escritas con palabras;
-   abreviaciones;
-   negaciones;
-   correcciones del hablante;
-   productos parecidos;
-   tamaños diferentes;
-   productos que no existen;
-   cantidades faltantes;
-   frases largas provenientes de STT.

Pero esa segunda fase queda fuera del alcance inicial de este benchmark.
