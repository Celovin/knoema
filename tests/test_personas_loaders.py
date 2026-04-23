from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from luvoire.cli import main
from luvoire.personas import LPIPersona, list_countries, load_country
from luvoire.personas.loaders.nemotron_base import _reset_attribution_log_for_tests

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "personas"


@pytest.fixture(autouse=True)
def use_persona_fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LUVOIRE_PERSONAS_FIXTURE_ROOT", str(FIXTURE_ROOT.resolve()))
    _reset_attribution_log_for_tests()


def test_persona_loader_registry_has_exact_seven_countries() -> None:
    assert list_countries() == ("USA", "JPN", "IND", "BRA", "SGP", "FRA", "KOR")


def test_persona_loaders_emit_lpi_for_all_countries() -> None:
    for iso in list_countries():
        personas = list(load_country(iso, limit=3, seed=7))
        assert len(personas) == 3
        assert all(isinstance(persona, LPIPersona) for persona in personas)
        assert all(persona.country_iso == iso for persona in personas)
        assert all("llm_narrative_synthetic" in persona.distortion_flags for persona in personas)


def test_persona_sampling_is_deterministic_across_processes() -> None:
    snippet = (
        "from luvoire.personas import load_country;"
        "print(next(load_country('USA', limit=100, seed=42)).persona_id)"
    )
    env = dict(os.environ)
    env["LUVOIRE_PERSONAS_FIXTURE_ROOT"] = str(FIXTURE_ROOT.resolve())

    first = subprocess.check_output([sys.executable, "-c", snippet], env=env, text=True).strip()
    second = subprocess.check_output([sys.executable, "-c", snippet], env=env, text=True).strip()

    assert first == second
    assert first.startswith("usa")


def test_persona_attribution_logs_once_per_country(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO")

    for iso in list_countries():
        next(load_country(iso, limit=1))
    first_pass = [record.message for record in caplog.records if "CC-BY-4.0" in record.message]

    for iso in list_countries():
        next(load_country(iso, limit=1))
    second_pass = [record.message for record in caplog.records if "CC-BY-4.0" in record.message]

    assert len(first_pass) == 7
    assert len(second_pass) == 7
    assert all("Nemotron-Personas" in message for message in first_pass)


def test_persona_distortion_flag_contract() -> None:
    personas = [next(load_country(iso, limit=1)) for iso in list_countries()]
    flagged = list(load_country("USA", limit=100, seed=2))

    assert all(persona.distortion_flags[0] == "llm_narrative_synthetic" for persona in personas)
    assert any("blue_shift_risk" in persona.distortion_flags for persona in flagged)


def test_personas_cli_list_sample_and_schema(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["personas", "list"]) == 0
    list_lines = capsys.readouterr().out.strip().splitlines()
    assert len(list_lines) == 7
    assert [line.split("\t")[0] for line in list_lines] == list(list_countries())

    assert main(["personas", "sample", "--country", "USA", "--n", "3", "--seed", "42"]) == 0
    sample_lines = capsys.readouterr().out.strip().splitlines()
    assert len(sample_lines) == 3
    assert all(json.loads(line)["country_iso"] == "USA" for line in sample_lines)

    schema_path = tmp_path / "lpi_schema.json"
    assert main(["personas", "schema", "--out", str(schema_path)]) == 0
    assert json.loads(schema_path.read_text(encoding="utf-8"))["title"] == "Luvoire Persona Interface v1"
