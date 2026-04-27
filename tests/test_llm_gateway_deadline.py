"""Round-4 audit: cumulative deadline across LLMGateway provider fallback."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import pytest

from luvoire.llm.gateway import LLMGateway
from luvoire.protocols import Message


class _SlowFailingClient:
    """Provider that always fails after sleeping for ``delay`` seconds."""

    def __init__(self, *, model: str, delay: float) -> None:
        self.model = model
        self._delay = delay

    def complete(self, _messages: Sequence[Message], **_kwargs: Any) -> str:
        time.sleep(self._delay)
        raise RuntimeError(f"{self.model} unavailable")


def test_fallback_deadline_aborts_remaining_providers() -> None:
    """Three providers each sleeping 0.2s and failing; with a 0.25s
    cumulative deadline only the first one (or two) should run before
    the gateway raises ``TimeoutError`` — never the full sum.
    """

    providers = [
        ("p1", _SlowFailingClient(model="p1", delay=0.2)),
        ("p2", _SlowFailingClient(model="p2", delay=0.2)),
        ("p3", _SlowFailingClient(model="p3", delay=0.2)),
    ]
    gateway = LLMGateway(providers, fallback_deadline_seconds=0.25)

    started = time.perf_counter()
    with pytest.raises(TimeoutError, match="deadline"):
        gateway.complete([{"role": "user", "content": "hi"}])
    elapsed = time.perf_counter() - started

    # Without the deadline guard, total would be ~0.6s. With it, the
    # third provider must be skipped, capping wait around 0.4-0.5s.
    assert elapsed < 0.55, f"deadline did not abort fallback (elapsed={elapsed:.3f}s)"


def test_fallback_deadline_must_be_positive() -> None:
    providers = [("p1", _SlowFailingClient(model="p1", delay=0.0))]
    with pytest.raises(ValueError, match="positive"):
        LLMGateway(providers, fallback_deadline_seconds=0.0)
    with pytest.raises(ValueError, match="positive"):
        LLMGateway(providers, fallback_deadline_seconds=-1.0)


def test_default_deadline_is_present() -> None:
    """Constructing with no explicit deadline must still set one — the
    default is what bounds production wait, not the per-provider timeout.
    """

    providers = [("p1", _SlowFailingClient(model="p1", delay=0.0))]
    gateway = LLMGateway(providers)
    # Implementation detail check: the private attribute exists. We
    # don't test the literal value to keep room for future tuning.
    assert hasattr(gateway, "_fallback_deadline_seconds")
    assert gateway._fallback_deadline_seconds > 0
