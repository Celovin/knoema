"""Tests for ``luvoire.safety.url_scheme.require_http_url``."""

from __future__ import annotations

import pytest

from luvoire.safety.url_scheme import UrlSchemeError, require_http_url


def test_https_url_passes_through() -> None:
    assert require_http_url("https://kosis.kr/api") == "https://kosis.kr/api"


def test_http_url_passes_through() -> None:
    assert require_http_url("http://localhost:11434/api/tags") == (
        "http://localhost:11434/api/tags"
    )


@pytest.mark.parametrize(
    "evil_url",
    [
        "file:///etc/passwd",
        "file://C:/Windows/System32/config/SAM",
        "gopher://10.0.0.1:8080/_attack",
        "ftp://example.com/leak",
        "data:text/html,<script>alert(1)</script>",
        "javascript:void(0)",
        "ldap://internal.local:389/dc=corp",
    ],
)
def test_non_http_schemes_are_rejected(evil_url: str) -> None:
    with pytest.raises(UrlSchemeError, match="not allowed"):
        require_http_url(evil_url)


def test_url_without_scheme_is_rejected() -> None:
    with pytest.raises(UrlSchemeError):
        require_http_url("example.com/api")


def test_url_with_scheme_but_no_host_is_rejected() -> None:
    """``http:somepath`` parses with empty netloc; would otherwise let
    urlopen treat the input as a local path."""

    with pytest.raises(UrlSchemeError, match="host"):
        require_http_url("http:somepath")


@pytest.mark.parametrize(
    "empty_input",
    ["", "   ", "\t\n"],
)
def test_empty_input_is_rejected(empty_input: str) -> None:
    with pytest.raises(UrlSchemeError):
        require_http_url(empty_input)


def test_non_string_input_is_rejected() -> None:
    with pytest.raises(UrlSchemeError):
        require_http_url(None)  # type: ignore[arg-type]
    with pytest.raises(UrlSchemeError):
        require_http_url(123)  # type: ignore[arg-type]


def test_uppercase_scheme_accepted() -> None:
    """Case-insensitive scheme check — ``HTTPS://...`` should pass."""

    assert require_http_url("HTTPS://example.com") == "HTTPS://example.com"
