from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

from scripts import build_leaderboard


def test_leaderboard_schema_requires_all_axes() -> None:
    schema = yaml.safe_load(Path("bench/schema.yaml").read_text(encoding="utf-8"))
    required_axes = schema["properties"]["results"]["required"]

    assert required_axes == [axis.axis_id for axis in build_leaderboard.AXES]


def test_leaderboard_luvoire_submission_is_generated_from_summaries() -> None:
    generated = build_leaderboard.generate_luvoire_submission()
    committed = yaml.safe_load(
        Path("bench/submissions/luvoire-0.3.0.yaml").read_text(encoding="utf-8")
    )

    assert committed == generated
    assert generated["framework"] == "Luvoire"
    assert generated["results"]["locomo"]["score"] == 1.0
    assert generated["results"]["mlmf"]["score"] == 0.875
    assert generated["results"]["htn"]["target"] == 0.85
    assert "not an audio pipeline" in generated["results"]["realtime_latency"]["caveat"]


def test_leaderboard_build_is_deterministic_and_puts_luvoire_first() -> None:
    subprocess.run([sys.executable, "scripts/build_leaderboard.py"], check=True)
    subprocess.run([sys.executable, "scripts/build_leaderboard.py", "--check"], check=True)

    leaderboard = Path("docs/bench/leaderboard.md").read_text(encoding="utf-8")
    table_rows = [line for line in leaderboard.splitlines() if line.startswith("| ")]

    assert table_rows[2].startswith("| 1 | Luvoire |")
    for axis in build_leaderboard.AXES:
        assert f"{axis.label} caveat" in table_rows[0]


def test_validate_submission_cli_accepts_luvoire_entry_and_rejects_missing_axis(
    tmp_path: Path,
) -> None:
    valid = subprocess.run(
        [sys.executable, "scripts/validate_submission.py", "bench/submissions/luvoire-0.3.0.yaml"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert valid.returncode == 0
    assert "PASS" in valid.stdout

    broken = build_leaderboard.generate_luvoire_submission()
    del broken["results"]["htn"]
    broken_path = tmp_path / "broken.yaml"
    broken_path.write_text(yaml.safe_dump(broken, sort_keys=False), encoding="utf-8")

    invalid = subprocess.run(
        [sys.executable, "scripts/validate_submission.py", str(broken_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert invalid.returncode == 1
    assert "htn" in invalid.stderr
