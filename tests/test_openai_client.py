from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import Any

from luvoire.llm import OpenAIClient


def test_openai_client_supports_openai_compatible_base_url(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class _ResponsesApi:
        def create(self, **kwargs: Any) -> Any:
            captured["request"] = kwargs
            return SimpleNamespace(
                output_text="compatible ok",
                usage=SimpleNamespace(input_tokens=12, output_tokens=7),
            )

    class _FakeOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured["init"] = kwargs
            self.responses = _ResponsesApi()

    module = ModuleType("openai")
    module.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", module)

    client = OpenAIClient(
        model="gpt-5-mini",
        api_key="local-token",
        base_url="http://127.0.0.1:8000/v1",
    )
    response = client.complete(
        [{"role": "user", "content": "hello openai-compatible"}],
        temperature=0.2,
        max_tokens=64,
    )

    assert response == "compatible ok"
    assert captured["init"] == {
        "api_key": "local-token",
        "base_url": "http://127.0.0.1:8000/v1",
    }
    assert captured["request"]["model"] == "gpt-5-mini"
    assert captured["request"]["temperature"] == 0.2
    assert captured["request"]["max_output_tokens"] == 64
