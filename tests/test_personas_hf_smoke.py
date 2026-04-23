from __future__ import annotations

import os

import pytest

from luvoire.personas import list_countries, load_country

pytestmark = pytest.mark.hf_live


@pytest.mark.skipif(
    os.getenv("LUVOIRE_HF_LIVE") != "1",
    reason="set LUVOIRE_HF_LIVE=1 to run live Hugging Face persona smoke tests",
)
def test_persona_hf_live_streams_one_row_per_country(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LUVOIRE_PERSONAS_FIXTURE_ROOT", raising=False)

    for iso in list_countries():
        persona = next(load_country(iso, limit=1))
        assert persona.country_iso == iso
        assert persona.grounding_source.startswith("nvidia/Nemotron-Personas-")
