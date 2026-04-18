from __future__ import annotations

import pytest

from knoema.demo.ollama_live import DEFAULT_OLLAMA_MODEL, available_ollama_models
from knoema.llm import LocalLLMError


@pytest.fixture(scope="session")
def ollama_live_demo_model() -> str:
    try:
        installed = available_ollama_models()
    except LocalLLMError as exc:
        pytest.skip(f"live Ollama smoke skipped: {exc}")
    if DEFAULT_OLLAMA_MODEL not in installed:
        pytest.skip(
            f"live Ollama smoke skipped: install {DEFAULT_OLLAMA_MODEL!r} with `ollama pull {DEFAULT_OLLAMA_MODEL}`"
        )
    return DEFAULT_OLLAMA_MODEL
