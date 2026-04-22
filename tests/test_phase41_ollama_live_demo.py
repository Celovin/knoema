from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from luvoire.demo.ollama_live import (
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_SEED,
    available_ollama_models,
    run_live_ollama_demo,
    warm_live_ollama_demo_model,
)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_phase41_live_ollama_demo_assets_exist() -> None:
    assert Path("examples/05_live_ollama_demo.ipynb").exists()
    assert Path("docs/videos/ollama_live_demo.md").exists()


def test_phase41_available_ollama_models_reads_tags(monkeypatch: Any) -> None:
    def fake_urlopen(url: str, timeout: float) -> _FakeResponse:
        assert url == "http://localhost:11434/api/tags"
        assert timeout == 2.0
        return _FakeResponse({"models": [{"name": DEFAULT_OLLAMA_MODEL}, {"name": "qwen3:latest"}]})

    monkeypatch.setattr("luvoire.demo.ollama_live.request.urlopen", fake_urlopen)

    assert available_ollama_models() == [DEFAULT_OLLAMA_MODEL, "qwen3:latest"]


def test_phase41_demo_runner_builds_seeded_five_agent_result(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "luvoire.demo.ollama_live.ensure_ollama_model_available",
        lambda model, base_url="http://localhost:11434", timeout=2.0: None,
    )

    def fake_complete(self: Any, messages: list[dict[str, str]], **kwargs: Any) -> str:
        del self
        agent_id = "unknown"
        for message in messages:
            content = message.get("content", "")
            if "Persona ID:" in content:
                agent_id = content.split("Persona ID:", 1)[1].splitlines()[0].strip()
                break
        return json.dumps(
            {
                "action_type": "coordinate",
                "target": "mina" if agent_id != "mina" else "jiho",
                "content": f"{agent_id} confirms the live demo handoff.",
            }
        )

    monkeypatch.setattr("luvoire.demo.ollama_live.OllamaClient.complete", fake_complete)

    result = run_live_ollama_demo()

    assert result.model == DEFAULT_OLLAMA_MODEL
    assert result.seed == DEFAULT_OLLAMA_SEED
    assert result.tick_count == 1
    assert result.action_count == 5
    assert result.relationship_edges >= 4
    assert result.action_mix == {"coordinate": 5}
    assert len(result.jsonl.splitlines()) == 5


def test_phase41_warmup_uses_live_model(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "luvoire.demo.ollama_live.ensure_ollama_model_available",
        lambda model, base_url="http://localhost:11434", timeout=2.0: None,
    )

    captured: dict[str, Any] = {}

    def fake_complete(self: Any, messages: list[dict[str, str]], **kwargs: Any) -> str:
        del self
        captured["messages"] = messages
        captured["kwargs"] = kwargs
        return '{"action_type":"observe","target":null,"content":"ready"}'

    monkeypatch.setattr("luvoire.demo.ollama_live.OllamaClient.complete", fake_complete)

    elapsed = warm_live_ollama_demo_model()

    assert elapsed >= 0.0
    assert "Warm the model" in captured["messages"][1]["content"]
    assert captured["kwargs"]["seed"] == DEFAULT_OLLAMA_SEED
    assert captured["kwargs"]["max_tokens"] == 32


def test_phase41_notebook_and_recording_doc_cover_model_seed_and_timing() -> None:
    notebook = json.loads(Path("examples/05_live_ollama_demo.ipynb").read_text(encoding="utf-8"))
    source = "\n".join("".join(cell.get("source", [])) for cell in notebook["cells"])
    doc = Path("docs/videos/ollama_live_demo.md").read_text(encoding="utf-8")

    assert "llama3.1:8b" in source
    assert "20260419" in source
    assert "30.0" in source or "30 seconds" in source
    assert "run_live_ollama_demo" in source
    assert "five-agent" in doc
    assert "30-second cap" in doc
    assert "llama3.1:8b" in doc


def test_phase41_live_ollama_smoke_completes_within_thirty_seconds(
    ollama_live_demo_model: str,
) -> None:
    warm_live_ollama_demo_model(model=ollama_live_demo_model)
    result = run_live_ollama_demo(model=ollama_live_demo_model)

    assert result.action_count == 5
    assert result.completed_within_target is True
    assert result.elapsed_seconds <= 30.0
