"""Weak comparison for ``If-None-Match``, as HTTP defines it.

The catalog ETag is the snapshot revision in quotes. A match does not require
the header to be byte-for-byte that quoted string: weak validators, a list,
and ``*`` are all part of the conditional request.
"""


def quoted_etag(revision: str) -> str:
    """Return a strong ETag for a revision that contains no quotes."""
    if '"' in revision or "\\" in revision or revision == "":
        raise ValueError("catalog revision cannot be used as an ETag")
    return f'"{revision}"'


def if_none_match_is_current(header: str | None, revision: str) -> bool:
    """Return whether ``header`` names the current revision, or ``*``.

    Comparison is weak: ``W/"revision"`` matches ``"revision"``. An unquoted
    token other than ``*`` does not match. A missing or blank header does not.
    """
    if header is None or header.strip() == "":
        return False
    for item in _split_etag_list(header):
        if item == "*":
            return True
        opaque = _opaque_tag(item)
        if opaque is not None and opaque == revision:
            return True
    return False


def _split_etag_list(header: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quoted = False
    for char in header:
        if char == '"':
            quoted = not quoted
            current.append(char)
            continue
        if char == "," and not quoted:
            piece = "".join(current).strip()
            if piece:
                parts.append(piece)
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _opaque_tag(item: str) -> str | None:
    text = item.strip()
    if text[:2].upper() == "W/":
        text = text[2:].strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        return None
    return text[1:-1]
