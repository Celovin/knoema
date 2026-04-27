"""Round-4 audit: constant-time API key comparison for legacy auth path."""

from __future__ import annotations

from luvoire.api.auth import _tokens_equal


def test_tokens_equal_returns_true_on_match() -> None:
    assert _tokens_equal("abcd1234", "abcd1234") is True


def test_tokens_equal_returns_false_on_mismatch() -> None:
    assert _tokens_equal("abcd1234", "wxyz9876") is False


def test_tokens_equal_returns_false_when_expected_missing() -> None:
    """A missing server-side key MUST never compare equal — including
    against a missing presented token. Otherwise a misconfigured deploy
    would let any (or no) token through."""

    assert _tokens_equal(None, None) is False
    assert _tokens_equal("", None) is False
    assert _tokens_equal("anything", None) is False
    assert _tokens_equal(None, "") is False


def test_tokens_equal_handles_none_presented_token() -> None:
    """A missing client token must compare unequal but still run a
    fixed-length compare so the response time does not leak the length
    of the expected key.
    """

    assert _tokens_equal(None, "secret-key") is False


def test_tokens_equal_handles_different_lengths() -> None:
    """Different-length tokens must compare unequal without raising."""

    assert _tokens_equal("short", "muchlongerexpected") is False
    assert _tokens_equal("muchlongerpresented", "short") is False


def test_tokens_equal_handles_unicode() -> None:
    """Korean / non-ASCII keys must compare correctly via UTF-8 encoding."""

    assert _tokens_equal("키-1234", "키-1234") is True
    assert _tokens_equal("키-1234", "키-9999") is False
