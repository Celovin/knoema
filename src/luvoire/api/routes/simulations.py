"""Simulation lifecycle routes."""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from knoema.api.auth import AuthenticatedTenant
from knoema.api.rate_limit import enforce_rate_limit
from knoema.api.schemas import CreateSimulationRequest, SimulationStatusResponse
from knoema.api.service import SimulationNotFoundError, SimulationRecord, SimulationService
from knoema.api.tier_rate_limit import enforce_tier_rate_limit
from knoema.api.usage_middleware import record_request_usage
from knoema.billing.tiers import is_model_allowed

router = APIRouter(prefix="/simulations", tags=["simulations"])


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


def _ensure_model_allowed(tenant: AuthenticatedTenant, model: str) -> None:
    if is_model_allowed(tenant.tier, model):
        return
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail=f"Upgrade tier to use model '{model}'.",
    )


def _create_simulation_response(
    request_body: CreateSimulationRequest,
    request: Request,
    tenant: AuthenticatedTenant,
    model: str,
) -> SimulationStatusResponse:
    _ensure_model_allowed(tenant, model)
    service = _service_from_request(request)
    record = service.create(request_body)
    record_request_usage(
        request,
        model=model,
        input_tokens=len(request_body.agents),
        output_tokens=record.total_ticks,
        cost_usd="0",
    )
    return _status_response(record)


@router.post("", response_model=SimulationStatusResponse, status_code=status.HTTP_201_CREATED)
def create_simulation(
    request_body: CreateSimulationRequest,
    request: Request,
    tenant: Annotated[AuthenticatedTenant, Depends(enforce_tier_rate_limit)],
    model: str = Query(default="gpt-5.4-mini"),
) -> SimulationStatusResponse:
    return _create_simulation_response(request_body, request, tenant, model)


@router.post("/run", response_model=SimulationStatusResponse)
def run_simulation(
    request_body: CreateSimulationRequest,
    request: Request,
    tenant: Annotated[AuthenticatedTenant, Depends(enforce_tier_rate_limit)],
    model: str = Query(default="gpt-5.4-mini"),
) -> SimulationStatusResponse:
    return _create_simulation_response(request_body, request, tenant, model)


@router.get("/{simulation_id}", response_model=SimulationStatusResponse, dependencies=[Depends(enforce_rate_limit)])
def get_simulation(simulation_id: str, request: Request) -> SimulationStatusResponse:
    service = _service_from_request(request)
    try:
        record = service.get(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    return _status_response(record)


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(enforce_rate_limit)])
def delete_simulation(simulation_id: str, request: Request) -> Response:
    service = _service_from_request(request)
    try:
        service.delete(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


__all__ = ["router"]
