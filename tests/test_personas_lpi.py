from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from luvoire.personas import LPIPersona, lpi_json_schema

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "personas"
LPI_FIELDS = (
    "persona_id",
    "country_iso",
    "language_locale",
    "age",
    "sex",
    "region_l1",
    "region_l2",
    "education_isced",
    "occupation_isco08",
    "income_bracket_oecd",
    "household_size",
    "marital_status",
    "big5",
    "narrative_text",
    "grounding_source",
    "grounding_version",
    "distortion_flags",
    "extras",
)


def test_lpi_dataclass_round_trips_twenty_persona_golden_fixture() -> None:
    payload = json.loads((FIXTURE_DIR / "lpi_golden.json").read_text(encoding="utf-8"))

    assert len(payload) == 20
    assert {row["country_iso"] for row in payload} == {"USA", "JPN", "IND", "BRA", "SGP", "FRA", "KOR"}
    for row in payload:
        persona = LPIPersona.from_dict(row)
        assert tuple(persona.to_dict()) == LPI_FIELDS
        assert persona.to_dict() == row


def test_lpi_schema_file_matches_introspection_and_validates_golden_fixture() -> None:
    schema = lpi_json_schema()
    committed_schema = json.loads(
        Path("src/luvoire/personas/lpi_schema.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema)
    payload = json.loads((FIXTURE_DIR / "lpi_golden.json").read_text(encoding="utf-8"))

    assert committed_schema == schema
    for row in payload:
        validator.validate(row)
