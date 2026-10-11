"""Shared difficulty levels for text prompts and their audio recordings."""

LEVELS = {
    "solo_agregar": "basico",
    "solo_restar": "basico",
    "restar_ambos": "habitual",
    "corregir_cantidad": "habitual",
    "negar_agregacion": "habitual",
    "negar_restacion": "habitual",
    "negar_varias_agregaciones": "exigente",
    "negar_varias_restaciones": "exigente",
    "negar_agregacion_y_restacion": "exigente",
    "caso_integral": "exigente",
}


def prompt_path(directory, case_id):
    return directory / LEVELS[case_id] / f"{case_id}.txt"
