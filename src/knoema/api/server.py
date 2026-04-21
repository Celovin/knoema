"""FastAPI application for the Knoema runtime."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from knoema.api.rate_limit import RateLimiter
from knoema.api.routes import agents, events, simulations, unity, ws
from knoema.api.schemas import HealthResponse
from knoema.api.service import SimulationService
from knoema.api.unity_service import UnityRuntimeService


def create_app(
    *,
    simulation_service: SimulationService | None = None,
    unity_runtime_service: UnityRuntimeService | None = None,
    rate_limiter: RateLimiter | None = None,
) -> FastAPI:
    service = simulation_service or SimulationService()
    unity_service = unity_runtime_service or UnityRuntimeService()
    limiter = rate_limiter or RateLimiter.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.simulation_service = service
        app.state.unity_runtime_service = unity_service
        app.state.rate_limiter = limiter
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
