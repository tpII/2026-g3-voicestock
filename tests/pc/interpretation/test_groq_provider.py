"""Groq draft provider tests. No live API call is made."""

import json

import pytest

from pc.interpretation.groq import GroqDraftProvider
from pc.interpretation.providers import ProviderError

CATALOG = [
    {
        "nombre": "Arroz",
        "marca": "Marolio",
        "variante": None,
        "presentacion": "1 kg",
    }
]


def test_provider_returns_the_decoded_draft() -> None:
    draft = {
        "operaciones": [
            {
                "operacion": "agregar_stock",
                "producto": {
                    "nombre": "Arroz",
                    "marca": "Marolio",
                    "variante": None,
                    "presentacion": "1 kg",
                },
                "cantidad": 2,
            }
        ]
    }
    seen: dict[str, object] = {}

    def poster(payload: dict[str, object]) -> dict[str, object]:
        seen.update(payload)
        return {"choices": [{"message": {"content": json.dumps(draft)}}]}

    provider = GroqDraftProvider(poster=poster, catalog=CATALOG)
    assert provider.interpret("agregá dos de arroz marolio de un kilo") == draft
    assert seen["model"] == "openai/gpt-oss-20b"
    messages = seen["messages"]
    assert isinstance(messages, list)
    assert '"product_id"' not in messages[0]["content"]


def test_malformed_content_is_a_provider_error() -> None:
    def poster(payload: dict[str, object]) -> dict[str, object]:
        return {"choices": [{"message": {"content": "not-json"}}]}

    provider = GroqDraftProvider(poster=poster, catalog=CATALOG)
    with pytest.raises(ProviderError, match="not JSON"):
        provider.interpret("agregá arroz")
