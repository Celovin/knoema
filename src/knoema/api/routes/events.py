"""Event injection routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, status

from knoema.api.auth import require_api_key
from knoema.api.rate_limit import enforce_rate_limit
from knoema.api.schemas import ApiEventConfig, InjectedEventResponse
from knoema.api.service import SimulationNotFoundError, SimulationService, SimulationStateError

router = APIRouter(
    prefix="/simulations",
    tags=["events"],
    dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
)


def _service_from_request(request: Request) -> SimulationService:
    return cast(SimulationService, request.app.state.simulation_service)


@router.post("/{simulation_id}/events", response_model=InjectedEventResponse)
def inject_event(
    simulation_id: str,
    event_request: ApiEventConfig,
    request: Request,
) -> InjectedEventResponse:
    service = _service_from_request(request)
    try:
        record = service.get(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    event = event_request.to_domain(
        default_timestamp=record.simulator.environment.current_time,
        default_location=" > ".join(record.simulator.environment.location_path),
    )
    try:
        updated = service.inject_event(simulation_id, event)
    except SimulationStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return InjectedEventResponse(
        simulation_id=simulation_id,
        accepted=True,
        scheduled_events=updated.scheduled_events,
        event=event_request.model_copy(update={"timestamp": event.timestamp, "location": event.location}),
    )


__all__ = ["router"]
