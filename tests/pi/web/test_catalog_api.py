"""HTTP read of the active catalog snapshot."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

from pi.catalog import (
    CatalogService,
    CatalogSnapshot,
    CatalogSnapshotProduct,
    Category,
    Product,
)
from pi.storage import apply_migrations, connect
from pi.web.app import create_app

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@asynccontextmanager
async def client_for(catalog_port: object | None) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(catalog_port=catalog_port)  # type: ignore[arg-type]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


async def test_catalog_without_a_port_is_not_ready() -> None:
    async with client_for(None) as client:
        response = await client.get("/api/v1/catalog")

    assert response.status_code == 503
    assert response.json()["code"] == "catalog_not_ready"


class _SnapshotPort:
    def __init__(self, snapshot: CatalogSnapshot) -> None:
        self.snapshot = snapshot

    def read_snapshot(self) -> CatalogSnapshot:
        return self.snapshot


async def test_catalog_returns_the_snapshot_without_stock() -> None:
    snapshot = CatalogSnapshot(
        version=1,
        revision="abc",
        products=(
            CatalogSnapshotProduct(
                product_id="gaseosa-zero",
                name="Gaseosa",
                brand="Coca-Cola",
                variant="Zero",
                presentation="2.25 L",
                units=("unit",),
                aliases=("Coca Zero de dos veinticinco",),
            ),
        ),
    )

    async with client_for(_SnapshotPort(snapshot)) as client:
        response = await client.get("/api/v1/catalog")
    revision = snapshot.revision

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["version"] == 1
    assert body["revision"] == revision
    assert body["products"] == [
        {
            "product_id": "gaseosa-zero",
            "name": "Gaseosa",
            "brand": "Coca-Cola",
            "variant": "Zero",
            "presentation": "2.25 L",
            "units": ["unit"],
            "aliases": ["Coca Zero de dos veinticinco"],
        }
    ]
    assert "quantity" not in response.text
    assert "category" not in response.text


async def test_the_route_can_read_a_sqlite_catalog(tmp_path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    apply_migrations(connection)
    catalog = CatalogService(connection)
    catalog.add_category(Category("bebidas", "Bebidas"))
    catalog.add_product(
        Product(
            product_id="gaseosa-zero",
            name="Gaseosa",
            brand="Coca-Cola",
            variant="Zero",
            presentation="2.25 L",
            category_id="bebidas",
        )
    )

    async with client_for(catalog) as client:
        response = await client.get("/api/v1/catalog")
    connection.close()

    assert response.status_code == 200
    assert response.json()["products"][0]["product_id"] == "gaseosa-zero"
