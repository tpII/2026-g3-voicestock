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

- Ejecuciones medidas analizadas: **30**
- Ejecuciones con error HTTP/cliente: **0**
- Los warm-up fueron excluidos.
- La velocidad y la latencia no se interpretan como calidad semántica.

## Comparación por modelo

| Modelo              | Params | Runs | JSON   | Schema | Exact  | Total medio | Tok/s | RAM pico MB |
| ------------------- | ------ | ---- | ------ | ------ | ------ | ----------- | ----- | ----------- |
| granite3.1-dense:2b | ~2B    | 5    | 100.0% | 0.0%   | 0.0%   | 23,209 ms   | 9.05  | 1949        |
| llama3.2:1b         | ~1B    | 5    | 0.0%   | 0.0%   | 0.0%   | 20,608 ms   | 12.67 | 1543        |
| qwen2.5:3b-instruct | ~3B    | 5    | 100.0% | 0.0%   | 0.0%   | 17,705 ms   | 8.80  | 2166        |
| qwen3.5:2b          | ~2B    | 5    | 100.0% | 100.0% | 0.0%   | 28,577 ms   | 8.42  | 2044        |
| qwen3:1.7b          | ~1.7B  | 5    | 100.0% | 100.0% | 0.0%   | 19,520 ms   | 12.61 | 1883        |
| qwen3:4b-instruct   | ~4B    | 5    | 100.0% | 100.0% | 100.0% | 34,231 ms   | 6.33  | 3132        |

## Lectura rápida

- Menor latencia media: **qwen2.5:3b-instruct** (17,705 ms).
- Mayor exact match: **qwen3:4b-instruct** (100.0%).
- La elección final debe priorizar `exact_match` y luego contrastar latencia, velocidad y RAM.

## Alertas

- **granite3.1-dense:2b** no obtuvo ningún `exact_match`.
- **granite3.1-dense:2b** tuvo respuestas con esquema inválido.
- **llama3.2:1b** no obtuvo ningún `exact_match`.
- **llama3.2:1b** tuvo respuestas que no fueron JSON válido.
- **llama3.2:1b** tuvo respuestas con esquema inválido.
- **qwen2.5:3b-instruct** no obtuvo ningún `exact_match`.
- **qwen2.5:3b-instruct** tuvo respuestas con esquema inválido.
- **qwen3.5:2b** no obtuvo ningún `exact_match`.
- **qwen3:1.7b** no obtuvo ningún `exact_match`.
