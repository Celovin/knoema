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


def _language_state_values() -> tuple[object, ...]:
    values: list[object] = []
    questionnaire_defaults = playground_app.questionnaire_default_responses()
    for slot_index in range(playground_app.AGENT_EDITOR_SLOT_COUNT):
        personality = dict(playground_app.PERSONA_TRAIT_DEFAULTS)
        responses = dict(questionnaire_defaults)
        name = f"Agent {slot_index + 1}"
        age = 24 + slot_index
        routine_text = ""
        mode = playground_app.QUESTIONNAIRE_MODE_SLIDERS
        persona_preset = ""
        routine_preset = "free"
        if slot_index == 0:
            personality["openness"] = 0.91
            personality["honesty_humility"] = 0.87
            responses["q01"] = 5
            name = "Edited Mina"
            age = 31
            routine_text = "- start_hour: 9"
            mode = playground_app.QUESTIONNAIRE_MODE_HEXACO
            persona_preset = "empathetic_mediator"
            routine_preset = "shopkeeper"
        values.extend(
            [
                persona_preset,
                routine_preset,
                name,
                age,
                routine_text,
                mode,
                *[personality[field_name] for field_name in playground_app.PERSONA_TRAIT_FIELDS],
                *[responses[item.item_id] for item in playground_app.HEXACO_QUESTIONNAIRE_ITEMS],
            ]
        )
    return tuple(values)


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


def test_language_updates_preserve_agent_editor_values() -> None:
    current_responses = playground_app.questionnaire_default_responses()
    current_responses["q01"] = 5
    english_updates = playground_app._language_updates(
        "English",
        playground_app.LABELS["ko"]["replay"],
        None,
        None,
        None,
        None,
        3,
        False,
        3,
        False,
        10,
        20260419,
        False,
        "Auto",
        False,
        False,
        "independent_t",
        0.5,
        0.05,
        0.8,
        128.0,
        *_language_state_values(),
    )

    assert _find_label_update(english_updates, "Name")["value"] == "Edited Mina"
    assert _find_label_update(english_updates, "Openness")["value"] == 0.91
    assert _find_label_update(english_updates, "Q01")["value"] == 5
    assert any(
        update
        == playground_app.questionnaire_summary_markdown(
            playground_app.score_hexaco_questionnaire(current_responses),
            "en",
        )
        for update in english_updates
    )
