"""URL scheme validation for outbound HTTP calls.

Defense-in-depth helper used by every ``urllib.request.urlopen`` /
``httpx`` call site whose URL is sourced from operator config rather
than a hard-coded literal. Without it, a misconfigured deploy or an
attacker who can write to env / config could substitute ``file:///etc/
passwd`` (local file read), ``gopher://...`` (protocol smuggling), or a
private-network IP for SSRF.

The validator only allows ``http`` and ``https`` schemes and returns
the parsed URL on success; callers can then pass the URL straight to
``urlopen`` / ``httpx`` knowing the boundary check is done. The check
is intentionally minimal: hostname / IP allowlists belong in the
caller (e.g. KOSIS endpoint pinning), not in this helper.

Usage::

    from luvoire.safety.url_scheme import require_http_url

    safe_url = require_http_url(endpoint_url)
    request.urlopen(safe_url, timeout=5)
"""

from __future__ import annotations

from urllib.parse import urlparse

_ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


class UrlSchemeError(ValueError):
    """Raised when a URL's scheme is not on the allowlist."""


def require_http_url(url: str) -> str:
    """Return ``url`` unchanged when it has an ``http(s)`` scheme.

    Raises :class:`UrlSchemeError` for any other scheme (``file``,
    ``gopher``, ``ftp``, ``data``, missing scheme, etc.). Empty / non-
    string input is also rejected with the same exception type so a
    single ``except UrlSchemeError`` catches all rejection paths.
    """

    if not isinstance(url, str) or not url.strip():
        raise UrlSchemeError("URL must be a non-empty string")
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UrlSchemeError(
            f"URL scheme {parsed.scheme!r} is not allowed; "
            f"only {sorted(_ALLOWED_SCHEMES)} accepted"
        )
    if not parsed.netloc:
        # ``http:somepath`` without ``//host`` parses with an empty
        # netloc and would still be accepted by ``urlopen`` against
        # a local filesystem. Reject it explicitly.
        raise UrlSchemeError(f"URL {url!r} has no host component")
    return url


__all__ = ["UrlSchemeError", "require_http_url"]
