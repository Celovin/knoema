"""Demo helpers for notebooks, recordings, and reproducible showcases."""

from knoema.demo.ollama_live import (
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_SEED,
    OllamaLiveDemoResult,
    available_ollama_models,
    run_live_ollama_demo,
    warm_live_ollama_demo_model,
)

__all__ = [
    "DEFAULT_OLLAMA_MODEL",
    "DEFAULT_OLLAMA_SEED",
    "OllamaLiveDemoResult",
    "available_ollama_models",
    "run_live_ollama_demo",
    "warm_live_ollama_demo_model",
]
