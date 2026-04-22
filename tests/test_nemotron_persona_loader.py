from __future__ import annotations

import json

from luvoire.persona.nemotron_loader import (
    EXPECTED_AGENT_ATTRIBUTE_KEYS,
    NemotronPersonaSource,
)

FORBIDDEN_ENTITY_STRINGS = (
    "Lith" + "eon",
    "Se" + "izn",
    "Ov" + "riel",
    "Fang" + "den",
    "No" + "trivo",
    "Milky" + "pix",
    "Ya" + "mi",
    "Qwen" + "3.5-35B-A3B",
)
RAW_NEMOTRON_KEYS = {
    "uuid",
    "sex",
    "district",
    "province",
    "education_level",
    "family_type",
    "housing_type",
    "marital_status",
    "military_status",
}


def test_nemotron_fixture_sampling_is_deterministic_across_runs() -> None:
    source = NemotronPersonaSource(repo_id="fixture")

    runs = [
        source.sample(n=50, seed=1234, filters={"region_contains": "Gangnam"})
        for _ in range(3)
    ]

    ids_by_run = [[str(row["uuid"]) for row in run] for run in runs]
    assert ids_by_run[0] == ids_by_run[1] == ids_by_run[2]
    assert len(ids_by_run[0]) == 50


def test_nemotron_to_agent_attributes_has_exact_public_keys() -> None:
    source = NemotronPersonaSource(repo_id="fixture")
    persona = source.sample(n=1, seed=1234, filters={"region_contains": "Gangnam"})[0]

    attributes = source.to_agent_attributes(persona)

    assert tuple(attributes) == EXPECTED_AGENT_ATTRIBUTE_KEYS
    assert RAW_NEMOTRON_KEYS.isdisjoint(attributes)
    assert attributes["persona_id"] == persona["uuid"]
    assert attributes["region"] == "서울-강남구"
    assert attributes["income_band"] == "unknown"


def test_nemotron_region_contains_filter_accepts_gangnam_alias() -> None:
    source = NemotronPersonaSource(repo_id="fixture")

    rows = source.sample(n=64, seed=20260421, filters={"region_contains": "Gangnam"})

    assert len(rows) == 64
    assert all("강남" in str(row["district"]) for row in rows)


def test_nemotron_fixture_and_mapped_output_do_not_contain_forbidden_entities() -> None:
    source = NemotronPersonaSource(repo_id="fixture")
    rows = source.sample(n=128, seed=20260421, filters={"region_contains": "Gangnam"})
    mapped = [source.to_agent_attributes(row) for row in rows]

    text = json.dumps({"rows": rows, "mapped": mapped}, ensure_ascii=False, sort_keys=True)

    assert not any(forbidden in text for forbidden in FORBIDDEN_ENTITY_STRINGS)
