"""Round-6: tiktoken-backed estimate_tokens with heuristic fallback."""

from __future__ import annotations

import importlib
import sys

import pytest

import luvoire.llm.gateway as gateway_module
from luvoire.llm.gateway import estimate_tokens


def test_empty_string_returns_zero() -> None:
    assert estimate_tokens("") == 0


def test_short_text_returns_at_least_one() -> None:
    assert estimate_tokens("hi") >= 1


def test_token_count_grows_with_input_length() -> None:
    short = estimate_tokens("hello world")
    long = estimate_tokens("hello world " * 100)
    assert long > short


def test_estimate_falls_back_when_tiktoken_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If ``tiktoken`` cannot be imported (air-gapped CI / minimal
    install) ``estimate_tokens`` must fall back to the historical
    ``len(text) // 4`` heuristic so the billing meter keeps working.
    """

    # Reset the lazy-load cache so monkeypatch takes effect.
    monkeypatch.setattr(gateway_module, "_tiktoken_attempted", False)
    monkeypatch.setattr(gateway_module, "_tiktoken_encoder", None)

    # Force the import to fail by inserting a sentinel into sys.modules.
    real_tiktoken = sys.modules.pop("tiktoken", None)

    class _ImportBlocker:
        def find_spec(self, name: str, *_args: object, **_kwargs: object) -> None:
            if name == "tiktoken":
                raise ImportError("blocked by test")
            return None

    blocker = _ImportBlocker()
    sys.meta_path.insert(0, blocker)
    try:
        # 100-char text → fallback returns max(1, 100//4) = 25.
        result = estimate_tokens("a" * 100)
        assert result == 25
    finally:
        sys.meta_path.remove(blocker)
        if real_tiktoken is not None:
            sys.modules["tiktoken"] = real_tiktoken
        # Reset cache so subsequent tests see real tiktoken if available.
        monkeypatch.setattr(gateway_module, "_tiktoken_attempted", False)
        monkeypatch.setattr(gateway_module, "_tiktoken_encoder", None)


def test_estimate_uses_tiktoken_when_available() -> None:
    """When tiktoken IS installed, the result should differ from the
    pure ``len/4`` heuristic on Korean text (Hangul codepoints encode
    to ~2-3 BPE tokens each, not 1/4 of the character count).
    """

    tiktoken = pytest.importorskip("tiktoken")
    encoder = tiktoken.get_encoding("cl100k_base")
    text = "안녕하세요 반갑습니다 한국어 토큰 카운트 테스트"
    expected = max(1, len(encoder.encode(text)))
    # Reset cache so this test isn't sensitive to ordering.
    gateway_module._tiktoken_attempted = False
    gateway_module._tiktoken_encoder = None
    actual = estimate_tokens(text)
    assert actual == expected
    # Sanity: tiktoken disagrees with len/4 for Korean.
    assert actual != max(1, len(text) // 4)


def test_module_reload_resets_lazy_cache() -> None:
    """Reloading the gateway module must reset the tiktoken cache so a
    fresh process doesn't carry stale state across tests.
    """

    importlib.reload(gateway_module)
    assert gateway_module._tiktoken_attempted is False
    assert gateway_module._tiktoken_encoder is None
