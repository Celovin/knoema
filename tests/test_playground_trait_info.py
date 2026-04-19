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


def _find_label_update(updates: list[object], label: str) -> dict[str, object]:
    return next(
        update
        for update in updates
        if isinstance(update, dict) and update.get("label") == label
    )


def test_subtask3_big_five_sliders_render_with_inline_help() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)
    sliders = {
        component.label: component
        for component in components
        if type(component).__name__ == "Slider" and getattr(component, "label", None)
    }

    assert sliders[playground_app.LABELS["ko"]["openness"]].info == playground_app.LABELS["ko"]["openness_info"]
    assert (
        sliders[playground_app.LABELS["ko"]["conscientiousness"]].info
        == playground_app.LABELS["ko"]["conscientiousness_info"]
    )
    assert sliders[playground_app.LABELS["ko"]["extraversion"]].info == playground_app.LABELS["ko"]["extraversion_info"]
    assert (
        sliders[playground_app.LABELS["ko"]["agreeableness"]].info
        == playground_app.LABELS["ko"]["agreeableness_info"]
    )
    assert sliders[playground_app.LABELS["ko"]["neuroticism"]].info == playground_app.LABELS["ko"]["neuroticism_info"]


def test_subtask3_language_updates_big_five_labels_and_info() -> None:
    english_updates = playground_app._language_updates("English", playground_app.LABELS["ko"]["replay"])

    assert _find_label_update(english_updates, "Openness")["info"] == playground_app.LABELS["en"]["openness_info"]
    assert (
        _find_label_update(english_updates, "Conscientiousness")["info"]
        == playground_app.LABELS["en"]["conscientiousness_info"]
    )
    assert _find_label_update(english_updates, "Extraversion")["info"] == playground_app.LABELS["en"]["extraversion_info"]
    assert (
        _find_label_update(english_updates, "Agreeableness")["info"]
        == playground_app.LABELS["en"]["agreeableness_info"]
    )
    assert (
        _find_label_update(english_updates, "Emotional volatility (Neuroticism)")["info"]
        == playground_app.LABELS["en"]["neuroticism_info"]
    )

    korean_updates = playground_app._language_updates(playground_app.LANGUAGE_CHOICES[0], "Replay only")
    assert (
        _find_label_update(korean_updates, playground_app.LABELS["ko"]["neuroticism"])["info"]
        == playground_app.LABELS["ko"]["neuroticism_info"]
    )
