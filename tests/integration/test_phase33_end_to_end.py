from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from knoema import Environment, LocalClient, Persona, Personality, Simulator


def _agent(agent_id: str) -> Persona:
    return Persona(
        agent_id=agent_id,
        name=agent_id.title(),
        age=19,
        background="Synthetic participant in a replayable study scene.",
        personality=Personality(0.5, 0.6, 0.4, 0.7, 0.3),
        values=["clarity"],
        goals=["keep the run reproducible"],
    )


def test_phase33_simulation_jsonl_round_trip_preserves_tick_order(tmp_path: Path) -> None:
    simulator = Simulator(
        agents=[_agent("alice"), _agent("bob")],
        environment=Environment(
            start_time=datetime(2026, 4, 18, 9, 0),
            location_path=("Korea", "Seoul", "Lab"),
        ),
        tick_duration_minutes=120,
        llm=LocalClient(
            lambda messages: (
                '{"action_type": "observe", "target": null, '
                '"content": "records a reproducible observation."}'
            )
        ),
    )
    output_path = tmp_path / "run.jsonl"

    simulator.run(duration_days=1)
    simulator.export_logs(output_path)
    records = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert len(records) == 24
    assert [record["tick"] for record in records[:4]] == [0, 0, 1, 1]
    assert records[0]["timestamp"] == "2026-04-18T09:00:00"
    assert records[-1]["timestamp"] == "2026-04-19T07:00:00"
    assert {record["agent_id"] for record in records} == {"alice", "bob"}


def test_phase33_simulator_keeps_agent_memory_buffers_separate() -> None:
    simulator = Simulator(
        agents=[_agent("alice"), _agent("bob")],
        environment=Environment(
            start_time=datetime(2026, 4, 18, 9, 0),
            location_path=("Korea", "Seoul", "Lab"),
        ),
        tick_duration_minutes=720,
    )

    simulator.run(duration_days=1)

    alice_memories = simulator.short_term_memories["alice"].recent()
    bob_memories = simulator.short_term_memories["bob"].recent()
    assert len(alice_memories) == 2
    assert len(bob_memories) == 2
    assert {memory.agent_id for memory in alice_memories} == {"alice"}
    assert {memory.agent_id for memory in bob_memories} == {"bob"}
