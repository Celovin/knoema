"""Prometheus metrics for opt-in API and billing observability."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

from luvoire.billing.tiers import TierName


@dataclass(slots=True)
class MetricsState:
    billing_tokens: Any
    registry: Any
    request_duration: Any
    requests_total: Any
    rate_limit_hits: Any
    webhook_dispatch_total: Any


_ACTIVE_METRICS: MetricsState | None = None


def setup_metrics(app: FastAPI, *, enabled: bool) -> bool:
    """Mount Prometheus metrics when enabled."""

    if not enabled:
        return False
    prometheus = _prometheus_client()
    registry = prometheus.CollectorRegistry(auto_describe=True)
    state = MetricsState(
        registry=registry,
        requests_total=prometheus.Counter(
            "luvoire_requests_total",
            "HTTP requests served by the Luvoire API.",
            ("route", "method", "status", "tier"),
            registry=registry,
        ),
        request_duration=prometheus.Histogram(
            "luvoire_request_duration_seconds",
            "HTTP request duration in seconds.",
            ("route",),
            registry=registry,
        ),
        billing_tokens=prometheus.Counter(
            "luvoire_billing_tokens_total",
            "Billing token usage by hashed tenant, direction, and tier.",
            ("tenant_id_hash", "direction", "tier"),
            registry=registry,
        ),
        webhook_dispatch_total=prometheus.Counter(
            "luvoire_webhook_dispatch_total",
            "Webhook dispatch attempts by status.",
            ("status",),
            registry=registry,
        ),
        rate_limit_hits=prometheus.Counter(
            "luvoire_rate_limit_hits_total",
            "Tenant tier rate-limit hits.",
            ("tier",),
            registry=registry,
        ),
    )
    app.state.luvoire_metrics = state
    _set_active_metrics(state)

    @app.middleware("http")
    async def _metrics_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = int(response.status_code)
            return response
        finally:
            route = _route_template(request)
            tier = _request_tier(request)
            state.requests_total.labels(
                route=route,
                method=request.method,
                status=str(status_code),
                tier=tier,
            ).inc()
            state.request_duration.labels(route=route).observe(perf_counter() - started)

    @app.get("/metrics", include_in_schema=False)
    def _metrics_endpoint() -> Response:
        return Response(
            prometheus.generate_latest(registry),
            media_type=prometheus.CONTENT_TYPE_LATEST,
        )

    return True


def record_billing_tokens(
    *,
    tenant_id: str,
    tier: TierName,
    input_tokens: int,
    output_tokens: int,
) -> None:
    state = _ACTIVE_METRICS
    if state is None:
        return
    tenant_hash = _tenant_hash(tenant_id)
    if input_tokens:
        state.billing_tokens.labels(
            tenant_id_hash=tenant_hash,
            direction="input",
            tier=tier,
        ).inc(float(input_tokens))
    if output_tokens:
        state.billing_tokens.labels(
            tenant_id_hash=tenant_hash,
            direction="output",
            tier=tier,
        ).inc(float(output_tokens))


def record_webhook_dispatch(status: str) -> None:
    state = _ACTIVE_METRICS
    if state is None:
        return
    state.webhook_dispatch_total.labels(status=status).inc()


def record_rate_limit_hit(tier: TierName) -> None:
    state = _ACTIVE_METRICS
    if state is None:
        return
    state.rate_limit_hits.labels(tier=tier).inc()


def _set_active_metrics(state: MetricsState) -> None:
    global _ACTIVE_METRICS
    _ACTIVE_METRICS = state


def _request_tier(request: Request) -> str:
    tenant = getattr(request.state, "authenticated_tenant", None)
    tier = getattr(tenant, "tier", None)
    if isinstance(tier, str):
        return tier
    return "anonymous"


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if isinstance(path, str):
        return path
    return request.url.path


def _tenant_hash(tenant_id: str) -> str:
    return sha256(tenant_id.encode("utf-8")).hexdigest()[:16]


def _prometheus_client() -> Any:
    try:
        import prometheus_client
    except ImportError as exc:  # pragma: no cover - depends on optional install
        raise RuntimeError("Install luvoire-engine[observability] to enable Prometheus metrics.") from exc
    return prometheus_client


__all__ = [
    "MetricsState",
    "record_billing_tokens",
    "record_rate_limit_hit",
    "record_webhook_dispatch",
    "setup_metrics",
]
