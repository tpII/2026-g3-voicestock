"""Location, connections and transactions of the Raspberry Pi SQLite database.

VoiceStock keeps one SQLite file on the Raspberry Pi. Only the process that
owns it, ``voicestock-pi``, opens it; remote consumers such as the browser or
the PC reach the data through that process and never open the file. Catalog,
stock and history share the file and a single migration order.

Connections run in autocommit mode. A write that spans several statements, or
several modules, runs inside one ``transaction`` opened by the caller, and the
modules that join it never commit on their own.
"""

import os
import sqlite3
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path

DATABASE_ENV_VAR = "VOICESTOCK_DATABASE"
DATABASE_FILENAME = "voicestock.sqlite3"
BUSY_TIMEOUT_SECONDS = 5.0

# Directories whose contents may disappear on reboot or are meant to be
# disposable. The database must never live under them.
VOLATILE_ROOTS: tuple[Path, ...] = (
    Path("/tmp"),
    Path("/var/tmp"),
    Path("/dev/shm"),
    Path("/run"),
    Path(tempfile.gettempdir()),
)


class VolatileDatabasePathError(ValueError):
    """The database path is in memory or under a temporary directory."""


def default_database_path(environ: Mapping[str, str] = os.environ) -> Path:
    """Return the database path the owner process uses.

    ``VOICESTOCK_DATABASE`` wins when set. Otherwise the file lives in the
    user's data directory: ``$XDG_DATA_HOME/voicestock`` or
    ``~/.local/share/voicestock``.
    """
    if explicit := environ.get(DATABASE_ENV_VAR, "").strip():
        return Path(explicit).expanduser()
    data_home = environ.get("XDG_DATA_HOME", "").strip()
    base = Path(data_home) if data_home else Path.home() / ".local" / "share"
    return base / "voicestock" / DATABASE_FILENAME


def ensure_persistent_path(
    path: Path | str, volatile_roots: tuple[Path, ...] = VOLATILE_ROOTS
) -> Path:
    """Return ``path`` made absolute, or reject a path that would not persist."""
    if str(path).strip() in ("", ":memory:"):
        raise VolatileDatabasePathError("the database must be a file on disk")
    resolved = Path(path).expanduser().resolve()
    for root in volatile_roots:
        root = root.resolve()
        if resolved == root or root in resolved.parents:
            raise VolatileDatabasePathError(
                f"{resolved} is under {root}, which does not persist"
            )
    return resolved


def connect(path: Path | str) -> sqlite3.Connection:
    """Open a connection with the settings every VoiceStock module relies on.

    Foreign keys are enforced, writes wait up to ``BUSY_TIMEOUT_SECONDS`` for
    a concurrent writer, and the write-ahead log lets readers proceed while a
    transaction is open. The parent directory is created when missing.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        path, timeout=BUSY_TIMEOUT_SECONDS, isolation_level=None
    )
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        if connection.execute("PRAGMA foreign_keys").fetchone() != (1,):
            raise sqlite3.NotSupportedError("SQLite does not enforce foreign keys")
    except BaseException:
        connection.close()
        raise
    return connection


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run the block as one unit of work: commit on success, roll back on error.

    The write lock is taken when the block starts, so two units of work on the
    same file never interleave their writes.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
