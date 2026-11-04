"""Tests for the location, connections and transactions of the Pi database."""

import sqlite3
from pathlib import Path

import pytest

from pi.storage import (
    DATABASE_ENV_VAR,
    VolatileDatabasePathError,
    connect,
    default_database_path,
    ensure_persistent_path,
    transaction,
)


def test_default_path_prefers_the_environment_variable() -> None:
    environ = {DATABASE_ENV_VAR: "/srv/voicestock/stock.sqlite3"}

    assert default_database_path(environ) == Path("/srv/voicestock/stock.sqlite3")


def test_default_path_uses_the_xdg_data_directory() -> None:
    environ = {"XDG_DATA_HOME": "/home/pi/.data"}

    assert default_database_path(environ) == Path(
        "/home/pi/.data/voicestock/voicestock.sqlite3"
    )


def test_default_path_falls_back_to_the_home_data_directory() -> None:
    expected = Path.home() / ".local/share/voicestock/voicestock.sqlite3"

    assert default_database_path({}) == expected


def test_default_path_is_persistent() -> None:
    assert ensure_persistent_path(default_database_path({})).is_absolute()


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/voicestock.sqlite3",
        "/var/tmp/voicestock/voicestock.sqlite3",
        "/dev/shm/voicestock.sqlite3",
        "/run/user/1000/voicestock.sqlite3",
        "/tmp",
        "",
        ":memory:",
    ],
)
def test_volatile_paths_are_rejected(path: str) -> None:
    with pytest.raises(VolatileDatabasePathError):
        ensure_persistent_path(path)


def test_paths_that_resolve_into_a_volatile_root_are_rejected(
    tmp_path: Path,
) -> None:
    volatile = tmp_path / "volatile"
    volatile.mkdir()
    link = tmp_path / "data"
    link.symlink_to(volatile)

    with pytest.raises(VolatileDatabasePathError):
        ensure_persistent_path(link / "voicestock.sqlite3", (volatile,))


def test_persistent_paths_are_returned_absolute(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"

    assert ensure_persistent_path(path, volatile_roots=()) == path.resolve()


def test_connect_creates_the_directory_and_enforces_foreign_keys(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "voicestock.sqlite3"

    connection = connect(path)
    try:
        assert path.exists()
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        assert connection.in_transaction is False
    finally:
        connection.close()


def test_transaction_commits_for_other_connections(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    writer = connect(path)
    writer.execute("CREATE TABLE item (value INTEGER)")

    with transaction(writer):
        writer.execute("INSERT INTO item VALUES (1)")
    writer.close()

    reader = connect(path)
    try:
        assert reader.execute("SELECT value FROM item").fetchall() == [(1,)]
    finally:
        reader.close()


def test_transaction_rolls_back_when_the_block_fails(tmp_path: Path) -> None:
    connection = connect(tmp_path / "voicestock.sqlite3")
    connection.execute("CREATE TABLE item (value INTEGER)")

    with pytest.raises(RuntimeError), transaction(connection):
        connection.execute("INSERT INTO item VALUES (1)")
        raise RuntimeError("fails before the commit")

    try:
        assert connection.execute("SELECT value FROM item").fetchall() == []
        assert connection.in_transaction is False
    finally:
        connection.close()


def test_transaction_holds_the_write_lock(tmp_path: Path) -> None:
    path = tmp_path / "voicestock.sqlite3"
    first = connect(path)
    second = sqlite3.connect(path, timeout=0, isolation_level=None)
    try:
        with transaction(first), pytest.raises(sqlite3.OperationalError):
            second.execute("BEGIN IMMEDIATE")
    finally:
        second.close()
        first.close()
