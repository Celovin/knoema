from __future__ import annotations

import json
from pathlib import Path

from knoema.dsl import collect_validation_issues, load_scenario


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _scenario_paths(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.yaml")
        if not path.name.startswith("_")
    )


def validate_scenarios() -> list[dict[str, object]]:
    repo_root = _repo_root()
    hub_root = repo_root / "scenarios_hub"
    paths = _scenario_paths(hub_root)
    if not paths:
        raise SystemExit("No scenario files found under scenarios_hub.")

    seen_ids: set[str] = set()
    results: list[dict[str, object]] = []
    for path in paths:
        scenario = load_scenario(path)
        issues = collect_validation_issues(scenario)
        if issues:
            details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
            raise SystemExit(f"{path}: unexpected validation issues: {details}")
        if scenario.scenario_id != path.stem:
            raise SystemExit(
                f"{path}: scenario_id '{scenario.scenario_id}' must match filename '{path.stem}'."
            )
        if scenario.scenario_id in seen_ids:
            raise SystemExit(f"Duplicate scenario_id detected: {scenario.scenario_id}")
        seen_ids.add(scenario.scenario_id)

        logs = scenario.to_simulator().run(duration_days=scenario.duration_days)
        if not logs:
            raise SystemExit(f"{path}: simulator smoke run did not produce any logs.")

        results.append(
            {
                "path": str(path.relative_to(repo_root)).replace("\\", "/"),
                "scenario_id": scenario.scenario_id,
                "domain": scenario.domain,
                "agent_count": len(scenario.agents),
                "log_count": len(logs),
            }
        )
    return results


def main() -> None:
    results = validate_scenarios()
    print(json.dumps({"validated": len(results), "scenarios": results}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        raise SystemExit(str(exc)) from exc
