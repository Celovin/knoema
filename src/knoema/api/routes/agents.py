"""Agent inspection routes."""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, status

from knoema.api.auth import require_api_key
from knoema.api.rate_limit import enforce_rate_limit
from knoema.api.schemas import AgentListResponse, AgentSummary, MemoryItem, MemoryListResponse
from knoema.api.service import SimulationNotFoundError, SimulationService

router = APIRouter(
    prefix="/simulations",
    tags=["agents"],
    dependencies=[Depends(require_api_key), Depends(enforce_rate_limit)],
)


def _service_from_request(request: Request) -> SimulationService:
    return cast(SimulationService, request.app.state.simulation_service)


@router.get("/{simulation_id}/agents", response_model=AgentListResponse)
def list_agents(simulation_id: str, request: Request) -> AgentListResponse:
    service = _service_from_request(request)
    try:
        record = service.get(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    agents = []
    for agent in record.simulator.agents:
        context = record.simulator.environment.get_context(agent.agent_id)
        agents.append(
            AgentSummary(
                agent_id=agent.agent_id,
                name=agent.name,
                location=context.location,
                memory_count=len(record.simulator.short_term_memories[agent.agent_id]),
                theory_of_mind_enabled=agent.theory_of_mind.enabled,
            )
        )
    return AgentListResponse(simulation_id=simulation_id, agents=agents)


@router.get("/{simulation_id}/agents/{agent_id}/memory", response_model=MemoryListResponse)
def get_agent_memory(simulation_id: str, agent_id: str, request: Request) -> MemoryListResponse:
    service = _service_from_request(request)
    try:
        record = service.get(simulation_id)
    except SimulationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation not found.") from exc
    memory_buffer = record.simulator.short_term_memories.get(agent_id)
    if memory_buffer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found.")
    memories = [MemoryItem.from_domain(memory) for memory in memory_buffer.recent()]
    return MemoryListResponse(
        simulation_id=simulation_id,
        agent_id=agent_id,
        memories=memories,
    )


__all__ = ["router"]
