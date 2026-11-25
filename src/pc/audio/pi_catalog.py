"""Fetch the Raspberry Pi catalog before an interpretation.

The PC keeps the last validated snapshot in memory. It does not open the Pi
database and it does not write the catalog back. A failed request leaves the
previous snapshot installed and refuses the current audio operation.
"""

import logging

import httpx

from pc.audio.catalog import (
    CatalogSnapshotError,
    InstalledCatalog,
    parse_catalog_snapshot,
)

logger = logging.getLogger(__name__)


class CatalogSyncError(Exception):
    """The Pi catalog could not be synchronized for this operation."""


class PiCatalogSession:
    """Conditional ``GET /api/v1/catalog`` against one Pi base URL."""

    def __init__(self, base_url: str, client: httpx.Client) -> None:
        self._client = client
        self._url = f"{base_url.rstrip('/')}/api/v1/catalog"
        self._current: InstalledCatalog | None = None
        self._closed = False

    @property
    def current(self) -> InstalledCatalog | None:
        """The snapshot accepted for interpretation, if one exists."""
        return self._current

    def pull(self) -> InstalledCatalog:
        """Read the current snapshot. A new body is not installed yet."""
        if self._closed:
            raise CatalogSyncError("catalog client is closed")
        headers = {}
        if self._current is not None:
            headers["If-None-Match"] = f'"{self._current.revision}"'
        try:
            response = self._client.get(self._url, headers=headers)
        except httpx.TimeoutException as error:
            logger.info("catalog request timed out")
            raise CatalogSyncError("catalog request timed out") from error
        except httpx.HTTPError as error:
            logger.info("catalog request failed")
            raise CatalogSyncError("catalog request failed") from error
        try:
            return self._read(response)
        finally:
            response.close()

    def accept(self, catalog: InstalledCatalog) -> None:
        """Install ``catalog`` only after its interpretation context exists."""
        self._current = catalog

    def close(self) -> None:
        """Close the HTTP client. A second call does nothing."""
        if self._closed:
            return
        self._closed = True
        self._client.close()

    def _read(self, response: httpx.Response) -> InstalledCatalog:
        if response.status_code == 304:
            if self._current is None:
                raise CatalogSyncError("catalog returned 304 before a snapshot existed")
            etag = response.headers.get("etag")
            if _etag_value(etag) != self._current.revision:
                raise CatalogSyncError("catalog 304 etag does not match the snapshot")
            return self._current
        if response.status_code != 200:
            logger.info("catalog request returned HTTP %s", response.status_code)
            raise CatalogSyncError(
                f"catalog request returned HTTP {response.status_code}"
            )
        try:
            body = response.json()
        except ValueError as error:
            raise CatalogSyncError("catalog response is not JSON") from error
        try:
            return parse_catalog_snapshot(body, response.headers.get("etag"))
        except CatalogSnapshotError as error:
            raise CatalogSyncError(str(error)) from error


def _etag_value(header: str | None) -> str | None:
    if header is None:
        return None
    text = header.strip()
    if text[:2].upper() == "W/":
        text = text[2:].strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        return None
    return text[1:-1]
