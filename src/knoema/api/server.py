"""FastAPI application for the Knoema runtime."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from knoema.api.rate_limit import RateLimiter
from knoema.api.routes import agents, events, simulations, unity, ws
from knoema.api.schemas import HealthResponse
from knoema.api.service import SimulationService
from knoema.api.tier_rate_limit import TierRateLimiter
from knoema.api.unity_service import UnityRuntimeService
from knoema.api.usage_middleware import UsageMeteringMiddleware
from knoema.billing.api_keys import APIKeyManager
from knoema.billing.gateway import UsageMeter


def create_app(
    *,
    simulation_service: SimulationService | None = None,
    unity_runtime_service: UnityRuntimeService | None = None,
    rate_limiter: RateLimiter | None = None,
    api_key_manager: APIKeyManager | None = None,
    usage_meter: UsageMeter | None = None,
    tier_rate_limiter: TierRateLimiter | None = None,
) -> FastAPI:
    service = simulation_service or SimulationService()
    unity_service = unity_runtime_service or UnityRuntimeService()
    limiter = rate_limiter or RateLimiter.from_env()
    tenant_keys = api_key_manager or APIKeyManager()
    meter = usage_meter or UsageMeter()
    tenant_limiter = tier_rate_limiter or TierRateLimiter()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.simulation_service = service
        app.state.unity_runtime_service = unity_service
        app.state.rate_limiter = limiter
        app.state.api_key_manager = tenant_keys
        app.state.usage_meter = meter
        app.state.tier_rate_limiter = tenant_limiter
        try:
            yield
        finally:
            service.shutdown()
            unity_service.shutdown()

    app = FastAPI(
        title="Knoema Engine API",
        version="0.2.0",
        description="REST and WebSocket surface for Knoema simulations.",
        lifespan=lifespan,
    )
    app.add_middleware(UsageMeteringMiddleware)

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
    return app


app = create_app()

__all__ = ["app", "create_app"]
