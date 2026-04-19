from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
playground_simulation = importlib.import_module("playground.simulation")


def test_subtask13_scenario_hints_read_localized_yaml_descriptions() -> None:
    dorm_config = playground_simulation.load_run_config(
        playground_simulation.scenario_path("Dorm: two agents")
    )

    assert dorm_config.description_ko is not None
    assert dorm_config.description_en is not None
    assert "룸메이트" in dorm_config.description_ko
    assert "Two roommates" in dorm_config.description_en

    korean_hint = playground_simulation.build_playground_hint(
        scenario_name="Village: ten agents",
        language="ko",
    )
    english_hint = playground_simulation.build_playground_hint(
        scenario_name="Village: ten agents",
        language="en",
    )

    assert korean_hint.startswith("**시나리오:**")
    assert "다대다 상호작용" in korean_hint
    assert english_hint.startswith("**Scenario:**")
    assert "many-to-many interaction" in english_hint


def test_subtask13_hint_renders_above_run_button_and_updates_with_language() -> None:
    app = playground_app.build_app()

    hint_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Markdown"
        and "knoema-hint" in (getattr(child, "elem_classes", None) or [])
    )
    run_button_index = next(
        index
        for index, child in enumerate(app.children)
        if type(child).__name__ == "Button" and getattr(child, "elem_id", None) == "run-button"
    )

    assert hint_index < run_button_index

    english_hint = playground_app._hint_markdown_update("School corridor", "English")
    korean_hint = playground_app._hint_markdown_update(
        "School corridor",
        playground_app.LANGUAGE_CHOICES[0],
    )
    neutral_hint = playground_simulation.build_playground_hint(
        scenario_name=None,
        language="en",
    )

    assert "Scenario" in english_hint
    assert "Students in a school corridor" in english_hint
    assert "시나리오" in korean_hint
    assert "공정한 청소 분담" in korean_hint
    assert neutral_hint == "Select a demo scenario to preview a short persistent-agent interaction flow."
