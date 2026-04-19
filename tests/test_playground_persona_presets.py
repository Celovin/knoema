from __future__ import annotations

import importlib
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


def test_subtask6_persona_presets_load_twenty_five_complete_vectors() -> None:
    presets = list(playground_simulation.load_persona_presets())

    assert len(presets) == 25
    required = {
        "id",
        "label_ko",
        "label_en",
        "description_ko",
        "description_en",
        "personality",
    }
    assert len(playground_simulation.PERSONA_TRAIT_FIELDS) == 30
    for preset in presets:
        assert required <= set(preset)
        assert set(playground_simulation.PERSONA_TRAIT_FIELDS) <= set(preset["personality"])


def test_subtask6_persona_dropdown_renders_blank_plus_twenty_five_choices() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)
    persona_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "persona-preset-dropdown"
    )

    assert persona_dropdown.value == ""
    assert len(persona_dropdown.choices) == 26
    assert persona_dropdown.choices[0][1] == ""


def test_subtask6_loading_machiavellian_politician_updates_visible_sliders() -> None:
    expected = playground_simulation.persona_trait_values("machiavellian_politician")
    updates = playground_app._apply_persona_preset("machiavellian_politician")

    assert expected is not None
    assert len(updates) == 5
    assert [update["value"] for update in updates] == list(expected)
