"""Deterministic revisions of the active catalog snapshot."""

from pi.catalog import CATALOG_SNAPSHOT_VERSION, CatalogService, Product
from pi.catalog.snapshot import CatalogSnapshotProduct, build_snapshot


def _product(product_id: str, name: str, **changes: object) -> Product:
    values: dict[str, object] = {
        "product_id": product_id,
        "name": name,
        "category_id": "bebidas",
        "brand": "Marca",
        "presentation": "1 L",
        "aliases": (),
    }
    values.update(changes)
    return Product(**values)  # type: ignore[arg-type]


def test_the_same_content_has_the_same_revision_in_any_order() -> None:
    first = CatalogSnapshotProduct(
        "b", "Gaseosa", "Coca-Cola", "Zero", "2.25 L", ("unit",), ("Coca zero",)
    )
    second = CatalogSnapshotProduct(
        "a", "Agua", "Villa", None, "1.5 L", ("unit",), ("Villa", "agua villa")
    )
    swapped_aliases = CatalogSnapshotProduct(
        "a", "Agua", "Villa", None, "1.5 L", ("unit",), ("agua villa", "Villa")
    )

    forward = build_snapshot((first, second))
    backward = build_snapshot((swapped_aliases, first))

    assert forward.version == CATALOG_SNAPSHOT_VERSION
    assert forward.revision == backward.revision
    assert [product.product_id for product in forward.products] == ["a", "b"]
    assert forward.products[0].aliases == ("agua villa", "Villa")


def test_a_snapshot_excludes_stock_retirement_and_category(
    catalog: CatalogService,
) -> None:
    catalog.add_product(
        _product("agua", "Agua", aliases=("Villa",)),
    )
    catalog.add_product(_product("gaseosa", "Gaseosa", variant="Zero"))
    catalog.retire_product("gaseosa")

    snapshot = catalog.read_snapshot()
    again = catalog.read_snapshot()
    payload = snapshot.as_dict()

    assert snapshot.revision == again.revision
    assert [product.product_id for product in snapshot.products] == ["agua"]
    assert snapshot.products[0].aliases == ("Villa",)
    assert snapshot.products[0].units == ("unit",)
    encoded = str(payload)
    assert "quantity" not in encoded
    assert "retired" not in encoded
    assert "category" not in encoded
    assert "gaseosa" not in encoded


def test_revision_changes_when_the_effective_catalog_changes(
    connection, catalog: CatalogService
) -> None:
    catalog.add_product(_product("agua", "Agua"))
    original = catalog.read_snapshot().revision

    catalog.add_alias("agua", "Agua mineral")
    with_alias = catalog.read_snapshot().revision
    connection.execute(
        "UPDATE catalog_products SET category_id = 'almacen' WHERE product_id = 'agua'"
    )
    after_category = catalog.read_snapshot().revision
    catalog.retire_product("agua")
    after_retirement = catalog.read_snapshot().revision

    assert with_alias != original
    assert after_category == with_alias
    assert after_retirement != with_alias
    assert catalog.read_snapshot().products == ()
