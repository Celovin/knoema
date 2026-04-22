"""Shared command parsing and deterministic scenario runs for chat bots."""

from __future__ import annotations

import json
import shlex
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from luvoire.cli import PLAYGROUND_SCENARIOS
from luvoire.environment import Environment
from luvoire.llm import LocalClient
from luvoire.persona import Persona
from luvoire.simulator import Simulator
from luvoire.types import Personality

DEFAULT_TICKS = 4
MAX_TICKS = 12


@dataclass(frozen=True, slots=True)
class BotCommand:
    action: str
    scenario: str
    ticks: int


@dataclass(frozen=True, slots=True)
class BotRunSummary:
    scenario: str
    ticks: int
    agent_count: int
    action_counts: dict[str, int]
    jsonl: str
    markdown: str


def parse_bot_command(text: str) -> BotCommand:
    """Parse `!luvoire run <scenario> [--ticks N]` or slash-command text."""

    tokens = shlex.split(text.strip())
    if tokens and tokens[0].lower() in {"!luvoire", "/luvoire", "luvoire"}:
        tokens = tokens[1:]
    if not tokens:
        raise ValueError("usage: !luvoire run <scenario> [--ticks N]")
    action = tokens[0].lower()
    if action != "run":
        raise ValueError("only the run action is supported")

    ticks = DEFAULT_TICKS
    scenario_parts: list[str] = []
    index = 1
    while index < len(tokens):
        token = tokens[index]
        if token == "--ticks":
            if index + 1 >= len(tokens):
                raise ValueError("--ticks requires an integer value")
            ticks = _clamp_ticks(int(tokens[index + 1]))
            index += 2
            continue
        scenario_parts.append(token)
        index += 1
    scenario = " ".join(scenario_parts).strip()
    if not scenario:
        raise ValueError("scenario is required")
    return BotCommand(action=action, scenario=scenario, ticks=ticks)


def run_scenario_for_bot(scenario: str, ticks: int = DEFAULT_TICKS) -> BotRunSummary:
    """Run a small deterministic scenario suitable for a chat response."""

    resolved = _resolve_scenario_name(scenario)
    tick_count = _clamp_ticks(ticks)
    environment = Environment(
        start_time=datetime(2026, 4, 21, 9, 0, 0),
        location_path=("Luvoire", "Chat", resolved),
        conditions={"channel": "bot", "scenario": resolved},
    )
    agents = _bot_personas()
    for agent in agents:
        environment.set_agent_location(agent.agent_id, environment.location_path)
    response = _response_factory(resolved)
    simulator = Simulator(
        agents=agents,
        environment=environment,
        tick_duration_minutes=15,
        llm=LocalClient(response),
    )
    simulator.run_ticks(tick_count)
    jsonl = "\n".join(
        json.dumps(entry.to_json_dict(), ensure_ascii=False, sort_keys=True)
        for entry in simulator.logs
    )
    if jsonl:
        jsonl += "\n"
    action_counts = Counter(entry.action.action_type for entry in simulator.logs)
    counts = dict(sorted(action_counts.items()))
    markdown = _summary_markdown(resolved, tick_count, len(agents), counts)
    return BotRunSummary(
        scenario=resolved,
        ticks=tick_count,
        agent_count=len(agents),
        action_counts=counts,
        jsonl=jsonl,
        markdown=markdown,
    )


def format_discord_embed(summary: BotRunSummary) -> dict[str, Any]:
    """Return a Discord embed payload without requiring discord.py."""

    action_mix = ", ".join(f"{key}: {value}" for key, value in summary.action_counts.items())
    return {
        "title": f"Luvoire run: {summary.scenario}",
        "description": summary.markdown,
        "color": 0x2F855A,
        "fields": [
            {"name": "Ticks", "value": str(summary.ticks), "inline": True},
            {"name": "Agents", "value": str(summary.agent_count), "inline": True},
            {"name": "Action mix", "value": action_mix or "none", "inline": False},
        ],
    }


def format_slack_blocks(summary: BotRunSummary) -> list[dict[str, Any]]:
    """Return Slack Block Kit blocks without requiring slack-bolt."""

    action_mix = ", ".join(f"{key}: {value}" for key, value in summary.action_counts.items())
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Luvoire run: {summary.scenario}"},
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": summary.markdown}},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Ticks:* {summary.ticks}  *Agents:* {summary.agent_count}  *Actions:* {action_mix or 'none'}",
                }
            ],
        },
    ]


def _resolve_scenario_name(value: str) -> str:
    normalized = value.strip().lower().replace("_", " ")
    scenarios = [scenario["name"] for scenario in PLAYGROUND_SCENARIOS]
    for scenario in scenarios:
        if scenario.lower() == normalized:
            return scenario
    for scenario in scenarios:
        if normalized in scenario.lower() or scenario.lower().replace(":", "") in normalized:
            return scenario
    raise ValueError(f"unknown scenario: {value}")


def _clamp_ticks(value: int) -> int:
    return max(1, min(MAX_TICKS, value))


def _bot_personas() -> list[Persona]:
    base = {
        "openness": 0.65,
        "conscientiousness": 0.7,
        "extraversion": 0.55,
        "agreeableness": 0.68,
        "neuroticism": 0.35,
    }
    return [
        Persona(
            agent_id="mina",
            name="Mina",
            age=24,
            background="Luvoire chat demo agent.",
            personality=Personality(**base),
            values=["clarity", "coordination"],
            goals=["summarize the situation"],
        ),
        Persona(
            agent_id="joon",
            name="Joon",
            age=26,
            background="Luvoire chat demo partner.",
            personality=Personality(**{**base, "extraversion": 0.45, "agreeableness": 0.72}),
            values=["reliability", "care"],
            goals=["respond constructively"],
        ),
    ]


def _response_factory(scenario: str) -> Any:
    action_cycle = ("observe", "speak", "offer", "comfort")
    counter = {"index": 0}

    def respond(messages: list[dict[str, str]]) -> str:
        system_prompt = messages[0]["content"] if messages else ""
        agent_id = _line_value(system_prompt, "Persona ID: ") or "mina"
        action_type = action_cycle[counter["index"] % len(action_cycle)]
        counter["index"] += 1
        target: str | None = "joon" if agent_id == "mina" else "mina"
        if action_type == "observe":
            target = None
        payload = {
            "action_type": action_type,
            "target": target,
            "content": f"{agent_id} handles {scenario} with {action_type}.",
        }
        return json.dumps(payload, ensure_ascii=False)

    return respond


def _line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _summary_markdown(
    scenario: str,
    ticks: int,
    agent_count: int,
    action_counts: dict[str, int],
) -> str:
    action_mix = ", ".join(f"{key}={value}" for key, value in action_counts.items())
    return "\n".join(
        [
            f"**Scenario:** {scenario}",
            f"**Ticks:** {ticks}",
            f"**Agents:** {agent_count}",
            f"**Action mix:** {action_mix or 'none'}",
        ]
    )
