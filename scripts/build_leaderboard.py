"""Build the Knoema Bench public leaderboard from YAML submissions."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
BENCH_DIR = ROOT / "bench"
SUBMISSIONS_DIR = BENCH_DIR / "submissions"
SCHEMA_PATH = BENCH_DIR / "schema.yaml"
LEADERBOARD_PATH = ROOT / "docs" / "bench" / "leaderboard.md"
KNOEMA_SUBMISSION_PATH = SUBMISSIONS_DIR / "knoema-0.2.0.yaml"
KNOEMA_VERSION = "0.2.0"


@dataclass(frozen=True)
class AxisDefinition:
    axis_id: str
    label: str
    target_label: str
    higher_is_better: bool = True


AXES: tuple[AxisDefinition, ...] = (
    AxisDefinition("locomo", "LoCoMo", "score >= 0.80"),
    AxisDefinition("memoryagentbench", "MemoryAgentBench", "score >= 0.80"),
    AxisDefinition("memoryarena", "MemoryArena", "score >= 0.60"),
    AxisDefinition("mlmf", "MLMF retention", "retention >= published baseline"),
    AxisDefinition("theory_of_mind", "ToM Sally-Anne", "accuracy >= 0.80"),
    AxisDefinition("htn", "HTN planning", "depth-3 goal achievement >= 0.85"),
    AxisDefinition("realtime_latency", "Real-time latency", "normalized score >= 1.00"),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated Knoema submission or leaderboard differs from disk.",
    )
    args = parser.parse_args(argv)

    SUBMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    LEADERBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)

    generated_submission = generate_knoema_submission()
    generated_leaderboard = render_leaderboard(load_all_submissions(generated_submission))

    if args.check:
        failures: list[str] = []
        if KNOEMA_SUBMISSION_PATH.read_text(encoding="utf-8") != dump_yaml(generated_submission):
            failures.append(str(KNOEMA_SUBMISSION_PATH))
        if LEADERBOARD_PATH.read_text(encoding="utf-8") != generated_leaderboard:
            failures.append(str(LEADERBOARD_PATH))
        if failures:
            print("leaderboard artifacts are stale:", ", ".join(failures), file=sys.stderr)
            return 1
        print("leaderboard artifacts are current")
        return 0

    KNOEMA_SUBMISSION_PATH.write_text(dump_yaml(generated_submission), encoding="utf-8")
    LEADERBOARD_PATH.write_text(generated_leaderboard, encoding="utf-8")
    print(f"wrote {KNOEMA_SUBMISSION_PATH}")
    print(f"wrote {LEADERBOARD_PATH}")
    return 0


def generate_knoema_submission() -> dict[str, Any]:
    memory = load_json(ROOT / "benchmarks" / "memory_benchmark_integration" / "results" / "summary.json")
    mlmf = load_json(ROOT / "experiments" / "mlmf_retention_benchmark" / "results" / "summary.json")
    tom = load_json(ROOT / "experiments" / "theory_of_mind_ablation" / "results" / "summary.json")
    htn = load_json(ROOT / "experiments" / "planning_depth" / "results" / "summary.json")
    latency = load_json(ROOT / "benchmarks" / "formal_report" / "results" / "latency_comparison.json")

    memory_rows = {row["benchmark_id"]: row for row in memory["rows"]}
    htn_depth_three = htn["results"]["3"]
    replay_latency = next(
        row for row in latency["measured_rows"] if row["path_id"] == "playground_replay"
    )
    latency_target_ms = min(row["latency_ms_high"] for row in latency["published_rows"])
    normalized_latency_score = min(1.0, latency_target_ms / replay_latency["mean_tick_latency_ms"])

    return {
        "framework": "Knoema Engine",
        "version": KNOEMA_VERSION,
        "date": "2026-04-21",
        "contact": "hello@celovin.com",
        "repository": "https://github.com/Celovin/knoema",
        "results": {
            "locomo": memory_result(
                memory_rows["locomo"],
                caveat="synthetic local proxy inspired by LoCoMo; not an official LoCoMo submission",
            ),
            "memoryagentbench": memory_result(
                memory_rows["memoryagentbench"],
                caveat=(
                    "synthetic EventQA and FactConsolidation proxy; not an official "
                    "MemoryAgentBench submission"
                ),
            ),
            "memoryarena": memory_result(
                memory_rows["memoryarena"],
                caveat=(
                    "synthetic decision-relevant memory proxy over SQLite and FAISS retrieval; "
                    "not an official MemoryArena submission"
                ),
            ),
            "mlmf": {
                "score": round(float(mlmf["measured_retention"]), 3),
                "target": round(float(mlmf["target_retention"]), 3),
                "caveat": (
                    "deterministic synthetic long-horizon retention harness; target is the "
                    "committed published-baseline field"
                ),
                "source": "experiments/mlmf_retention_benchmark/results/summary.json",
            },
            "theory_of_mind": {
                "score": round(float(tom["baseline_accuracy"]), 3),
                "target": 0.8,
                "caveat": (
                    "symbolic Sally-Anne false-belief harness; demonstrates opt-in belief "
                    "tracking, not human-level cognition"
                ),
                "source": "experiments/theory_of_mind_ablation/results/summary.json",
            },
            "htn": {
                "score": round(float(htn_depth_three["goal_achievement_rate"]), 3),
                "target": 0.85,
                "caveat": (
                    "deterministic hierarchical-goal pursuit benchmark at depth 3 over 20 seeds"
                ),
                "source": "experiments/planning_depth/results/summary.json#results.3",
            },
            "realtime_latency": {
                "score": round(float(normalized_latency_score), 3),
                "target": 1.0,
                "caveat": (
                    f"normalized from {replay_latency['mean_tick_latency_ms']:.3f} ms replay-only "
                    f"tick latency against the {latency_target_ms:.0f} ms published ACE/Inworld "
                    "envelope; not an audio pipeline measurement"
                ),
                "source": "benchmarks/formal_report/results/latency_comparison.json#playground_replay",
            },
        },
    }


def memory_result(row: dict[str, Any], *, caveat: str) -> dict[str, Any]:
    return {
        "score": round(float(row["score"]), 3),
        "target": round(float(row["target"]), 3),
        "caveat": caveat,
        "source": (
            "benchmarks/memory_benchmark_integration/results/summary.json"
            f"#{row['benchmark_id']}"
        ),
    }


def load_all_submissions(knoema_submission: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    submissions: list[dict[str, Any]] = []
    for path in sorted(SUBMISSIONS_DIR.glob("*.yaml")):
        if path.name == "TEMPLATE.yaml":
            continue
        if path == KNOEMA_SUBMISSION_PATH and knoema_submission is not None:
            data = knoema_submission
        else:
            data = load_yaml(path)
        validate_submission_data(data, source=path)
        submissions.append(data)

    if KNOEMA_SUBMISSION_PATH not in sorted(SUBMISSIONS_DIR.glob("*.yaml")):
        data = generate_knoema_submission() if knoema_submission is None else knoema_submission
        validate_submission_data(data, source=KNOEMA_SUBMISSION_PATH)
        submissions.append(data)

    return sorted(submissions, key=leaderboard_sort_key)


def render_leaderboard(submissions: list[dict[str, Any]]) -> str:
    lines = [
        "# Knoema Bench Leaderboard",
        "",
        "<!-- This file is generated by scripts/build_leaderboard.py. -->",
        "",
        "Knoema Bench ranks persistent-agent frameworks across seven public axes. "
        "Scores are shown exactly as submitted; average score uses the raw axis score "
        "fields and does not erase caveats.",
        "",
        "| Rank | Framework | Version | Average | "
        + " | ".join(axis.label for axis in AXES)
        + " | "
        + " | ".join(f"{axis.label} caveat" for axis in AXES)
        + " |",
        "| ---: | --- | --- | ---: | "
        + " | ".join("---:" for _ in AXES)
        + " | "
        + " | ".join("---" for _ in AXES)
        + " |",
    ]

    for rank, submission in enumerate(submissions, start=1):
        results = submission["results"]
        score_cells = [format_score(results[axis.axis_id]) for axis in AXES]
        caveat_cells = [escape_cell(str(results[axis.axis_id]["caveat"])) for axis in AXES]
        row = [
            str(rank),
            escape_cell(str(submission["framework"])),
            escape_cell(str(submission["version"])),
            f"{average_score(submission):.3f}",
            *score_cells,
            *caveat_cells,
        ]
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "## Axis Targets",
            "",
            "| Axis | Target | Higher Is Better |",
            "| --- | --- | --- |",
        ]
    )
    for axis in AXES:
        higher = "yes" if axis.higher_is_better else "no"
        lines.append(f"| {axis.label} | {axis.target_label} | {higher} |")

    lines.extend(
        [
            "",
            "## Submission Validation",
            "",
            "Validate a candidate submission before opening a pull request:",
            "",
            "```bash",
            "python scripts/validate_submission.py bench/submissions/<your-framework>.yaml",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def validate_submission_file(path: Path) -> None:
    validate_submission_data(load_yaml(path), source=path)


def validate_submission_data(data: dict[str, Any], *, source: Path) -> None:
    schema = load_yaml(SCHEMA_PATH)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda error: list(error.path))
    if errors:
        rendered = "; ".join(f"{list(error.path)}: {error.message}" for error in errors)
        msg = f"{source}: schema validation failed: {rendered}"
        raise ValueError(msg)

    missing_sources = [
        result["source"]
        for result in data["results"].values()
        if not source_path_exists(str(result["source"]))
    ]
    if missing_sources:
        msg = f"{source}: source paths do not exist: {', '.join(missing_sources)}"
        raise ValueError(msg)


def source_path_exists(source: str) -> bool:
    path_part = source.split("#", 1)[0]
    if path_part.startswith(("http://", "https://")):
        return True
    return (ROOT / path_part).exists()


def leaderboard_sort_key(submission: dict[str, Any]) -> tuple[float, str]:
    return (-average_score(submission), str(submission["framework"]).lower())


def average_score(submission: dict[str, Any]) -> float:
    results = submission["results"]
    return sum(float(results[axis.axis_id]["score"]) for axis in AXES) / len(AXES)


def format_score(result: dict[str, Any]) -> str:
    return f"{float(result['score']):.3f} / {float(result['target']):.3f}"


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"{path}: expected YAML mapping"
        raise TypeError(msg)
    return data


def dump_yaml(data: dict[str, Any]) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


if __name__ == "__main__":
    sys.exit(main())
