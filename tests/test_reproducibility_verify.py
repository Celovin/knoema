from __future__ import annotations

import json
import sys
from pathlib import Path

from luvoire.reproducibility import generate_run_fingerprint, verify_run_fingerprint

sys.path.insert(0, str(Path.cwd()))
from scripts import luvoire_verify


def test_batch_u_verify_rejects_tampered_result() -> None:
    run_config = {"scenario": "Village: ten agents", "seed": 20260421}
    jsonl = '{"tick":0,"agent_id":"agent_1","action":{"action_type":"observe"}}'
    certificate = generate_run_fingerprint(
        run_config,
        jsonl,
        generated_at="2026-04-21T00:00:00+00:00",
    )

    ok_report = verify_run_fingerprint(certificate, run_config=run_config, result=jsonl)
    tampered_report = verify_run_fingerprint(
        certificate,
        run_config=run_config,
        result='{"tick":0,"agent_id":"agent_1","action":{"action_type":"deceive"}}',
    )

    assert ok_report.verified
    assert not tampered_report.verified
    assert "output_merkle_root" in tampered_report.mismatches


def test_batch_u_luvoire_verify_cli_exit_codes(tmp_path: Path) -> None:
    run_config = {"scenario": "Office team conflict", "seed": 7}
    jsonl = '{"tick":0,"agent_id":"agent_1","action":{"action_type":"speak"}}'
    certificate = generate_run_fingerprint(
        run_config,
        jsonl,
        generated_at="2026-04-21T00:00:00+00:00",
    )
    certificate_path = tmp_path / "run_fingerprint.json"
    result_path = tmp_path / "run.jsonl"
    tampered_path = tmp_path / "tampered.jsonl"
    certificate_path.write_text(json.dumps(certificate), encoding="utf-8")
    result_path.write_text(jsonl, encoding="utf-8")
    tampered_path.write_text(
        '{"tick":0,"agent_id":"agent_1","action":{"action_type":"attack"}}',
        encoding="utf-8",
    )

    assert luvoire_verify.main([str(certificate_path), "--result-jsonl", str(result_path)]) == 0
    assert luvoire_verify.main([str(certificate_path), "--result-jsonl", str(tampered_path)]) == 1
