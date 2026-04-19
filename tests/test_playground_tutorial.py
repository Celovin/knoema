from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask28_tutorial_declares_eight_steps_per_language() -> None:
    assert playground_app.TUTORIAL_STORAGE_KEY == "knoema_tutorial_completed"
    assert len(playground_app.TUTORIAL_STEPS["ko"]) == 8
    assert len(playground_app.TUTORIAL_STEPS["en"]) == 8
    assert playground_app.TUTORIAL_STEPS["ko"][0]["selector"] == "#scenario-dropdown"
    assert playground_app.TUTORIAL_STEPS["en"][-1]["selector"] == "#export-panel"
    assert "localStorage" in playground_app.TUTORIAL_HEAD
    assert "data-tour-action" in playground_app.TUTORIAL_HEAD


def test_subtask28_build_app_exposes_tutorial_targets() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "tutorial-button"
    )
    scenario_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "scenario-dropdown"
    )
    environment_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "environment-preset"
    )
    extended_panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "extended-personality-panel"
    )
    export_panel = next(
        component
        for component in components
        if getattr(component, "elem_id", None) == "export-panel"
    )

    assert button.value == "?"
    assert scenario_dropdown.label == playground_app.LABELS["ko"]["scenario"]
    assert environment_dropdown.label == playground_app.LABELS["ko"]["environment"]
    assert extended_panel.label == playground_app.LABELS["ko"]["extended_panel"]
    assert export_panel.elem_id == "export-panel"
