"""The integrated runtime uses one SQLite catalog on the calling thread."""

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from tests.pi.test_runtime import (
    FakeButton,
    FakeClient,
    OneTake,
    _envelope,
)

from pi.catalog import CatalogService, Category, Product
from pi.catalog.access import (
    CatalogNotInitializedError,
    OpeningProductResolver,
    OpeningSnapshotReader,
    require_initialized_catalog,
)
from pi.catalog.resolver import SqliteProductResolver
from pi.inventory.stock import create_stock_record
from pi.operation_contract import OperationValidator, ProductQuery, ResolutionStatus
from pi.runtime import build_runtime, main
from pi.storage import apply_migrations, connect, open_database
from pi.web.app import create_app
from pi.web.settings import WebServerSettings


def _database(tmp_path: Path) -> Path:
    path = tmp_path / "voicestock.sqlite3"
    connection = connect(path)
    apply_migrations(connection)
    catalog = CatalogService(connection)
    catalog.add_category(Category("bebidas", "Bebidas"))
    catalog.add_product(
        Product(
            product_id="coca-zero",
            name="Coca Cola Zero 2L",
            category_id="bebidas",
            aliases=("Coca Zero",),
        )
    )
    catalog.add_product(
        Product(
            product_id="retired-soda",
            name="Gaseosa retirada",
            category_id="bebidas",
        )
    )
    catalog.retire_product("retired-soda")
    connection.close()
    return path


