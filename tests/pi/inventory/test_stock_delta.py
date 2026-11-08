"""Tests for changing stock by an atomic delta through ``InventoryService``."""

import sqlite3
import threading
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest

from pi.inventory import (
    IncompatibleUnitError,
    InsufficientStockError,
    InvalidDeltaError,
    InventoryService,
    RetiredProductError,
    StockLevel,
    StockNotInitializedError,
    StockWriter,
    UnknownProductError,
    create_stock_record,
)
from pi.storage import apply_migrations, connect, transaction

COCA = "coca-cola-zero-2l"


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "voicestock.sqlite3"
    connection = connect(path)
    apply_migrations(connection)
    connection.executemany(
        "INSERT INTO catalog_products (product_id, stock_unit) VALUES (?, 'unit')",
        [(COCA,), ("arroz-gallo-1kg",), ("leche-sin-stock",), ("yerba-retirada",)],
    )
    with transaction(connection):
        create_stock_record(connection, COCA, 5)
        create_stock_record(connection, "arroz-gallo-1kg", 2)
        create_stock_record(connection, "yerba-retirada", 0)
        connection.execute(
            "UPDATE catalog_products SET retired = 1 "
            "WHERE product_id = 'yerba-retirada'"
        )
    connection.close()
    return path


@pytest.fixture
def connection(database: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(database)
    yield connection
    connection.close()


@pytest.fixture
def service(connection: sqlite3.Connection) -> InventoryService:
    return InventoryService(connection)


def _quantity(path: Path, product_id: str = COCA) -> int:
    """Read the committed quantity through a brand-new connection."""
    reader = connect(path)
    try:
        (quantity,) = reader.execute(
            "SELECT quantity FROM inventory_stock WHERE product_id = ?",
            (product_id,),
        ).fetchone()
        return quantity
    finally:
        reader.close()


def test_the_service_implements_the_writer_port(service) -> None:
    assert isinstance(service, StockWriter)


def test_a_positive_delta_adds_stock(database, service) -> None:
    assert service.apply_delta(COCA, 3, "unit") == StockLevel(COCA, 8, "unit")
    assert _quantity(database) == 8


def test_a_negative_delta_within_stock_removes_it(database, service) -> None:
    assert service.apply_delta(COCA, -2, "unit") == StockLevel(COCA, 3, "unit")
    assert _quantity(database) == 3


def test_a_delta_can_leave_the_stock_at_zero(database, service) -> None:
    assert service.apply_delta(COCA, -5, "unit").quantity == 0
    assert _quantity(database) == 0


def test_a_delta_that_would_go_negative_is_rejected(database, service) -> None:
    with pytest.raises(InsufficientStockError) as raised:
        service.apply_delta(COCA, -6, "unit")

    assert (raised.value.available, raised.value.delta) == (5, -6)
    assert _quantity(database) == 5


def test_an_unknown_product_changes_nothing(database, connection, service) -> None:
    before = connection.execute("SELECT * FROM inventory_stock").fetchall()

    with pytest.raises(UnknownProductError):
        service.apply_delta("fernet-750ml", 1, "unit")

    assert connection.execute("SELECT * FROM inventory_stock").fetchall() == before


def test_a_product_without_a_record_gets_no_record(connection, service) -> None:
    with pytest.raises(StockNotInitializedError):
        service.apply_delta("leche-sin-stock", 1, "unit")

    assert (
        connection.execute(
            "SELECT * FROM inventory_stock WHERE product_id = 'leche-sin-stock'"
        ).fetchall()
        == []
    )


def test_a_retired_product_is_not_changed(database, service) -> None:
    with pytest.raises(RetiredProductError):
        service.apply_delta("yerba-retirada", 1, "unit")

    assert _quantity(database, "yerba-retirada") == 0


@pytest.mark.parametrize("unit", ["kg", "UNIT", "units", None])
def test_a_different_unit_is_rejected_without_conversion(
    database, service, unit
) -> None:
    with pytest.raises(IncompatibleUnitError):
        service.apply_delta(COCA, 1, unit)

    assert _quantity(database) == 5


@pytest.mark.parametrize("delta", [0, 1.0, 0.5, Decimal("1"), "1", True, None])
def test_inexact_or_zero_deltas_are_rejected(database, service, delta) -> None:
    with pytest.raises(InvalidDeltaError):
        service.apply_delta(COCA, delta, "unit")

    assert _quantity(database) == 5


def test_a_change_of_its_own_is_committed_before_returning(
    database, connection, service
) -> None:
    service.apply_delta(COCA, 1, "unit")

    assert connection.in_transaction is False
    assert _quantity(database) == 6


def test_a_change_survives_reopening_the_database(database, connection) -> None:
    InventoryService(connection).apply_delta(COCA, 4, "unit")
    connection.close()

    reopened = connect(database)
    try:
        assert InventoryService(reopened).get_stock(COCA).level.quantity == 9
    finally:
        reopened.close()


def test_a_change_joins_the_caller_unit_of_work(database, connection, service):
    with transaction(connection):
        service.apply_delta(COCA, -1, "unit")
        service.apply_delta("arroz-gallo-1kg", 1, "unit")

        assert connection.in_transaction is True
        assert _quantity(database) == 5

    assert _quantity(database) == 4
    assert _quantity(database, "arroz-gallo-1kg") == 3


def test_a_caller_failure_before_commit_keeps_the_previous_stock(
    database, connection, service
) -> None:
    with pytest.raises(RuntimeError), transaction(connection):
        service.apply_delta(COCA, -1, "unit")
        connection.execute("CREATE TABLE history_written_with_stock (x INTEGER)")
        raise RuntimeError("history could not be recorded")

    assert _quantity(database) == 5
    assert "history_written_with_stock" not in {
        name for (name,) in connection.execute("SELECT name FROM sqlite_master")
    }


def test_a_rejection_inside_the_caller_unit_of_work_leaves_it_to_the_caller(
    database, connection, service
) -> None:
    with transaction(connection):
        service.apply_delta("arroz-gallo-1kg", 1, "unit")
        with pytest.raises(InsufficientStockError):
            service.apply_delta(COCA, -50, "unit")

        assert connection.in_transaction is True

    assert _quantity(database) == 5
    assert _quantity(database, "arroz-gallo-1kg") == 3


def test_a_delta_changes_only_one_stock_row(connection, service) -> None:
    before = connection.total_changes

    service.apply_delta(COCA, 1, "unit")

    assert connection.total_changes - before == 1
    assert connection.execute("SELECT count(*) FROM inventory_stock").fetchone() == (3,)


def _run_concurrently(
    database: Path, deltas: list[int]
) -> tuple[list[StockLevel], list[Exception]]:
    """Apply each delta from its own thread and connection at the same time."""
    barrier = threading.Barrier(len(deltas))
    levels: list[StockLevel] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker(delta: int) -> None:
        connection = connect(database)
        try:
            barrier.wait()
            level = InventoryService(connection).apply_delta(COCA, delta, "unit")
            with lock:
                levels.append(level)
        except Exception as error:  # collected for the assertions below
            with lock:
                errors.append(error)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker, args=(d,)) for d in deltas]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return levels, errors


