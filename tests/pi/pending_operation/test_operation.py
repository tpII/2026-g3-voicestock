"""PendingOperation is created only from a validated operation."""

import ast
from pathlib import Path

import pytest

from pi.operation_contract import (
    RejectionReason,
    ValidatedOperation,
    ValidationRejection,
)
from pi.pending_operation import PendingOperation, PendingOperationView


def _validated(quantity: int = 2, operation: str = "add_stock") -> ValidatedOperation:
    return ValidatedOperation(
        operation=operation,
        product_id="coca-cola-zero-2l",
        product_name="Coca Cola Zero 2L",
        quantity=quantity,
        unit="unit",
    )


def test_pending_operation_keeps_the_validated_operation_and_a_new_id() -> None:
    validated = _validated()

    pending = PendingOperation.from_validated(validated, "sumá dos coca cola zero")

    assert pending.validated_operation is validated
    assert pending.recognized_text == "sumá dos coca cola zero"
    assert pending.operation_id.strip()
    view = pending.to_view()
    assert isinstance(view, PendingOperationView)
    assert view.operation_id == pending.operation_id
    assert view.recognized_text == "sumá dos coca cola zero"
    assert view.product == "Coca Cola Zero 2L"
    assert view.operation == "agregar"
    assert view.quantity == 2
    assert view.unit == "unidad"
    assert view.confirmation_message == "Agregar 2 unidades de Coca Cola Zero 2L"


def test_each_pending_operation_receives_its_own_id() -> None:
    validated = _validated()

    first = PendingOperation.from_validated(validated, "una")
    second = PendingOperation.from_validated(validated, "otra")

    assert first.operation_id != second.operation_id


def test_confirmation_message_uses_the_singular_unit() -> None:
    pending = PendingOperation.from_validated(_validated(quantity=1), "")

    assert pending.to_view().confirmation_message == (
        "Agregar 1 unidad de Coca Cola Zero 2L"
    )
    assert pending.to_view().unit == "unidad"


def test_remove_stock_uses_the_quitar_label() -> None:
    pending = PendingOperation.from_validated(
        _validated(operation="remove_stock"),
        "sacá una",
    )

    view = pending.to_view()
    assert view.operation == "quitar"
    assert view.confirmation_message == "Quitar 2 unidades de Coca Cola Zero 2L"


def test_a_rejection_cannot_become_a_pending_operation() -> None:
    rejection = ValidationRejection(RejectionReason.UNKNOWN_PRODUCT, "missing")

    with pytest.raises(TypeError):
        PendingOperation.from_validated(rejection, "texto")  # type: ignore[arg-type]


def test_blank_operation_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        PendingOperation("  ", "texto", _validated())


def test_operation_model_does_not_import_storage_or_the_pc() -> None:
    text = (
        Path(__file__).parents[3] / "src" / "pi" / "pending_operation" / "operation.py"
    ).read_text(encoding="utf-8")
    modules = {
        alias.name
        for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    modules.update(
        node.module or ""
        for node in ast.walk(ast.parse(text))
        if isinstance(node, ast.ImportFrom)
    )
    assert "sqlite3" not in modules
    assert not any(name == "pc" or name.startswith("pc.") for name in modules)
