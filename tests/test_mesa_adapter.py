from __future__ import annotations

from datetime import datetime

import pytest

pytest.importorskip("mesa")

import luvoire
from luvoire import Environment, Persona, Personality, Simulator
from luvoire.adapters.mesa import LuvoireMesaModel, to_mesa_model


def test_mesa_adapter_smoke_steps_luvoire_state() -> None:
    simulator = _simulator(agent_count=10)
    model = to_mesa_model(simulator, seed=42)

    for _ in range(5):
        model.step()

    assert isinstance(model, LuvoireMesaModel)
    assert len(simulator.logs) == 50
    assert model.current_tick == 5
    assert simulator.environment.current_time == datetime(2026, 4, 23, 11, 30)


def test_mesa_adapter_is_deterministic_for_same_seed() -> None:
    first = to_mesa_model(_simulator(agent_count=10), seed=42)
    second = to_mesa_model(_simulator(agent_count=10), seed=42)

    first_trajectory: list[tuple[tuple[str, str, str], ...]] = []
    second_trajectory: list[tuple[tuple[str, str, str], ...]] = []
    for _ in range(20):
        first.step()
        second.step()
        first_trajectory.append(first.agent_state())
        second_trajectory.append(second.agent_state())

    assert first_trajectory == second_trajectory
    assert len(first.luv.logs) == len(second.luv.logs) == 200


def test_import_luvoire_stays_independent_of_adapter_surface() -> None:
    assert luvoire.Simulator is Simulator


def _simulator(*, agent_count: int) -> Simulator:
    return Simulator(
        agents=[_persona(index) for index in range(agent_count)],
        environment=Environment(
            start_time=datetime(2026, 4, 23, 9, 0),
            location_path=("Luvoire Demo World", "Mesa Lab"),
            conditions={"mode": "mesa-adapter-test"},
        ),
        tick_duration_minutes=30,
    )


def _persona(index: int) -> Persona:
    return Persona(
        agent_id=f"agent_{index:02d}",
        name=f"Agent {index:02d}",
        age=24 + index,
        background="Synthetic Mesa adapter test participant.",
        personality=Personality(0.55, 0.65, 0.45, 0.7, 0.35),
        values=["stability", "coordination"],
        goals=["advance the deterministic adapter test"],
    )
