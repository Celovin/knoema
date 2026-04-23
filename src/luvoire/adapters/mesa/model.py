"""Mesa Model wrapper for a Luvoire Simulator."""

from __future__ import annotations

import importlib

from luvoire.adapters.mesa.agent import LuvoireMesaAgent
from luvoire.environment import EnvironmentContext
from luvoire.persona import Persona
from luvoire.simulator import Simulator
from luvoire.types import Action

mesa = importlib.import_module("mesa")


class LuvoireMesaModel(mesa.Model):  # type: ignore[misc,name-defined]
    """Expose a Luvoire `Simulator` through the Mesa 3 model surface."""

    def __init__(self, sim: Simulator, seed: int = 0) -> None:
        super().__init__(rng=seed)
        self.luv = sim
        self.seed = int(seed)
        self.current_tick = 0
        self._agents_by_id: dict[str, LuvoireMesaAgent] = {}
        for agent in sim.agents:
            mesa_agent = LuvoireMesaAgent(self, agent)
            self._agents_by_id[agent.agent_id] = mesa_agent

    def step(self) -> None:
        for event in self.luv.scheduler.due(self.luv.environment.current_time):
            self.luv.environment.record_event(event)
            self.luv.dispatcher.dispatch(event)
        self.agents.shuffle_do("step")
        self.luv.environment.advance_time(self.luv.tick_duration)
        self.current_tick += 1

    def observe(self, agent: Persona) -> EnvironmentContext:
        return self.luv.environment.get_context(agent.agent_id)

    def act(self, agent: Persona, observation: EnvironmentContext) -> Action:
        return self.luv._decide_for_agent(agent, context=observation)

    def apply(self, agent: Persona, action: Action) -> None:
        self.luv._record_action(self.current_tick, agent, action)

    def agent_state(self) -> tuple[tuple[str, str, str], ...]:
        """Compact deterministic state snapshot for tests and notebooks."""

        latest_by_agent: dict[str, tuple[str, str, str]] = {}
        for entry in self.luv.logs:
            latest_by_agent[entry.agent_id] = (
                entry.agent_id,
                entry.action.action_type,
                entry.action.location,
            )
        return tuple(latest_by_agent[key] for key in sorted(latest_by_agent))


def to_mesa_model(sim: Simulator, seed: int = 0) -> LuvoireMesaModel:
    return LuvoireMesaModel(sim, seed=seed)
