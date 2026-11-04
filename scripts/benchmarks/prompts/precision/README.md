# Prompts por dificultad

El contrato común está en `contract.txt`. Los diez textos del corpus se agrupan
por nivel; sus grabaciones originales y WAV usan el mismo nivel en
`tests/fixtures/speech_to_text/{originals,wav}/`.

- **basico:** solo_agregar, solo_restar. Una acción sin corrección ni cancelación.
- **habitual:** restar_ambos, corregir_cantidad, negar_agregacion, negar_restacion.
  Varios artículos con una misma acción, una corrección o una cancelación simple.
- **exigente:** negar_varias_agregaciones, negar_varias_restaciones,
  negar_agregacion_y_restacion, caso_integral. Cancelación selectiva o combinación
  de acciones, correcciones y referencias.

`solo_agregar` contiene dos artículos, pero se conserva como básico por la
clasificación acordada: no combina acciones, correcciones ni negaciones.
La fuente compartida de clasificación es `scripts/benchmarks/prompt_levels.py`.
