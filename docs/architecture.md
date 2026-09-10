# Arquitectura

Este documento reunirá las decisiones de arquitectura de VoiceStock a medida que el proyecto avance.

Todavía no hay decisiones definitivas. El diseño se documentará aquí cuando cada parte del sistema se implemente o se acuerde.

## Alcance previsto

VoiceStock es un sistema de gestión de inventario asistido por voz, centrado en una Raspberry Pi.

A alto nivel, el sistema está pensado para incluir:

- Raspberry Pi como controlador central
- captura de audio
- Speech-to-Text
- integración con un modelo de lenguaje a través de una interfaz independiente del proveedor
- validación de respuestas estructuradas
- persistencia en SQLite
- interfaz web

La elección de ejecutar el modelo de lenguaje en la nube o de forma local todavía está pendiente y se registrará aquí cuando se tome.
