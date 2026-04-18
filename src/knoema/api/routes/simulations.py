"""Simulation lifecycle routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from knoema.api.auth import require_api_key
from knoema.api.rate_limit import enforce_rate_limit
from knoema.api.schemas import CreateSimulationRequest, SimulationStatusResponse
from knoema.api.service import SimulationNotFoundError, SimulationRecord, SimulationService

router = APIRouter(
    prefix="/simulations",
    tags=["simulations"],
    dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
)


def _service_from_request(request: Request) -> SimulationService:
    return cast(SimulationService, request.app.state.simulation_service)


def _status_response(record: SimulationRecord) -> SimulationStatusResponse:
    return SimulationStatusResponse(
        simulation_id=record.simulation_id,
        status=record.status,
        agent_count=record.agent_count,
        completed_ticks=record.completed_ticks,
        total_ticks=record.total_ticks,
        scheduled_events=record.scheduled_events,
        started_at=record.started_at,
        updated_at=record.updated_at,
        error=record.error,
    )


@router.post("", response_model=SimulationStatusResponse, status_code=status.HTTP_201_CREATED)
def create_simulation(request_body: CreateSimulationRequest, request: Request) -> SimulationStatusResponse:
    service = _service_from_request(request)
    record = service.create(request_body)
    return _status_response(record)


@router.get("/{simulation_id}", response_model=SimulationStatusResponse)
def get_simulation(simulation_id: str, request: Request) -> SimulationStatusResponse:
    service = _service_from_request(request)
    try:
        record = service.get(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    return _status_response(record)


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_simulation(simulation_id: str, request: Request) -> Response:
    service = _service_from_request(request)
    try:
        service.delete(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
