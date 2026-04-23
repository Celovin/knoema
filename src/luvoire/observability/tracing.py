"""OpenTelemetry tracing setup for opt-in Luvoire observability."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from importlib import import_module
from typing import Any

_TRACER: Any | None = None


def setup_tracing(exporter: str | None, *, app: object | None = None) -> bool:
    """Configure OpenTelemetry tracing when an exporter name is supplied."""

    if exporter is None or exporter == "":
        return False
    if exporter != "otlp":
        raise ValueError("LUVOIRE_OTEL_EXPORTER must be unset or 'otlp'")

    try:
        trace = import_module("opentelemetry.trace")
        fastapi_module = import_module("opentelemetry.instrumentation.fastapi")
        resources_module = import_module("opentelemetry.sdk.resources")
        trace_sdk_module = import_module("opentelemetry.sdk.trace")
        export_module = import_module("opentelemetry.sdk.trace.export")
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install luvoire-engine[observability] to enable OpenTelemetry tracing.") from exc

    resource = resources_module.Resource.create({"service.name": "luvoire-engine"})
    provider = trace.get_tracer_provider()
    if not hasattr(provider, "add_span_processor"):
        provider = trace_sdk_module.TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
    provider.add_span_processor(export_module.SimpleSpanProcessor(_build_span_exporter(exporter)))
    _set_tracer(trace.get_tracer("luvoire"))
    if app is not None:
        fastapi_module.FastAPIInstrumentor.instrument_app(app)
    return True


def genai_attributes(
    *,
    system: str,
    operation: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    base_url: str | None = None,
) -> dict[str, object]:
    """Build a stable attribute set for Luvoire GenAI spans."""

    attributes: dict[str, object] = {
        "gen_ai.system": system,
        "gen_ai.operation.name": operation,
    }
    if model:
        attributes["gen_ai.request.model"] = model
    if temperature is not None:
        attributes["gen_ai.request.temperature"] = temperature
    if max_tokens is not None:
        attributes["gen_ai.request.max_tokens"] = max_tokens
    if base_url:
        attributes["luvoire.llm.base_url"] = base_url
    return attributes


@contextmanager
def trace_span(name: str, attributes: Mapping[str, object] | None = None) -> Iterator[Any | None]:
    tracer = _TRACER
    if tracer is None:
        yield None
        return
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)
        yield span


def _build_span_exporter(exporter: str) -> Any:
    if exporter != "otlp":
        raise ValueError("unsupported tracing exporter")
    try:
        exporter_module = import_module("opentelemetry.exporter.otlp.proto.http.trace_exporter")
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install opentelemetry-exporter-otlp-proto-http for OTLP export.") from exc
    return exporter_module.OTLPSpanExporter()


def _set_tracer(tracer: Any) -> None:
    global _TRACER
    _TRACER = tracer


__all__ = ["genai_attributes", "setup_tracing", "trace_span"]
