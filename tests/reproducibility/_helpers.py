from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import datetime

from knoema.environment import Environment
from knoema.llm import LocalClient
from knoema.persona import Persona
from knoema.protocols import Message
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import Personality, WorldEvent

AGENT_IDS = ("alice", "bob", "cara")


def build_seeded_simulator(seed: int = 20260418) -> Simulator:
    environment = Environment(
        start_time=datetime(2026, 6, 1, 9, 0),
        location_path=("Knoema Demo World", "Reproducibility Lab", "Common Room"),
        conditions={"seed": seed, "weather": "clear"},
    )
    personas = [_persona(agent_id, index, seed) for index, agent_id in enumerate(AGENT_IDS)]
    for agent in personas:
        environment.set_agent_location(
            agent.agent_id,
            ("Knoema Demo World", "Reproducibility Lab", agent.name),
        )
    simulator = Simulator(
        agents=personas,
        environment=environment,
        tick_duration_minutes=360,
        llm=LocalClient(_seeded_responder(seed)),
    )
    simulator.scheduler.schedule(
        WorldEvent(
            timestamp=datetime(2026, 6, 1, 15, 0),
            event_type="lab.checkpoint",
            participants=list(AGENT_IDS),
            location="Knoema Demo World > Reproducibility Lab > Common Room",
            description=f"Seed {seed} checkpoint.",
        )
    )
    return simulator


def export_log_text(logs: Sequence[SimulationLogEntry]) -> str:
    return "\n".join(json.dumps(entry.to_json_dict(), sort_keys=True) for entry in logs) + "\n"


def canonical_memory_text(simulator: Simulator) -> str:
    payload = []
    for agent_id in sorted(simulator.short_term_memories):
        for memory in simulator.short_term_memories[agent_id].recent(50):
            payload.append(
                {
                    "agent_id": memory.agent_id,
                    "content": memory.content,
                    "importance": memory.importance,
                    "memory_type": memory.memory_type,
                    "timestamp": memory.timestamp.isoformat(),
                }
            )
    return json.dumps(payload, sort_keys=True)


def replay_summary_from_jsonl(text: str) -> dict[str, object]:
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    edges: set[tuple[str, str]] = set()
    for row in rows:
        target = row["action"]["target"]
        if target is None:
            continue
        agent_id = row["agent_id"]
        edges.add((agent_id, target))
        edges.add((target, agent_id))
    return {
        "action_count": len(rows),
        "agents": sorted({row["agent_id"] for row in rows}),
        "first_timestamp": rows[0]["timestamp"] if rows else None,
        "last_timestamp": rows[-1]["timestamp"] if rows else None,
        "relationship_edges": sorted(f"{source}->{target}" for source, target in edges),
        "ticks": sorted({row["tick"] for row in rows}),
    }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _persona(agent_id: str, index: int, seed: int) -> Persona:
    offset = (seed + index) % 7
    return Persona(
        agent_id=agent_id,
        name=agent_id.title(),
        age=24 + index,
        background=f"Synthetic reproducibility participant {index + 1}.",
        personality=Personality(
            openness=round(0.45 + offset * 0.03, 3),
            conscientiousness=round(0.50 + offset * 0.02, 3),
            extraversion=round(0.35 + offset * 0.02, 3),
            agreeableness=round(0.55 + offset * 0.02, 3),
            neuroticism=round(0.18 + offset * 0.01, 3),
        ),
        values=["repeatability", "clear logs"],
        goals=[f"preserve seed {seed}", "produce replayable behavior"],
    )


def _seeded_responder(seed: int):
    partner_map = {"alice": "bob", "bob": "cara", "cara": "alice"}

    def respond(messages: Sequence[Message]) -> str:
        system_prompt = str(messages[0].get("content", "")) if messages else ""
        user_prompt = str(messages[-1].get("content", "")) if messages else ""
        agent_id = _line_value(system_prompt, "Persona ID: ") or "alice"
        timestamp = _line_value(user_prompt, "Time: ") or "2026-06-01T00:00:00"
        hour = datetime.fromisoformat(timestamp).hour
        target = partner_map[agent_id] if hour >= 12 else None
        action_type = "coordinate" if target is not None else "observe"
        payload = {
            "action_type": action_type,
            "target": target,
            "content": f"seed={seed};agent={agent_id};hour={hour};action={action_type}",
        }
        return json.dumps(payload, sort_keys=True)

    return respond


def _line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None
