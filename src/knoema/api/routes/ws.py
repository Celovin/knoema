"""WebSocket streaming route for live simulation logs."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, status

from knoema.api.auth import require_websocket_api_key
from knoema.api.rate_limit import enforce_websocket_rate_limit
from knoema.api.service import SimulationNotFoundError

router = APIRouter(tags=["stream"])


@router.websocket("/simulations/{simulation_id}/stream")
async def stream_simulation(simulation_id: str, websocket: WebSocket) -> None:
    require_websocket_api_key(websocket)
    enforce_websocket_rate_limit(websocket)
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
