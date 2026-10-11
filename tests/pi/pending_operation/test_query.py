"""Query port: a snapshot of the current pending operation, or none."""

from dataclasses import dataclass, fields

from fakes import MemorySlot, coca_cola_view

from pi.pending_operation import (
    PendingOperationGateway,
    PendingOperationQueryPort,
    PendingOperationView,
    ProvisionalOperationExecutor,
)


def test_get_current_returns_the_pending_snapshot() -> None:
    view = coca_cola_view()
    gateway = PendingOperationGateway(MemorySlot(view), ProvisionalOperationExecutor())

    current = gateway.get_current()

    assert current == view
    assert isinstance(gateway, PendingOperationQueryPort)


def test_get_current_returns_none_when_nothing_is_pending() -> None:
    gateway = PendingOperationGateway(MemorySlot(None), ProvisionalOperationExecutor())

    assert gateway.get_current() is None


def test_get_current_exposes_only_the_view_fields() -> None:
    expected = {
        "operation_id",
        "recognized_text",
        "product",
        "operation",
        "quantity",
        "unit",
        "confirmation_message",
    }
    assert {field.name for field in fields(PendingOperationView)} == expected

    @dataclass(frozen=True)
    class LeakyView(PendingOperationView):
        secret: str = "inventory-row"

    leaked = LeakyView(
        operation_id="op-aaa",
        recognized_text="agregar diez unidades de coca cola",
        product="Coca-Cola",
        operation="agregar",
        quantity=10,
        unit="unidad",
        confirmation_message="Agregar 10 unidades de Coca-Cola",
        secret="inventory-row",
    )
    gateway = PendingOperationGateway(
        MemorySlot(leaked),
        ProvisionalOperationExecutor(),
    )

    current = gateway.get_current()

    assert type(current) is PendingOperationView
    assert current is not None
    assert not hasattr(current, "secret")
    assert current.confirmation_message == "Agregar 10 unidades de Coca-Cola"
