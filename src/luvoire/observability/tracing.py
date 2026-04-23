"""OpenTelemetry tracing setup for opt-in Luvoire observability."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from importlib import import_module
from typing import Any
from urllib.parse import urlsplit, urlunsplit
from weakref import WeakSet

_TRACER: Any | None = None
_REGISTERED_PROCESSORS: dict[tuple[int, str], Any] = {}
_INSTRUMENTED_APPS: WeakSet[object] = WeakSet()


def setup_tracing(exporter: str | None, *, app: object | None = None) -> bool:
    """Configure OpenTelemetry tracing when an exporter name is supplied."""

    if exporter is None or exporter == "":
        _set_tracer(None)
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
    processor_key = (id(provider), exporter)
    if processor_key not in _REGISTERED_PROCESSORS:
        processor = export_module.SimpleSpanProcessor(_build_span_exporter(exporter))
        provider.add_span_processor(processor)
        _REGISTERED_PROCESSORS[processor_key] = processor
    _set_tracer(trace.get_tracer("luvoire"))
    if app is not None and app not in _INSTRUMENTED_APPS:
        fastapi_module.FastAPIInstrumentor.instrument_app(app)
        _INSTRUMENTED_APPS.add(app)
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
    sanitized_base_url = _sanitize_base_url(base_url)
    if sanitized_base_url:
        attributes["luvoire.llm.base_url"] = sanitized_base_url
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


def _sanitize_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    try:
        parsed = urlsplit(base_url)
    except ValueError:
        return None
    if not parsed.scheme or parsed.hostname is None:
        return None
    netloc = parsed.hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    return urlunsplit((parsed.scheme, netloc, "", "", ""))


def _reset_tracing_state_for_tests() -> None:
    global _INSTRUMENTED_APPS
    _set_tracer(None)
    _INSTRUMENTED_APPS = WeakSet()
    try:
        trace = import_module("opentelemetry.trace")
    except ImportError:
        _REGISTERED_PROCESSORS.clear()
        return
    provider = trace.get_tracer_provider()
    active_processor = getattr(provider, "_active_span_processor", None)
    current_processors = getattr(active_processor, "_span_processors", None)
    if active_processor is not None and isinstance(current_processors, tuple):
        registered = set(_REGISTERED_PROCESSORS.values())
        active_processor._span_processors = tuple(
            processor for processor in current_processors if processor not in registered
        )
    for processor in _REGISTERED_PROCESSORS.values():
        shutdown = getattr(processor, "shutdown", None)
        if callable(shutdown):
            shutdown()
    _REGISTERED_PROCESSORS.clear()


__all__ = ["genai_attributes", "setup_tracing", "trace_span"]
