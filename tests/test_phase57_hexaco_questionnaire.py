from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
hexaco_questionnaire = importlib.import_module("playground.hexaco_questionnaire")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask57_inventory_covers_sixty_items_across_six_domains() -> None:
    items = hexaco_questionnaire.HEXACO_QUESTIONNAIRE_ITEMS
    defaults = hexaco_questionnaire.questionnaire_default_responses()
    domain_counts = hexaco_questionnaire.questionnaire_domain_counts()

    assert len(items) == 60
    assert set(domain_counts) == set(hexaco_questionnaire.HEXACO_DOMAINS)
    assert all(count == 10 for count in domain_counts.values())
    assert set(defaults) == {item.item_id for item in items}
    assert all(value == hexaco_questionnaire.QUESTIONNAIRE_RESPONSE_DEFAULT for value in defaults.values())


def test_subtask57_scoring_projects_hexaco_answers_into_thirty_trait_vector() -> None:
    responses = hexaco_questionnaire.questionnaire_default_responses()
    for item in hexaco_questionnaire.questionnaire_domain_items("honesty_humility"):
        responses[item.item_id] = 1 if item.reverse_scored else 5
    for item in hexaco_questionnaire.questionnaire_domain_items("agreeableness"):
        responses[item.item_id] = 1 if item.reverse_scored else 5

    scores = hexaco_questionnaire.score_hexaco_questionnaire(responses)
    overrides = hexaco_questionnaire.derive_personality_from_questionnaire(responses)

    assert scores["honesty_humility"] > 0.9
    assert scores["agreeableness"] > 0.9
    assert overrides["honesty_humility"] > 0.9
    assert overrides["fairness"] > 0.9
    assert overrides["machiavellianism"] < 0.2
    assert set(overrides) == set(playground_app.PERSONA_TRAIT_FIELDS)


def test_subtask57_build_app_exposes_questionnaire_mode_and_sixty_likert_items() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    questionnaire_panel = next(
        component
        for component in components
        if getattr(component, "elem_id", None) == "hexaco-questionnaire-panel"
    )
    questionnaire_mode = next(
        component
        for component in components
        if getattr(component, "elem_id", None) == "personality-input-mode"
    )
    question_sliders = [
        component
        for component in components
        if type(component).__name__ == "Slider"
        and isinstance(getattr(component, "elem_id", None), str)
        and getattr(component, "elem_id", "").startswith("hexaco-item-q")
        and not getattr(component, "elem_id", "").endswith("-2")
        and not getattr(component, "elem_id", "").endswith("-3")
    ]

    assert questionnaire_panel.visible is False
    assert questionnaire_mode.value == hexaco_questionnaire.QUESTIONNAIRE_MODE_SLIDERS
    assert len(question_sliders) == 60


def test_subtask57_questionnaire_mode_auto_projects_answers_into_trait_updates() -> None:
    responses = hexaco_questionnaire.questionnaire_default_responses()
    for item in hexaco_questionnaire.questionnaire_domain_items("honesty_humility"):
        responses[item.item_id] = 1 if item.reverse_scored else 5

    updates = playground_app._questionnaire_mode_updates(
        hexaco_questionnaire.QUESTIONNAIRE_MODE_HEXACO,
        "English",
        *[responses[item.item_id] for item in hexaco_questionnaire.HEXACO_QUESTIONNAIRE_ITEMS],
    )

    panel_update = updates[0]
    trait_values = updates[1:-1]
    summary = updates[-1]

    assert panel_update["visible"] is True
    assert panel_update["open"] is True
    assert trait_values[playground_app.PERSONA_TRAIT_FIELDS.index("honesty_humility")] > 0.9
    assert trait_values[playground_app.PERSONA_TRAIT_FIELDS.index("machiavellianism")] < 0.2
    assert "HEXACO summary" in summary
