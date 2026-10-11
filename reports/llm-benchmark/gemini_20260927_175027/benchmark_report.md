# Análisis del benchmark

## Prompt utilizado

```text
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

## Resumen

- Ejecuciones medidas analizadas: **25**
- Ejecuciones con error HTTP/cliente: **8**
- Los warm-up fueron excluidos.
- `Total medio` es el promedio de `total_latency_ms`: desde que el cliente envía la solicitud hasta que recibe la respuesta completa.
- En Groq incluye red y tiempo de respuesta extremo a extremo; en Ollama corresponde al tiempo observado desde el cliente local.
- La velocidad y la latencia no se interpretan como calidad semántica.

## Comparación por modelo

| Modelo                       | Params | Runs | JSON   | Schema | Exact  | Total medio | Tok/s  | RAM pico MB |
| ---------------------------- | ------ | ---- | ------ | ------ | ------ | ----------- | ------ | ----------- |
| gemini:gemini-3.5-flash      | cloud  | 5    | 100.0% | 100.0% | 100.0% | 6,003 ms    | 217.00 | N/D         |
| gemini:gemini-3.5-flash-lite | cloud  | 5    | 100.0% | 100.0% | 100.0% | 1,235 ms    | 488.87 | N/D         |
| gemini:gemini-3.6-flash      | cloud  | 5    | 100.0% | 100.0% | 100.0% | 4,810 ms    | 172.19 | N/D         |
| gemini:gemini-3.7-flash      | cloud  | 5    | 100.0% | 100.0% | 100.0% | 3,305 ms    | 489.57 | N/D         |
| gemini:gemini-3.8-flash      | cloud  | 5    | 100.0% | 100.0% | 100.0% | 2,339 ms    | 314.65 | N/D         |

## Lectura rápida

- Menor latencia media: **gemini:gemini-3.5-flash-lite** (1,235 ms).
- Mayor exact match: **gemini:gemini-3.5-flash-lite** (100.0%).
- La elección final debe priorizar `exact_match` y luego contrastar latencia, velocidad y RAM.

## Alertas

- Hay ejecuciones con error que deben revisarse en `benchmark_runs.csv`.
