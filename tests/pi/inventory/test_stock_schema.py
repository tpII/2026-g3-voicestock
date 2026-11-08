"""Tests for the stock schema and its link to the catalog."""

import sqlite3
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path

import pytest

from pi.inventory import (
    InvalidQuantityError,
    RetiredProductError,
    StockRecordExistsError,
    UnknownProductError,
    create_stock_record,
    find_active_products_without_stock,
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
        [("coca-cola-zero-2l", 0), ("arroz-gallo-1kg", 0), ("yerba-retirada", 1)],
    )
    connection.close()
    return path


@pytest.fixture
def connection(database: Path) -> Iterator[sqlite3.Connection]:
    connection = connect(database)
    yield connection
    connection.close()


def _stock(connection: sqlite3.Connection) -> list[tuple]:
    return connection.execute(
        "SELECT product_id, quantity, unit FROM inventory_stock ORDER BY product_id"
    ).fetchall()


def test_records_are_stored_in_the_product_stock_unit(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 12)

    assert _stock(connection) == [("coca-cola-zero-2l", 12, "unit")]


def test_zero_is_a_valid_initial_quantity(connection) -> None:
    create_stock_record(connection, "arroz-gallo-1kg", 0)

    assert _stock(connection) == [("arroz-gallo-1kg", 0, "unit")]


def test_a_missing_record_is_not_reported_as_zero(connection) -> None:
    create_stock_record(connection, "arroz-gallo-1kg", 0)

    assert find_active_products_without_stock(connection) == ("coca-cola-zero-2l",)


def test_every_active_product_can_get_its_record(connection) -> None:
    with transaction(connection):
        for product_id in find_active_products_without_stock(connection):
            create_stock_record(connection, product_id, 5)

    assert find_active_products_without_stock(connection) == ()
    assert [row[0] for row in _stock(connection)] == [
        "arroz-gallo-1kg",
        "coca-cola-zero-2l",
    ]


def test_records_survive_a_new_connection(database: Path, connection) -> None:
    with transaction(connection):
        create_stock_record(connection, "coca-cola-zero-2l", 7)
    connection.close()

    reopened = connect(database)
    try:
        assert _stock(reopened) == [("coca-cola-zero-2l", 7, "unit")]
    finally:
        reopened.close()


def test_creation_joins_the_caller_unit_of_work(connection) -> None:
    with pytest.raises(RuntimeError), transaction(connection):
        create_stock_record(connection, "coca-cola-zero-2l", 7)
        raise RuntimeError("the caller fails before committing")

    assert _stock(connection) == []


def test_a_product_cannot_have_two_records(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 7)

    with pytest.raises(StockRecordExistsError):
        create_stock_record(connection, "coca-cola-zero-2l", 3)

    assert _stock(connection) == [("coca-cola-zero-2l", 7, "unit")]


def test_unknown_products_get_no_record(connection) -> None:
    with pytest.raises(UnknownProductError):
        create_stock_record(connection, "fernet-750ml", 1)

    assert _stock(connection) == []


def test_retired_products_get_no_new_record(connection) -> None:
    with pytest.raises(RetiredProductError):
        create_stock_record(connection, "yerba-retirada", 1)

    assert find_active_products_without_stock(connection) == (
        "arroz-gallo-1kg",
        "coca-cola-zero-2l",
    )


@pytest.mark.parametrize("quantity", [-1, 1.5, 2.0, Decimal("2"), "2", True, None])
def test_inexact_or_negative_quantities_are_rejected(connection, quantity) -> None:
    with pytest.raises(InvalidQuantityError):
        create_stock_record(connection, "coca-cola-zero-2l", quantity)

    assert _stock(connection) == []


# The constraints below hold for any writer, not only for create_stock_record.


@pytest.mark.parametrize("quantity", [-1, 1.5, "doce", None, b"\x01"])
def test_the_schema_rejects_inexact_or_negative_quantities(
    connection, quantity
) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO inventory_stock VALUES ('coca-cola-zero-2l', ?, 'unit')",
            (quantity,),
        )


def test_the_schema_rejects_stock_of_a_missing_product(connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO inventory_stock VALUES ('fernet-750ml', 1, 'unit')"
        )


def test_the_schema_rejects_an_incompatible_unit(connection) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO inventory_stock VALUES ('coca-cola-zero-2l', 1, 'kg')"
        )


def test_the_schema_rejects_a_duplicated_record(connection) -> None:
    connection.execute(
        "INSERT INTO inventory_stock VALUES ('arroz-gallo-1kg', 1, 'unit')"
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO inventory_stock VALUES ('arroz-gallo-1kg', 2, 'unit')"
        )


def test_the_schema_rejects_a_record_for_a_retired_product(connection) -> None:
    with pytest.raises(sqlite3.IntegrityError, match="retired"):
        connection.execute(
            "INSERT INTO inventory_stock VALUES ('yerba-retirada', 1, 'unit')"
        )


def test_a_record_is_kept_when_its_product_is_retired(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 4)

    connection.execute(
        "UPDATE catalog_products SET retired = 1 WHERE product_id = 'coca-cola-zero-2l'"
    )

    assert _stock(connection) == [("coca-cola-zero-2l", 4, "unit")]
    assert find_active_products_without_stock(connection) == ("arroz-gallo-1kg",)


def test_a_product_with_stock_cannot_be_deleted(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 4)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "DELETE FROM catalog_products WHERE product_id = 'coca-cola-zero-2l'"
        )


def test_the_stock_unit_of_a_product_with_stock_cannot_change(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 4)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "UPDATE catalog_products SET stock_unit = 'pack' "
            "WHERE product_id = 'coca-cola-zero-2l'"
        )


def test_stock_records_are_never_deleted(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 4)

    with pytest.raises(sqlite3.IntegrityError, match="never deleted"):
        connection.execute("DELETE FROM inventory_stock")


@pytest.mark.parametrize(
    "assignment", ["product_id = 'arroz-gallo-1kg'", "unit = 'kg'"]
)
def test_a_record_cannot_move_to_another_product_or_unit(
    connection, assignment
) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 4)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f"UPDATE inventory_stock SET {assignment}")


def test_the_quantity_can_be_updated_within_the_constraints(connection) -> None:
    create_stock_record(connection, "coca-cola-zero-2l", 4)

    connection.execute("UPDATE inventory_stock SET quantity = 9")

    assert _stock(connection) == [("coca-cola-zero-2l", 9, "unit")]


def test_the_schema_holds_no_movements_or_pending_operations(connection) -> None:
    columns = {
        column
        for table in ("catalog_products", "inventory_stock")
        for (_, column, *_rest) in connection.execute(f"PRAGMA table_info({table})")
    }

    assert columns == {
        "product_id",
        "stock_unit",
        "retired",
        "name",
        "brand",
        "variant",
        "presentation",
        "category_id",
        "name_key",
        "brand_key",
        "variant_key",
        "presentation_key",
        "quantity",
        "unit",
    }
