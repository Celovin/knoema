"""Opt-in observability hooks for Luvoire."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "genai_attributes",
    "record_billing_tokens",
    "record_rate_limit_hit",
    "record_webhook_dispatch",
    "setup_metrics",
    "setup_tracing",
    "trace_span",
    "tracing",
]


def __getattr__(name: str) -> Any:
    if name == "tracing":
        return import_module("luvoire.observability.tracing")
    if name in {"record_billing_tokens", "record_rate_limit_hit", "record_webhook_dispatch", "setup_metrics"}:
        module = import_module("luvoire.observability.metrics")
        return getattr(module, name)
    if name in {"genai_attributes", "setup_tracing", "trace_span"}:
        module = import_module("luvoire.observability.tracing")
        return getattr(module, name)
    raise AttributeError(name)
