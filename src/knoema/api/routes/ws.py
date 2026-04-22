"""WebSocket streaming route for live simulation logs."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketException, status

from knoema.api.auth import optional_websocket_tenant, require_websocket_api_key
from knoema.api.rate_limit import enforce_websocket_rate_limit
from knoema.api.service import SimulationNotFoundError
from knoema.api.tier_rate_limit import TierRateLimiter

router = APIRouter(tags=["stream"])


@router.websocket("/simulations/{simulation_id}/stream")
async def stream_simulation(simulation_id: str, websocket: WebSocket) -> None:
    require_websocket_api_key(websocket)
    tenant = optional_websocket_tenant(websocket)
    if tenant is None:
        enforce_websocket_rate_limit(websocket)
    else:
        limiter = getattr(websocket.app.state, "tier_rate_limiter", None)
        if limiter is None:
            limiter = TierRateLimiter()
            websocket.app.state.tier_rate_limiter = limiter
        if not limiter.consume(tenant).allowed:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Tenant rate limit exceeded.",
            )
    await websocket.accept()
    service = websocket.app.state.simulation_service
    cursor = 0
    while True:
        try:
            record = service.get(simulation_id)
        except SimulationNotFoundError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        logs = record.simulator.logs
        while cursor < len(logs):
            entry = logs[cursor]
            await websocket.send_json(
                {
                    "type": "simulation.log",
                    "simulation_id": simulation_id,
                    "payload": entry.to_json_dict(),
                }
            )
            cursor += 1
        if record.status in {"completed", "failed", "cancelled"}:
            await websocket.send_json(
                {
                    "type": "simulation.status",
                    "simulation_id": simulation_id,
                    "status": record.status,
                    "completed_ticks": record.completed_ticks,
                    "total_ticks": record.total_ticks,
                    "error": record.error,
                }
            )
            await websocket.close()
            return
        await asyncio.sleep(0.01)


__all__ = ["router"]