def test_concurrent_deltas_are_never_lost(database) -> None:
    # The removals add up to 4, so no ordering can run out of stock.
    levels, errors = _run_concurrently(database, [1, 2, -1, 3, -2, 1, 1, -1])

    assert errors == []
    assert len(levels) == 8
    assert _quantity(database) == 5 + 4


def test_only_one_of_two_racing_removals_can_fit(database) -> None:
    levels, errors = _run_concurrently(database, [-3, -3])

    assert [level.quantity for level in levels] == [2]
    assert len(errors) == 1
    assert isinstance(errors[0], InsufficientStockError)
    assert _quantity(database) == 2


def test_racing_removals_never_go_below_zero(database) -> None:
    levels, errors = _run_concurrently(database, [-1] * 8)

    assert len(levels) == 5
    assert all(isinstance(error, InsufficientStockError) for error in errors)
    assert len(errors) == 3
    assert _quantity(database) == 0


def test_a_caller_holding_the_write_lock_serializes_other_writers(
    database, connection, service
) -> None:
    available: list[int] = []

    def other_writer() -> None:
        other = connect(database)
        try:
            InventoryService(other).apply_delta(COCA, -5, "unit")
        except InsufficientStockError as error:
            available.append(error.available)
        finally:
            other.close()

    with transaction(connection):
        service.apply_delta(COCA, -3, "unit")
        thread = threading.Thread(target=other_writer)
        thread.start()
        thread.join(timeout=0.2)
        assert thread.is_alive()

    thread.join()
    # The other writer waited for the commit and saw 2, not the original 5.
    assert available == [2]
    assert _quantity(database) == 2
