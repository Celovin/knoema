from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knoema.llm import LlamaCppClient, LocalLLMError, OllamaClient, VLLMClient


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _messages() -> list[dict[str, str]]:
    return [{"role": "user", "content": "hello local model"}]


def test_phase36_ollama_client_posts_chat_payload(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({"message": {"content": "ollama ok"}})

    monkeypatch.setattr("knoema.llm.local.http.request.urlopen", fake_urlopen)

    client = OllamaClient(model="llama3.3", timeout=12.0)
    response = client.complete(_messages(), temperature=0.2, max_tokens=64)

    assert response == "ollama ok"
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["timeout"] == 12.0
    assert captured["body"]["model"] == "llama3.3"
    assert captured["body"]["stream"] is False
    assert captured["body"]["options"]["num_predict"] == 64


def test_phase36_llama_cpp_client_reads_openai_style_response(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({"choices": [{"message": {"content": "llama.cpp ok"}}]})

    monkeypatch.setattr("knoema.llm.local.http.request.urlopen", fake_urlopen)

    client = LlamaCppClient(model="local-gguf", base_url="http://127.0.0.1:8080/")
    response = client.complete(_messages(), max_tokens=32)

    assert response == "llama.cpp ok"
    assert captured["url"] == "http://127.0.0.1:8080/v1/chat/completions"
    assert captured["body"]["model"] == "local-gguf"
    assert captured["body"]["max_tokens"] == 32


def test_phase36_vllm_client_sends_bearer_token_when_configured(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float) -> _FakeResponse:
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse({"choices": [{"message": {"content": "vllm ok"}}]})

    monkeypatch.setattr("knoema.llm.local.http.request.urlopen", fake_urlopen)

    client = VLLMClient(model="Qwen/Qwen2.5-7B-Instruct", api_key="local-token")
    response = client.complete(_messages(), temperature=0.1)

    assert response == "vllm ok"
    assert captured["url"] == "http://localhost:8000/v1/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer local-token"
    assert captured["body"]["model"] == "Qwen/Qwen2.5-7B-Instruct"
    assert captured["body"]["temperature"] == 0.1


def test_phase36_local_adapters_raise_on_invalid_payload(monkeypatch: Any) -> None:
    def fake_urlopen(request: Any, timeout: float) -> _FakeResponse:
        return _FakeResponse({"choices": []})

    monkeypatch.setattr("knoema.llm.local.http.request.urlopen", fake_urlopen)

    client = VLLMClient()
    try:
        client.complete(_messages())
    except LocalLLMError as exc:
        assert "choices" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("LocalLLMError was not raised")


def test_phase36_docs_and_ollama_notebook_cover_required_models() -> None:
    benchmark = Path("src/knoema/llm/local/benchmarks/local_vs_cloud.md").read_text(
        encoding="utf-8"
    )
    notebook = json.loads(Path("examples/05_ollama_local_fallback.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])

    assert "Ollama" in benchmark
    assert "llama.cpp" in benchmark
    assert "vLLM" in benchmark
    assert "Llama 3.3" in benchmark
    assert "Gemma 3" in benchmark
    assert "Qwen 2.5" in benchmark
    assert "OllamaClient" in source
    assert "KNOEMA_RUN_OLLAMA_DEMO" in source
    assert "deterministic-local" in source
