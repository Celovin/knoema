from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask4_environment_presets_load_and_cover_twenty_five_entries() -> None:
    presets = list(playground_simulation.load_environment_presets())

    assert len(presets) == 25
    required = {
        "id",
        "label_ko",
        "label_en",
        "location_path",
        "start_time",
        "conditions",
        "crowding",
        "notes_ko",
        "notes_en",
    }
    for preset in presets:
        assert required <= set(preset)


def test_subtask4_environment_choices_localize_labels_and_keep_ids() -> None:
    ko_choices = playground_simulation.environment_choices("ko")
    en_choices = playground_simulation.environment_choices("en")

    assert len(ko_choices) == 25
    assert len(en_choices) == 25
    assert ko_choices[0][1] == "university_dorm_evening"
    assert en_choices[0][1] == "university_dorm_evening"
    assert "허구" in next(label for label, value in ko_choices if value == "hospital_er_night")
    assert "fictional research only" in next(
        label for label, value in en_choices if value == "prison_yard_recess"
    )


def test_subtask4_environment_dropdown_and_runtime_override_work() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)
    environment_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "environment-preset"
    )

    assert environment_dropdown.value == "university_dorm_evening"
    assert len(environment_dropdown.choices) == 25

    result = playground_simulation.run_playground_scenario(
        scenario_name="Dorm: two agents",
        environment_preset_id="subway_rush_hour",
        provider="Replay only",
        api_key="",
        model="",
        primary_name="Preset Mina",
        primary_age=22,
        openness=0.7,
        conscientiousness=0.6,
        extraversion=0.5,
        agreeableness=0.7,
        neuroticism=0.3,
        ticks=1,
    )

    first_row = json.loads(result.jsonl.splitlines()[0])
    assert first_row["timestamp"].startswith("2026-04-20T08:10:00")
    assert "Dense public setting" in playground_simulation.environment_note("subway_rush_hour", "en")
