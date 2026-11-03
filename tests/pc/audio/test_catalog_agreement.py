"""The PC catalog gate and the Raspberry validator read one JSON file."""

import json
from pathlib import Path

from pc.audio.catalog import (
    ProductMatch,
    load_catalog_entries,
    match_description,
    prompt_rows,
)
from pi.operation_contract import (
    InMemoryProductResolver,
    OperationValidator,
    load_catalog,
)
from pi.operation_contract.rejection import RejectionReason, ValidationRejection
from pi.operation_contract.validator import ValidatedOperation
from shared.operation_contract import ProductDescription

CATALOG = [
    {
        "product_id": "arroz-marolio-1kg",
        "name": "Arroz",
        "brand": "Marolio",
        "variant": None,
        "presentation": "1 kg",
        "units": ["unit"],
    },
    {
        "product_id": "arroz-marolio-500g",
        "name": "Arroz",
        "brand": "Marolio",
        "variant": None,
        "presentation": "500 g",
        "units": ["unit"],
    },
]


def _write_catalog(path: Path) -> None:
    path.write_text(json.dumps(CATALOG), encoding="utf-8")


def _payload(
    name: str,
    brand: str | None,
    presentation: str | None,
) -> dict[str, object]:
    return {
        "contract_version": "1",
        "operations": [
            {
                "operation": "add_stock",
                "product": {
                    "name": name,
                    "brand": brand,
                    "variant": None,
                    "presentation": presentation,
                },
                "quantity": 2,
                "unit": "unit",
            }
        ],
    }


def test_both_loaders_read_the_same_catalog_file(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    _write_catalog(path)
    entries = load_catalog_entries(path)
    products = load_catalog(path)
    assert [entry.name for entry in entries] == [product.name for product in products]
    assert [entry.presentation for entry in entries] == [
        product.presentation for product in products
    ]
    rendered = json.dumps(prompt_rows(entries))
    assert "product_id" not in rendered
    assert "arroz-marolio-1kg" not in rendered


def test_pc_and_raspberry_agree_on_catalog_matches(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    _write_catalog(path)
    entries = load_catalog_entries(path)
    validator = OperationValidator(InMemoryProductResolver(load_catalog(path)))
    cases = (
        ("Arroz", "Marolio", "1 kg", ProductMatch.IDENTIFIED, "arroz-marolio-1kg"),
        ("arroz", "MAROLIO", "1 KG", ProductMatch.IDENTIFIED, "arroz-marolio-1kg"),
        ("Arroz", "Marolio", None, ProductMatch.AMBIGUOUS, None),
        ("Fideos", None, None, ProductMatch.UNKNOWN, None),
        ("Arroz", "Marolio", "1kg", ProductMatch.UNKNOWN, None),
        ("   ", "Marolio", "1 kg", ProductMatch.INSUFFICIENT, None),
    )
    reasons = {
        ProductMatch.AMBIGUOUS: RejectionReason.AMBIGUOUS_PRODUCT,
        ProductMatch.UNKNOWN: RejectionReason.UNKNOWN_PRODUCT,
        ProductMatch.INSUFFICIENT: RejectionReason.INSUFFICIENT_PRODUCT_ATTRIBUTES,
    }
    for name, brand, presentation, expected, product_id in cases:
        pc_match = match_description(
            ProductDescription(
                name=name,
                brand=brand,
                presentation=presentation,
            ),
            entries,
        )
        pi_result = validator.validate(_payload(name, brand, presentation))
        assert pc_match is expected
        if expected is ProductMatch.IDENTIFIED:
            assert isinstance(pi_result, ValidatedOperation)
            assert pi_result.product_id == product_id
            continue
        assert isinstance(pi_result, ValidationRejection)
        assert pi_result.reason is reasons[expected]
