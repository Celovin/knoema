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


def test_subtask26_cultural_priors_load_five_modules_with_expected_ids() -> None:
    priors = list(playground_simulation.load_cultural_priors())

    assert [prior["id"] for prior in priors] == [
        "confucian_korean",
        "western_individualist",
        "islamic_communitarian",
        "latin_american",
        "nordic_egalitarian",
    ]


def test_subtask26_cultural_prior_trait_values_shift_neutral_defaults_and_reset_on_none() -> None:
    fields = playground_simulation.PERSONA_TRAIT_FIELDS
    confucian_values = dict(
        zip(
            fields,
            playground_simulation.cultural_prior_trait_values("confucian_korean", fields),
            strict=True,
        )
    )
    neutral_values = dict(
        zip(
            fields,
            playground_simulation.cultural_prior_trait_values(None, fields),
            strict=True,
        )
    )

    assert confucian_values["binding_morals"] == 0.7
    assert confucian_values["conformity"] == 0.7
    assert confucian_values["tradition"] == 0.7
    assert confucian_values["self_direction"] == 0.3
    assert confucian_values["hedonism"] == 0.3
    assert neutral_values == playground_simulation.PERSONA_TRAIT_DEFAULTS


def test_subtask26_build_app_exposes_cultural_prior_dropdown_and_prior_then_preset_override() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)
    cultural_prior_dropdown = next(
        component
        for component in components
        if type(component).__name__ == "Dropdown"
        and getattr(component, "elem_id", None) == "cultural-prior-dropdown"
    )

    assert cultural_prior_dropdown.value == ""
    assert len(cultural_prior_dropdown.choices) == 6
    assert cultural_prior_dropdown.choices[0][1] == ""

    prior_updates = playground_app._apply_cultural_prior("confucian_korean")
    preset_updates = playground_app._apply_persona_preset("friendly_student")
    tradition_index = playground_simulation.PERSONA_TRAIT_FIELDS.index("tradition")

    assert len(prior_updates) == 30
    assert prior_updates[tradition_index]["value"] == 0.7
    assert len(preset_updates) == 30
    assert (
        preset_updates[tradition_index]["value"]
        == playground_simulation.persona_trait_values(
            "friendly_student",
            playground_simulation.PERSONA_TRAIT_FIELDS,
        )[tradition_index]
    )
    assert preset_updates[tradition_index]["value"] != prior_updates[tradition_index]["value"]
