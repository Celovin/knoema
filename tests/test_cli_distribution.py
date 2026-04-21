from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from knoema.cli import main, playground_launch_payload, verify_certificate_path
from knoema.reproducibility import generate_run_fingerprint


def test_cli_list_scenarios_json(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["list-scenarios", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["count"] == 30
    assert payload["scenarios"][0] == {
        "filename": "dorm_two_agents.yaml",
        "name": "Dorm: two agents",
    }


def test_cli_playground_dry_run_json(capsys) -> None:  # type: ignore[no-untyped-def]
    exit_code = main(["playground", "--host", "0.0.0.0", "--port", "7861", "--dry-run", "--json"])

    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["url"] == "http://0.0.0.0:7861"
    assert payload["app_file"].endswith("playground\\app.py") or payload["app_file"].endswith(
        "playground/app.py"
    )


def test_cli_verify_reproducibility_certificate(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    run_config = {"scenario": "dorm_two_agents", "seed": 17}
    result_jsonl = "\n".join(
        [
            json.dumps({"agent_id": "alice", "action": "wait"}, sort_keys=True),
            json.dumps({"agent_id": "bob", "action": "observe"}, sort_keys=True),
        ]
    )
    certificate = generate_run_fingerprint(run_config, result_jsonl, generated_at="2026-04-21T00:00:00Z")
    certificate_path = tmp_path / "run_fingerprint.json"
    run_config_path = tmp_path / "run_config.json"
    result_path = tmp_path / "run.jsonl"
    certificate_path.write_text(json.dumps(certificate), encoding="utf-8")
    run_config_path.write_text(json.dumps(run_config), encoding="utf-8")
    result_path.write_text(result_jsonl, encoding="utf-8")

    report = verify_certificate_path(certificate_path, run_config_path=run_config_path, result_jsonl_path=result_path)
    exit_code = main(
        [
            "verify",
            str(certificate_path),
            "--run-config",
            str(run_config_path),
            "--result-jsonl",
            str(result_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert report.verified is True
    assert exit_code == 0
    assert payload["verified"] is True
    assert payload["checked"] == ["schema_version", "fingerprint", "input_hash", "output_merkle_root"]


def test_python_module_entry_point_supports_cli() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "knoema", "list-scenarios", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)

    assert payload["count"] == 30
    assert payload["scenarios"][-1]["filename"] == "concert_lobby_intermission.yaml"


def test_playground_launch_payload_defaults_to_localhost() -> None:
    payload = playground_launch_payload()

    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 7860
    assert payload["url"] == "http://127.0.0.1:7860"
