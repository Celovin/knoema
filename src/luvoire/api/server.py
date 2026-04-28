"""FastAPI application for the Luvoire runtime."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from luvoire.api.rate_limit import RateLimiter
from luvoire.api.routes import agents, events, simulations, unity, ws
from luvoire.api.routes import stripe_webhook as stripe_webhook_route
from luvoire.api.schemas import HealthResponse
from luvoire.api.service import SimulationService
from luvoire.api.tier_rate_limit import TierRateLimiter
from luvoire.api.unity_service import UnityRuntimeService
from luvoire.api.usage_middleware import UsageMeteringMiddleware
from luvoire.billing.api_keys import APIKeyManager
from luvoire.billing.gateway import UsageMeter
from luvoire.billing.tenant_registry import TenantRegistry
from luvoire.config import get_env
from luvoire.observability.metrics import setup_metrics
from luvoire.observability.tracing import setup_tracing

LOGGER = logging.getLogger(__name__)


def _optional_env(name: str, old_name: str | None = None) -> str | None:
    value = get_env(name, old_name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _env_flag(name: str, old_name: str | None = None) -> bool:
    return (_optional_env(name, old_name) or "").lower() in {"1", "true", "yes", "on"}


def create_app(
    *,
    simulation_service: SimulationService | None = None,
    unity_runtime_service: UnityRuntimeService | None = None,
    rate_limiter: RateLimiter | None = None,
    api_key_manager: APIKeyManager | None = None,
    usage_meter: UsageMeter | None = None,
    tier_rate_limiter: TierRateLimiter | None = None,
    stripe_webhook_handler: stripe_webhook_route.StripeWebhookHandler | None = None,
) -> FastAPI:
    service = simulation_service or SimulationService()
    unity_service = unity_runtime_service or UnityRuntimeService()
    limiter = rate_limiter or RateLimiter.from_env()
    tenant_keys = api_key_manager or TenantRegistry().key_manager()
    meter = usage_meter or UsageMeter()
    tenant_limiter = tier_rate_limiter or TierRateLimiter()
    # The Stripe handler stays unconfigured (secret=None) by default so
    # ``create_app()`` keeps working in air-gapped CI; the webhook
    # endpoint will return 503 until ``STRIPE_WEBHOOK_SECRET`` is set
    # OR an explicit handler is injected here.
    stripe_handler = stripe_webhook_handler or stripe_webhook_route.StripeWebhookHandler()
    otel_exporter = _optional_env("LUVOIRE_OTEL_EXPORTER", "KNOEMA_OTEL_EXPORTER")
    metrics_enabled = _env_flag("LUVOIRE_METRICS_ENABLED", "KNOEMA_METRICS_ENABLED")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.simulation_service = service
        app.state.unity_runtime_service = unity_service
        app.state.rate_limiter = limiter
        app.state.api_key_manager = tenant_keys
        app.state.usage_meter = meter
        app.state.tier_rate_limiter = tenant_limiter
        app.state.stripe_webhook_handler = stripe_handler
        app.state.observability = {
            "metrics_enabled": metrics_enabled,
            "otel_exporter": otel_exporter or "none",
        }
        LOGGER.info(
            "luvoire_observability_startup",
            extra={
                "luvoire_metrics_enabled": metrics_enabled,
                "luvoire_otel_exporter": otel_exporter or "none",
            },
        )
        try:
            yield
        finally:
            service.shutdown()
            unity_service.shutdown()

    app = FastAPI(
        title="Luvoire API",
        version="0.3.0",
        description="REST and WebSocket surface for Luvoire simulations.",
        lifespan=lifespan,
    )
    app.add_middleware(UsageMeteringMiddleware)
    setup_metrics(app, enabled=metrics_enabled)
    setup_tracing(otel_exporter, app=app)

    @app.get("/healthz", response_model=HealthResponse, tags=["health"])
    def healthz() -> HealthResponse:
        return HealthResponse(
            status="ok",
            total_simulations=service.total_simulations(),
            active_simulations=service.active_simulations(),
        )

    app.include_router(simulations.router)
    app.include_router(agents.router)
    app.include_router(events.router)
    app.include_router(unity.router)
    app.include_router(ws.router)
    app.include_router(stripe_webhook_route.router)
    return app


app = create_app()


__all__ = ["app", "create_app"]
