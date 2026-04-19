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


def _find_label_update(updates: list[object], label: str) -> dict[str, object]:
    return next(
        update
        for update in updates
        if isinstance(update, dict) and update.get("label") == label
    )


def test_subtask5_build_app_renders_tiered_extended_personality_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    accordions = {
        getattr(component, "elem_id", None): component
        for component in components
        if type(component).__name__ == "Accordion"
    }
    sliders = {
        component.label: component
        for component in components
        if type(component).__name__ == "Slider" and getattr(component, "label", None)
    }
    markdown_values = [
        getattr(component, "value", None)
        for component in components
        if type(component).__name__ == "Markdown"
    ]

    assert accordions["tier-a-panel"].open is True
    assert accordions["extended-personality-panel"].open is True
    assert accordions["tier-bd-panel"].open is False
    assert accordions["tier-c-panel"].open is False
    assert accordions["tier-e-panel"].open is False
    assert accordions["tier-f-panel"].open is False
    assert accordions["tier-g-panel"].open is False

    assert playground_app.LABELS["ko"]["dark_tetrad_notice"] in markdown_values

    for field_name in playground_simulation.PERSONA_TRAIT_FIELDS:
        label = playground_app.LABELS["ko"][field_name]
        slider = sliders[label]
        assert slider.info == playground_app.LABELS["ko"][f"{field_name}_info"]
        assert slider.value == playground_simulation.PERSONA_TRAIT_DEFAULTS[field_name]


def test_subtask5_language_updates_cover_extended_tiers_and_dark_tetrad_labels() -> None:
    english_updates = playground_app._language_updates(
        "English",
        playground_app.LABELS["ko"]["replay"],
        "Dorm: two agents",
        playground_app._default_environment_id(),
        "machiavellian_politician",
    )

    assert (
        _find_label_update(english_updates, playground_app.LABELS["en"]["tier_c_panel"])["label"]
        == playground_app.LABELS["en"]["tier_c_panel"]
    )
    assert (
        _find_label_update(
            english_updates,
            playground_app.LABELS["en"]["machiavellianism"],
        )["info"]
        == playground_app.LABELS["en"]["machiavellianism_info"]
    )
    assert (
        _find_label_update(
            english_updates,
            playground_app.LABELS["en"]["universalism"],
        )["info"]
        == playground_app.LABELS["en"]["universalism_info"]
    )
