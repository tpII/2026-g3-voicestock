"""The published JSON Schema stays identical to the canonical model."""

import json
from pathlib import Path

from shared.operation_contract import CONTRACT_VERSION, contract_json_schema

SCHEMA_PATH = (
    Path(__file__).parents[3]
    / "docs"
    / "interfaces"
    / "schemas"
    / f"contract-payload-v{CONTRACT_VERSION}.schema.json"
)


def test_published_schema_matches_the_canonical_model() -> None:
    published = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    # If this fails, regenerate the file from contract_json_schema() as
    # described in docs/interfaces/operation-contract.md.
    assert published == contract_json_schema()
