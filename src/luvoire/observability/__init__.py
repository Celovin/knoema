"""Opt-in observability hooks for Luvoire."""

from luvoire.observability.metrics import (
    record_billing_tokens,
    record_rate_limit_hit,
    record_webhook_dispatch,
    setup_metrics,
)
from luvoire.observability.tracing import setup_tracing, trace_span

__all__ = [
    "record_billing_tokens",
    "record_rate_limit_hit",
    "record_webhook_dispatch",
    "setup_metrics",
    "setup_tracing",
    "trace_span",
]
