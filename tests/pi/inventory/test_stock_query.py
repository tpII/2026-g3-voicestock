"""Tests for reading the current stock through ``InventoryService``."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from pi.inventory import (
    InventoryService,
    StockLevel,
    StockLookup,
    StockReader,
    StockStatus,
    create_stock_record,
)
from pi.storage import apply_migrations, connect, transaction


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "voicestock.sqlite3"
    connection = connect(path)
    apply_migrations(connection)
    connection.executemany(
        "INSERT INTO catalog_products (product_id, stock_unit, retired) "
        "VALUES (?, 'unit', ?)",
        [
            ("coca-cola-zero-2l", 0),
            ("arroz-gallo-1kg", 0),
            ("leche-serenisima-1l", 0),
            ("yerba-retirada", 0),
        ],
    )
    with transaction(connection):
        create_stock_record(connection, "coca-cola-zero-2l", 12)
        create_stock_record(connection, "arroz-gallo-1kg", 0)
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


def test_the_service_implements_the_reader_port(service) -> None:
    assert isinstance(service, StockReader)


def test_an_existing_product_returns_its_stored_quantity(service) -> None:
    assert service.get_stock("coca-cola-zero-2l") == StockLookup(
        StockStatus.FOUND, StockLevel("coca-cola-zero-2l", 12, "unit")
    )


def test_zero_stock_is_found_and_not_missing(service) -> None:
    lookup = service.get_stock("arroz-gallo-1kg")

    assert lookup.status is StockStatus.FOUND
    assert lookup.level == StockLevel("arroz-gallo-1kg", 0, "unit")


def test_an_unknown_product_is_reported_explicitly(service) -> None:
    assert service.get_stock("fernet-750ml") == StockLookup(StockStatus.UNKNOWN_PRODUCT)


def test_a_product_without_a_record_is_not_reported_as_zero(service) -> None:
    assert service.get_stock("leche-serenisima-1l") == StockLookup(
        StockStatus.NOT_INITIALIZED
    )


def test_a_retired_product_still_reports_its_kept_stock(service) -> None:
    assert service.get_stock("yerba-retirada") == StockLookup(
        StockStatus.FOUND, StockLevel("yerba-retirada", 0, "unit", retired=True)
    )


def test_the_listing_matches_the_active_records(service) -> None:
    assert service.list_stock() == (
        StockLevel("arroz-gallo-1kg", 0, "unit"),
        StockLevel("coca-cola-zero-2l", 12, "unit"),
    )


def test_the_listing_can_include_retired_products(service) -> None:
    assert service.list_stock(include_retired=True) == (
        StockLevel("arroz-gallo-1kg", 0, "unit"),
        StockLevel("coca-cola-zero-2l", 12, "unit"),
        StockLevel("yerba-retirada", 0, "unit", retired=True),
    )


def test_reads_return_a_quantity_written_directly(connection, service) -> None:
    connection.execute(
        "UPDATE inventory_stock SET quantity = 40 "
        "WHERE product_id = 'coca-cola-zero-2l'"
    )

    assert service.get_stock("coca-cola-zero-2l").level.quantity == 40


def test_reads_see_what_another_connection_committed(database: Path, service) -> None:
    writer = connect(database)
    try:
        with transaction(writer):
            writer.execute(
                "UPDATE inventory_stock SET quantity = 7 "
                "WHERE product_id = 'coca-cola-zero-2l'"
            )
    finally:
        writer.close()

    assert service.get_stock("coca-cola-zero-2l").level.quantity == 7


def test_reads_do_not_see_what_another_connection_has_not_committed(
    database: Path, service
) -> None:
    writer = connect(database)
    try:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute(
            "UPDATE inventory_stock SET quantity = 99 "
            "WHERE product_id = 'coca-cola-zero-2l'"
        )

        assert service.get_stock("coca-cola-zero-2l").level.quantity == 12
    finally:
        writer.execute("ROLLBACK")
        writer.close()


def test_reads_take_part_in_the_caller_unit_of_work(connection, service) -> None:
    with pytest.raises(RuntimeError), transaction(connection):
        connection.execute(
            "UPDATE inventory_stock SET quantity = 1 "
            "WHERE product_id = 'coca-cola-zero-2l'"
        )
        assert service.get_stock("coca-cola-zero-2l").level.quantity == 1
        raise RuntimeError("the caller rolls back")

    assert service.get_stock("coca-cola-zero-2l").level.quantity == 12


def test_reads_do_not_leave_a_transaction_open(connection, service) -> None:
    service.get_stock("coca-cola-zero-2l")
    service.list_stock()

    assert connection.in_transaction is False