def test_the_integrated_command_does_not_accept_a_json_catalog(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(
            [
                "--pin",
                "17",
                "--bounce-time",
                "0.05",
                "--input-device",
                "mic",
                "--output-directory",
                str(tmp_path),
                "--catalog",
                "catalog.json",
            ]
        )

    assert exit_info.value.code == 2


def test_an_empty_catalog_stops_startup(tmp_path: Path, monkeypatch, capsys) -> None:
    path = tmp_path / "voicestock.sqlite3"
    monkeypatch.setenv("VOICESTOCK_DATABASE", str(path))
    monkeypatch.setattr(
        "pi.catalog.access.open_database",
        lambda target, volatile_roots=(): open_database(target, ()),
    )

    code = main(
        [
            "--pin",
            "17",
            "--bounce-time",
            "0.05",
            "--input-device",
            "mic",
            "--output-directory",
            str(tmp_path / "recordings"),
        ]
    )

    assert code == 1
    assert "voicestock-pi-database init" in capsys.readouterr().err


def test_an_initialized_catalog_is_what_startup_wires(
    tmp_path: Path, monkeypatch
) -> None:
    path = _database(tmp_path)
    monkeypatch.setenv("VOICESTOCK_DATABASE", str(path))
    monkeypatch.setattr(
        "pi.catalog.access.open_database",
        lambda target, volatile_roots=(): open_database(target, ()),
    )
    captured: dict[str, object] = {}

    class _Client:
        def __init__(self, settings: object) -> None:
            del settings

        def close(self) -> None:
            return None

    def capture_runtime(**kwargs: object) -> object:
        captured.update(kwargs)
        raise KeyboardInterrupt

    monkeypatch.setattr("pi.runtime.HttpInterpretationClient", _Client)
    monkeypatch.setattr("pi.runtime.build_runtime", capture_runtime)

    assert (
        main(
            [
                "--pin",
                "17",
                "--bounce-time",
                "0.05",
                "--input-device",
                "mic",
                "--output-directory",
                str(tmp_path / "recordings"),
            ]
        )
        == 0
    )
    validator = captured["validator"]
    assert isinstance(validator, OperationValidator)
    assert isinstance(validator._resolver, OpeningProductResolver)
    assert isinstance(captured["catalog_port"], OpeningSnapshotReader)


def test_startup_check_closes_its_connection(tmp_path: Path, monkeypatch) -> None:
    path = _database(tmp_path)
    held: list[sqlite3.Connection] = []
    real = open_database

    def remember(
        target: Path, volatile_roots: tuple[Path, ...] = ()
    ) -> sqlite3.Connection:
        del volatile_roots
        connection = real(target, ())
        held.append(connection)
        return connection

    monkeypatch.setattr("pi.catalog.access.open_database", remember)
    assert require_initialized_catalog(path, volatile_roots=()) == path
    with pytest.raises(sqlite3.ProgrammingError):
        held[0].execute("SELECT 1")


def test_a_database_without_products_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    connection = open_database(path, ())
    connection.close()

    with pytest.raises(CatalogNotInitializedError):
        require_initialized_catalog(path, volatile_roots=())


def test_resolution_and_the_snapshot_share_the_database(tmp_path: Path) -> None:
    path = _database(tmp_path)
    resolved = OpeningProductResolver(path).resolve(ProductQuery("Coca Cola Zero 2L"))
    retired = OpeningProductResolver(path).resolve(ProductQuery("Gaseosa retirada"))
    snapshot = OpeningSnapshotReader(path).read_snapshot()

    assert resolved.status is ResolutionStatus.IDENTIFIED
    assert resolved.product is not None
    assert resolved.product.product_id == "coca-zero"
    assert retired.status is ResolutionStatus.UNKNOWN
    assert [product.product_id for product in snapshot.products] == ["coca-zero"]
    assert snapshot.products[0].aliases == ("Coca Zero",)
    assert "quantity" not in snapshot.as_dict()["products"][0]


def test_resolution_runs_on_the_worker_and_closes_every_connection(
    tmp_path: Path, monkeypatch
) -> None:
    path = _database(tmp_path)
    opened: list[sqlite3.Connection] = []
    real_connect = connect

    def track(target: Path) -> sqlite3.Connection:
        connection = real_connect(target)
        opened.append(connection)
        return connection

    monkeypatch.setattr("pi.catalog.access.connect", track)

    def resolve() -> tuple[int, ResolutionStatus]:
        status = (
            OpeningProductResolver(path)
            .resolve(ProductQuery("Coca Cola Zero 2L"))
            .status
        )
        return threading.get_ident(), status

    with ThreadPoolExecutor(max_workers=1) as pool:
        worker_ident, status = pool.submit(resolve).result()
        worker_ident_again, status_again = pool.submit(resolve).result()

    assert status is ResolutionStatus.IDENTIFIED
    assert status_again is ResolutionStatus.IDENTIFIED
    assert worker_ident != threading.get_ident()
    assert worker_ident_again == worker_ident
    assert len(opened) == 2
    for connection in opened:
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")


def test_a_failed_resolution_closes_the_connection(tmp_path: Path, monkeypatch) -> None:
    path = _database(tmp_path)
    opened: list[sqlite3.Connection] = []
    real_connect = connect

    def track(target: Path) -> sqlite3.Connection:
        connection = real_connect(target)
        opened.append(connection)
        return connection

    monkeypatch.setattr("pi.catalog.access.connect", track)

    def fail(self: SqliteProductResolver, query: ProductQuery) -> None:
        del self, query
        raise RuntimeError("resolution failed")

    monkeypatch.setattr(SqliteProductResolver, "resolve", fail)
    with pytest.raises(RuntimeError, match="resolution failed"):
        OpeningProductResolver(path).resolve(ProductQuery("Coca Cola Zero 2L"))

    with pytest.raises(sqlite3.ProgrammingError):
        opened[0].execute("SELECT 1")


def test_a_failed_snapshot_read_closes_the_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _database(tmp_path)
    opened: list[sqlite3.Connection] = []
    real_connect = connect

    def track(target: Path) -> sqlite3.Connection:
        connection = real_connect(target)
        opened.append(connection)
        return connection

    def fail(self: CatalogService) -> None:
        del self
        raise RuntimeError("snapshot failed")

    monkeypatch.setattr("pi.catalog.access.connect", track)
    monkeypatch.setattr(CatalogService, "read_snapshot", fail)
    with pytest.raises(RuntimeError, match="snapshot failed"):
        OpeningSnapshotReader(path).read_snapshot()

    with pytest.raises(sqlite3.ProgrammingError):
        opened[0].execute("SELECT 1")


def test_stock_does_not_change_the_catalog_revision(tmp_path: Path) -> None:
    path = _database(tmp_path)
    before = OpeningSnapshotReader(path).read_snapshot().revision
    connection = connect(path)
    create_stock_record(connection, "coca-zero", 4)
    connection.execute(
        "UPDATE inventory_stock SET quantity = 9 WHERE product_id = ?",
        ("coca-zero",),
    )
    connection.close()
    after = OpeningSnapshotReader(path).read_snapshot().revision

    assert before == after


def test_the_http_read_opens_its_connection_on_the_server_thread(
    tmp_path: Path,
) -> None:
    path = _database(tmp_path)
    seen: dict[str, int] = {}

    class RecordingReader(OpeningSnapshotReader):
        def read_snapshot(self):  # type: ignore[no-untyped-def]
            seen["thread"] = threading.get_ident()
            return super().read_snapshot()

    def request_catalog() -> None:
        app = create_app(catalog_port=RecordingReader(path))
        with TestClient(app) as client:
            response = client.get("/api/v1/catalog")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["products"][0]["product_id"] == "coca-zero"
        assert "quantity" not in response.text
        assert "movement" not in response.text

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(request_catalog).result()

    direct = OpeningSnapshotReader(path)
    holder: dict[str, int] = {}

    def read_elsewhere() -> None:
        holder["thread"] = threading.get_ident()
        snapshot = direct.read_snapshot()
        assert snapshot.products[0].product_id == "coca-zero"

    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(read_elsewhere).result()

    assert seen["thread"] != threading.get_ident()
    assert holder["thread"] != threading.get_ident()
    assert holder["thread"] != seen["thread"]


def test_the_shared_flow_still_confirms_with_sqlite(tmp_path: Path) -> None:
    path = _database(tmp_path)
    client = FakeClient(_envelope())
    button = FakeButton()
    runtime = build_runtime(
        client=client,  # type: ignore[arg-type]
        validator=OperationValidator(OpeningProductResolver(path)),
        catalog_port=OpeningSnapshotReader(path),
        capture=OneTake(tmp_path / "take.wav"),  # type: ignore[arg-type]
        button_factory=lambda controller: button,
        web_settings=WebServerSettings(host="127.0.0.1", port=8123),
        delete_after_send=True,
    )

    def runner(application, host: str, port: int) -> None:  # type: ignore[no-untyped-def]
        del host, port
        runtime.controller.notify_pressed()
        runtime.controller.notify_released()
        runtime.controller.wait_until_caught_up()
        runtime.flow.wait_until_settled()
        status = application.state.status_port.get_status()
        operation_id = status.pending_operation.operation_id
        assert status.pending_operation.product == "Coca Cola Zero 2L"
        catalog = application.state.catalog_port.read_snapshot()
        assert catalog.products[0].product_id == "coca-zero"
        assert application.state.resolution_port.confirm(operation_id).status.value == (
            "success"
        )

    runtime.serve(runner=runner)
    assert client.calls == 1
    assert button.closed is True
    assert client.closed is True
