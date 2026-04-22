"""Unity SDK compatibility routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from luvoire.api.auth import require_api_key
from luvoire.api.rate_limit import enforce_rate_limit
from luvoire.api.schemas import (
    UnityActionAcceptedResponse,
    UnityActionRequest,
    UnityMemoryResponse,
    UnityTickRequest,
    UnityTickResponse,
)
from luvoire.api.unity_service import UnityRuntimeService, UnitySessionNotFoundError

router = APIRouter(
    tags=["unity"],
    dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
)


def _unity_service_from_request(request: Request) -> UnityRuntimeService:
    return cast(UnityRuntimeService, request.app.state.unity_runtime_service)


@router.post("/simulate/tick", response_model=UnityTickResponse)
def simulate_tick(request_body: UnityTickRequest, request: Request) -> UnityTickResponse:
    service = _unity_service_from_request(request)
    try:
        return service.tick(request_body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/agent/{agent_id}/memory", response_model=UnityMemoryResponse)
def get_unity_agent_memory(
    agent_id: str,
    request: Request,
    session_id: str = Query(default="unity-demo", min_length=1),
) -> UnityMemoryResponse:
    service = _unity_service_from_request(request)
    try:
        return service.memory(session_id=session_id, agent_id=agent_id)
    except UnitySessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unity session not found.") from exc


@router.post("/agent/{agent_id}/action", response_model=UnityActionAcceptedResponse)
def post_unity_agent_action(
    agent_id: str,
    request_body: UnityActionRequest,
    request: Request,
) -> UnityActionAcceptedResponse:
    service = _unity_service_from_request(request)
    try:
        return service.apply_action(agent_id=agent_id, request=request_body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


__all__ = ["router"]
