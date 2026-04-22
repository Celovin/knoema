"""GitHub-backed community scenario gallery loader."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast
from urllib import request

from luvoire.dsl import loads_scenario

DEFAULT_COMMUNITY_MANIFEST_URL = (
    "https://raw.githubusercontent.com/Celovin/luvoire-scenarios/main/manifest.json"
)
_CACHE: dict[str, tuple[float, tuple[CommunityScenario, ...]]] = {}


@dataclass(frozen=True, slots=True)
class CommunityScenario:
    scenario_id: str
    title: str
    summary: str
    author: str
    tags: tuple[str, ...]
    yaml_text: str
    source_url: str = ""


def seed_community_scenarios() -> tuple[CommunityScenario, ...]:
    """Return built-in seed scenarios used when the GitHub gallery is unavailable."""

    return (
        _seed(
            "classroom_peer_review",
            "Classroom Peer Review",
            "Students negotiate feedback norms after a draft exchange.",
            "Classroom",
            "Ari",
            "patient peer reviewer",
            "Bo",
            "defensive but curious writer",
            "The instructor asks each pair to agree on one actionable revision.",
            ("education", "feedback", "classroom"),
        ),
        _seed(
            "research_lab_onboarding",
            "Research Lab Onboarding",
            "A new lab member learns handoff norms during a project transition.",
            "Research Lab",
            "Mina",
            "organized senior researcher",
            "Joon",
            "new graduate assistant",
            "A dataset handoff checklist is introduced before the next meeting.",
            ("research", "onboarding", "handoff"),
        ),
        _seed(
            "indie_studio_playtest",
            "Indie Studio Playtest",
            "A small game team triages feedback from a fictional playtest.",
            "Studio",
            "Nora",
            "producer balancing scope",
            "Kai",
            "designer advocating player clarity",
            "A playtester reports confusion about the first quest objective.",
            ("game", "playtest", "production"),
        ),
        _seed(
            "family_care_schedule",
            "Family Care Schedule",
            "Family members coordinate a weekly care schedule for an elder.",
            "Family Home",
            "Sora",
            "careful planner",
            "Dae",
            "busy sibling trying to help",
            "A calendar conflict appears during the weekly planning call.",
            ("care", "coordination", "family"),
        ),
        _seed(
            "climate_club_vote",
            "Climate Club Vote",
            "A student club chooses between two fictional outreach plans.",
            "Club Room",
            "Lina",
            "values-driven organizer",
            "Mateo",
            "pragmatic logistics lead",
            "The club receives a room booking limit before voting.",
            ("civic", "club", "decision"),
        ),
    )


def community_scenario_choices() -> list[tuple[str, str]]:
    return [(scenario.title, scenario.scenario_id) for scenario in seed_community_scenarios()]


def community_scenario_by_id(scenario_id: str) -> CommunityScenario:
    for scenario in seed_community_scenarios():
        if scenario.scenario_id == scenario_id:
            return scenario
    raise KeyError(f"unknown community scenario: {scenario_id}")


def community_gallery_markdown(scenario_id: str, language: str = "en") -> str:
    scenario = community_scenario_by_id(scenario_id)
    tags = ", ".join(scenario.tags)
    if language == "ko":
        return "\n".join(
            [
                f"### {scenario.title}",
                "",
                scenario.summary,
                "",
                f"- 작성자: {scenario.author}",
                f"- 태그: {tags}",
                "",
                "```yaml",
                scenario.yaml_text.strip(),
                "```",
            ]
        )
    return "\n".join(
        [
            f"### {scenario.title}",
            "",
            scenario.summary,
            "",
            f"- Author: {scenario.author}",
            f"- Tags: {tags}",
            "",
            "```yaml",
            scenario.yaml_text.strip(),
            "```",
        ]
    )


def load_community_manifest(
    url: str = DEFAULT_COMMUNITY_MANIFEST_URL,
    *,
    timeout_seconds: float = 5.0,
    cache_ttl_seconds: float = 3600.0,
) -> tuple[CommunityScenario, ...]:
    """Fetch and validate a GitHub-hosted community scenario manifest."""

    now = time.time()
    cached = _CACHE.get(url)
    if cached is not None and now - cached[0] < cache_ttl_seconds:
        return cached[1]
    with request.urlopen(url, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("community manifest root must be a mapping")
    scenarios = parse_community_manifest(cast("Mapping[str, Any]", payload))
    _CACHE[url] = (now, scenarios)
    return scenarios


def parse_community_manifest(payload: Mapping[str, Any]) -> tuple[CommunityScenario, ...]:
    raw_items = payload.get("scenarios", [])
    if not isinstance(raw_items, Sequence) or isinstance(raw_items, (str, bytes)):
        raise ValueError("community manifest scenarios must be a list")
    scenarios: list[CommunityScenario] = []
    for item in raw_items:
        if not isinstance(item, Mapping):
            raise ValueError("community scenario entries must be mappings")
        yaml_text = str(item.get("yaml", "")).strip()
        loads_scenario(yaml_text)
        raw_tags = item.get("tags", [])
        tags = tuple(str(tag) for tag in raw_tags) if isinstance(raw_tags, Sequence) else ()
        scenarios.append(
            CommunityScenario(
                scenario_id=str(item.get("id", "")).strip(),
                title=str(item.get("title", "")).strip(),
                summary=str(item.get("summary", "")).strip(),
                author=str(item.get("author", "community")).strip() or "community",
                tags=tags,
                yaml_text=yaml_text,
                source_url=str(item.get("source_url", "")).strip(),
            )
        )
    if any(not scenario.scenario_id or not scenario.title for scenario in scenarios):
        raise ValueError("community scenarios require id and title")
    return tuple(scenarios)


def _seed(
    scenario_id: str,
    title: str,
    summary: str,
    location: str,
    first_name: str,
    first_background: str,
    second_name: str,
    second_background: str,
    event_description: str,
    tags: tuple[str, ...],
) -> CommunityScenario:
    yaml_text = _scenario_yaml(
        scenario_id,
        title,
        summary,
        location,
        first_name,
        first_background,
        second_name,
        second_background,
        event_description,
    )
    loads_scenario(yaml_text)
    return CommunityScenario(
        scenario_id=scenario_id,
        title=title,
        summary=summary,
        author="Celovin community seed",
        tags=tags,
        yaml_text=yaml_text,
        source_url=f"{DEFAULT_COMMUNITY_MANIFEST_URL}#{scenario_id}",
    )


def _scenario_yaml(
    scenario_id: str,
    title: str,
    summary: str,
    location: str,
    first_name: str,
    first_background: str,
    second_name: str,
    second_background: str,
    event_description: str,
) -> str:
    return f"""
