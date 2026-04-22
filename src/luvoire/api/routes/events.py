"""Event injection routes."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status

from luvoire.api.auth import AuthenticatedTenant
from luvoire.api.schemas import ApiEventConfig, InjectedEventResponse
from luvoire.api.service import SimulationNotFoundError, SimulationService, SimulationStateError
from luvoire.api.tier_rate_limit import enforce_tier_rate_limit

router = APIRouter(prefix="/simulations", tags=["events"])


def _service_from_request(request: Request) -> SimulationService:
    return cast(SimulationService, request.app.state.simulation_service)


@router.post("/{simulation_id}/events", response_model=InjectedEventResponse)
def inject_event(
    simulation_id: str,
    event_request: ApiEventConfig,
    request: Request,
    tenant: Annotated[AuthenticatedTenant, Depends(enforce_tier_rate_limit)],
) -> InjectedEventResponse:
    _ = tenant
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
