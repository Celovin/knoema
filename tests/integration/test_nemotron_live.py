from __future__ import annotations

import os

import pytest

from knoema.persona.nemotron_loader import DEFAULT_REPO_ID, NemotronPersonaSource

pytestmark = pytest.mark.slow


@pytest.mark.skipif(
    os.getenv("KNOEMA_ENABLE_HF_NETWORK") != "1",
    reason="live Hugging Face dataset access is opt-in",
)
def test_nemotron_live_streaming_sample_maps_to_agent_attributes() -> None:
    source = NemotronPersonaSource(
        repo_id=DEFAULT_REPO_ID,
        hf_token=os.getenv("HF_TOKEN"),
    )

    rows = source.sample(n=5, seed=20260422, filters={"region_contains": "Gangnam"})
    mapped = [source.to_agent_attributes(row) for row in rows]

    assert len(rows) == 5
    assert all("강남" in str(row.get("district", "")) for row in rows)
    assert all(attributes["region"] == "서울-강남구" for attributes in mapped)
