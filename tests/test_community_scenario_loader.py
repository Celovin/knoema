from __future__ import annotations

import importlib
import sys
from pathlib import Path

from knoema.community import (
    community_gallery_markdown,
    community_scenario_by_id,
    community_scenario_choices,
    parse_community_manifest,
    seed_community_scenarios,
)

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_batch_r_seed_gallery_exposes_five_scenarios() -> None:
    seeds = seed_community_scenarios()
    choices = community_scenario_choices()

    assert len(seeds) >= 5
    assert choices[0][1] == seeds[0].scenario_id
    assert community_scenario_by_id(seeds[0].scenario_id).yaml_text
    assert "```yaml" in community_gallery_markdown(seeds[0].scenario_id)


def test_batch_r_manifest_parser_validates_yaml_payloads() -> None:
    seed = seed_community_scenarios()[0]
    parsed = parse_community_manifest(
        {
            "scenarios": [
                {
                    "id": "external_classroom",
                    "title": "External Classroom",
                    "summary": "External manifest entry.",
                    "author": "tester",
                    "tags": ["education"],
                    "yaml": seed.yaml_text.replace(seed.scenario_id, "external_classroom"),
                }
            ]
        }
    )

    assert len(parsed) == 1
    assert parsed[0].scenario_id == "external_classroom"
    assert parsed[0].tags == ("education",)


def test_batch_r_playground_exposes_community_gallery_panel() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    panel = next(
        component
        for component in components
        if getattr(component, "elem_id", None) == "community-gallery-panel"
    )
    dropdown = next(
        component
        for component in components
        if getattr(component, "elem_id", None) == "community-gallery-scenario"
    )
    load_button = next(
        component
        for component in components
        if getattr(component, "elem_id", None) == "community-gallery-load"
    )

    assert panel.label == playground_app.LABELS["ko"]["community_gallery_panel"]
    assert dropdown.label == playground_app.LABELS["ko"]["community_gallery_scenario"]
    assert load_button.value == playground_app.LABELS["ko"]["community_gallery_load"]


def test_batch_r_playground_loads_seed_into_agent_controls() -> None:
    outputs = playground_app._community_scenario_updates("classroom_peer_review", "English")

    assert outputs[0]["value"] == 2
    assert outputs[1]["value"] == "Ari"
    assert "community.prompt" in outputs[-3]["value"]
    assert "Classroom Peer Review" in outputs[-1]["value"]
