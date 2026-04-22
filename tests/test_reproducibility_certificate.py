from __future__ import annotations

from luvoire.reproducibility import (
    EMPTY_MERKLE_ROOT,
    canonical_sha256,
    generate_run_fingerprint,
    result_merkle_root,
    verification_guide_markdown,
)


def test_batch_u_reproducibility_certificate_is_stable_for_same_inputs() -> None:
    run_config = {
        "scenario": "Dorm: two agents",
        "seed": 20260421,
        "provider": "Replay only",
        "trait_vector": {"openness": 0.5, "agreeableness": 0.7},
    }
    jsonl = "\n".join(
        [
            '{"tick":0,"agent_id":"agent_1","action":{"action_type":"speak"}}',
            '{"tick":0,"agent_id":"agent_2","action":{"action_type":"observe"}}',
        ]
    )

    first = generate_run_fingerprint(
        run_config,
        jsonl,
        generated_at="2026-04-21T00:00:00+00:00",
    )
    second = generate_run_fingerprint(
        run_config,
        jsonl,
        generated_at="2026-04-21T00:00:00+00:00",
    )

    assert first == second
    assert first["input_hash"] == canonical_sha256(run_config)
    assert first["output_merkle_root"] == result_merkle_root(jsonl)
    assert first["output_merkle_root"] != EMPTY_MERKLE_ROOT
    assert first["schema_version"] == "luvoire.run_fingerprint.v1"


def test_batch_u_verification_guide_names_cli_and_merkle_root() -> None:
    certificate = generate_run_fingerprint(
        {"scenario": "Office team conflict", "seed": 1},
        '{"tick":0,"action":{"action_type":"observe"}}',
        generated_at="2026-04-21T00:00:00+00:00",
    )

    guide = verification_guide_markdown(certificate)

    assert "luvoire_verify.py" in guide
    assert str(certificate["output_merkle_root"]) in guide
