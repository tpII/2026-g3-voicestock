"""Fixtures for the persistent catalog tests."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from pi.catalog import CatalogService, Category
from pi.storage import apply_migrations, connect


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    opened = connect(tmp_path / "voicestock.sqlite3")
    apply_migrations(opened)
    try:
        yield opened
    finally:
        opened.close()


@pytest.fixture
def catalog(connection: sqlite3.Connection) -> CatalogService:
    service = CatalogService(connection)
    service.add_category(Category("bebidas", "Bebidas"))
    service.add_category(Category("almacen", "Almacén"))
    return service
