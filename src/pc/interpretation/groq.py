"""Groq chat provider that returns an interpretation draft.

The HTTP call is injected. This module does not import a transport library,
so the interpretation package stays independent of the network stack. The
draft uses the internal vocabulary. Product attributes stay separate. This
provider does not build a ``ContractPayload`` and does not assign
``product_id``.
"""

import json
from collections.abc import Callable
from typing import Any

DEFAULT_LLM_MODEL = "openai/gpt-oss-20b"
ChatPoster = Callable[[dict[str, Any]], dict[str, Any]]

_DRAFT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "operaciones": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "operacion": {
                        "type": "string",
                        "enum": ["agregar_stock", "restar_stock"],
                    },
                    "producto": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "nombre": {"type": "string"},
                            "marca": {"type": ["string", "null"]},
                            "variante": {"type": ["string", "null"]},
                            "presentacion": {"type": ["string", "null"]},
                        },
                        "required": ["nombre", "marca", "variante", "presentacion"],
                    },
                    "cantidad": {"type": "integer", "minimum": 1},
                },
                "required": ["operacion", "producto", "cantidad"],
            },
        }
    },
    "required": ["operaciones"],
}


class GroqDraftProvider:
    """Ask an injected chat endpoint for one interpretation draft."""

    def __init__(
        self,
        *,
        poster: ChatPoster,
        catalog: list[dict[str, str | None]],
        model: str = DEFAULT_LLM_MODEL,
    ) -> None:
        if not model.strip():
            raise ValueError("LLM model must not be blank")
        if not catalog:
            raise ValueError("interpretation catalog must not be empty")
        self._poster = poster
        self._model = model
        self._instructions = _instructions(catalog)

    def interpret(self, text: str) -> dict[str, Any]:
        """Return the decoded draft. The poster reports its own failures."""
        body = self._poster(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": self._instructions},
                    {"role": "user", "content": text},
                ],
                "temperature": 0,
                "reasoning_effort": "low",
                "max_completion_tokens": 2000,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "operaciones_inventario",
                        "strict": True,
                        "schema": _DRAFT_SCHEMA,
                    },
                },
            }
        )
        return _draft_from_body(body)


def _instructions(catalog: list[dict[str, str | None]]) -> str:
    catalog_json = json.dumps(catalog, ensure_ascii=False)
    return (
        "Convertí un pedido de inventario dicho en español a JSON. "
        "Las únicas operaciones son agregar_stock y restar_stock. "
        "Devolvé cada operación que el pedido pide. No descartes operaciones "
        "de más ni completes una que no fue dicha. "
        "La cantidad es el entero dicho. No la inventes. "
        "El producto se describe solo con atributos del catálogo. "
        "Copiá nombre, marca, variante y presentacion tal como figuran. "
        "Si un atributo no fue dicho, usá null. "
        "No elijas una presentación cuando el pedido coincide con más de un "
        "producto. No inventes product_id ni productos fuera del catálogo. "
        f"Catálogo: {catalog_json}"
    )


def _draft_from_body(body: dict[str, Any]) -> dict[str, Any]:
    from pc.interpretation.providers import ProviderError

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ProviderError("interpretation response has no content") from error
    if not isinstance(content, str):
        raise ProviderError("interpretation content is not text")
    try:
        draft = json.loads(content)
    except ValueError as error:
        raise ProviderError("interpretation content is not JSON") from error
    if not isinstance(draft, dict):
        raise ProviderError("interpretation draft is not an object")
    return draft
