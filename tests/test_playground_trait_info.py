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


def test_subtask3_big_five_sliders_render_with_inline_help() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)
    sliders = {
        component.label: component
        for component in components
        if type(component).__name__ == "Slider" and getattr(component, "label", None)
    }

    assert sliders["개방성"].info == playground_app.LABELS["ko"]["openness_info"]
    assert sliders["성실성"].info == playground_app.LABELS["ko"]["conscientiousness_info"]
    assert sliders["외향성"].info == playground_app.LABELS["ko"]["extraversion_info"]
    assert sliders["친화성"].info == playground_app.LABELS["ko"]["agreeableness_info"]
    assert sliders["정서 불안정성"].info == playground_app.LABELS["ko"]["neuroticism_info"]


def test_subtask3_language_updates_big_five_labels_and_info() -> None:
    english_updates = playground_app._language_updates("English", "재생 전용")

    assert english_updates[8]["label"] == "Openness"
    assert english_updates[8]["info"] == playground_app.LABELS["en"]["openness_info"]
    assert english_updates[9]["label"] == "Conscientiousness"
    assert english_updates[9]["info"] == playground_app.LABELS["en"]["conscientiousness_info"]
    assert english_updates[10]["label"] == "Extraversion"
    assert english_updates[10]["info"] == playground_app.LABELS["en"]["extraversion_info"]
    assert english_updates[11]["label"] == "Agreeableness"
    assert english_updates[11]["info"] == playground_app.LABELS["en"]["agreeableness_info"]
    assert english_updates[12]["label"] == "Emotional volatility (Neuroticism)"
    assert english_updates[12]["info"] == playground_app.LABELS["en"]["neuroticism_info"]

    korean_updates = playground_app._language_updates("한국어", "Replay only")
    assert korean_updates[12]["label"] == "정서 불안정성"
    assert korean_updates[12]["info"] == playground_app.LABELS["ko"]["neuroticism_info"]
