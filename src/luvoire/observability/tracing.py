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
    provider = trace_sdk_module.TracerProvider(resource=resource)
    provider.add_span_processor(export_module.SimpleSpanProcessor(_build_span_exporter(exporter)))
    trace.set_tracer_provider(provider)
    _set_tracer(trace.get_tracer("luvoire"))
    if app is not None:
        fastapi_module.FastAPIInstrumentor.instrument_app(app)
    return True


@contextmanager
def trace_span(name: str, attributes: Mapping[str, object] | None = None) -> Iterator[None]:
    tracer = _TRACER
    if tracer is None:
        yield
        return
    with tracer.start_as_current_span(name) as span:
        for key, value in (attributes or {}).items():
            span.set_attribute(key, value)
        yield


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


__all__ = ["setup_tracing", "trace_span"]