schema_version: "1.0"
scenario_id: {scenario_id}
title: "{title}"
domain: academic_research
description: "{summary}"
seed: 20260421
tick_duration_minutes: 30
duration_days: 1
environment:
  start_time: "2026-04-21T09:00:00"
  location_path: [Community, Gallery, "{location}"]
  conditions:
    channel: gallery
    fictional: true
agents:
  - agent_id: agent_1
    name: "{first_name}"
    age: 24
    background: "Synthetic {first_background}."
    personality:
      openness: 0.68
      conscientiousness: 0.72
      extraversion: 0.52
      agreeableness: 0.70
      neuroticism: 0.32
    values: [clarity, care]
    goals: [reach a shared plan]
    location_path: [Community, Gallery, "{location}"]
  - agent_id: agent_2
    name: "{second_name}"
    age: 26
    background: "Synthetic {second_background}."
    personality:
      openness: 0.58
      conscientiousness: 0.64
      extraversion: 0.46
      agreeableness: 0.62
      neuroticism: 0.42
    values: [fairness, reliability]
    goals: [surface constraints]
    location_path: [Community, Gallery, "{location}"]
events:
  - timestamp: "2026-04-21T09:00:00"
    event_type: community.prompt
    participants: [agent_1, agent_2]
    location: "Community > Gallery > {location}"
    description: "{event_description}"
metrics:
  - name: action_mix
    kind: count
    description: "Count safe social actions by type."
ethics:
  fictional: true
  no_real_people: true
  no_prediction: true
  no_suspect_scoring: true
  sensitive_domain: false
local_response: '{{"action_type": "speak", "target": "agent_2", "content": "proposes a safe next step."}}'
""".strip()
