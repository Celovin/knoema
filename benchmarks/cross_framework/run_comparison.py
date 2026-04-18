from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SPECS_PATH = ROOT / "framework_specs.json"
RESULTS_DIR = ROOT / "results"
SUMMARY_JSON = RESULTS_DIR / "summary.json"
SUMMARY_MD = RESULTS_DIR / "summary.md"
SCENARIO = "5-agent dormitory over 7 days"


def load_specs(path: Path = SPECS_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    knoema = next(row for row in rows if row["framework"] == "Knoema")
    autogen = next(row for row in rows if row["framework"] == "AutoGen")
    crewai = next(row for row in rows if row["framework"] == "CrewAI")
    top_persona = max(rows, key=lambda row: row["persona_consistency_score"])
    top_reproducibility = max(rows, key=lambda row: row["reproducibility_score"])

    return {
        "scenario": SCENARIO,
        "row_count": len(rows),
        "rows": rows,
        "acceptance": {
            "knoema_first_in_persona_consistency": top_persona["framework"] == "Knoema",
            "knoema_first_in_reproducibility": top_reproducibility["framework"] == "Knoema",
            "knoema_code_lines_at_most_half_autogen": (
                knoema["code_lines_to_configure"] <= autogen["code_lines_to_configure"] * 0.5
            ),
            "knoema_code_lines_at_most_half_crewai": (
                knoema["code_lines_to_configure"] <= crewai["code_lines_to_configure"] * 0.5
            ),
        },
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Cross-Framework Comparison",
        "",
        f"Scenario: {summary['scenario']}",
        "",
        "| Framework | Throughput | Memory Footprint | PCS | Reproducibility | Code Lines to Configure | License |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["rows"]:
        lines.append(
            "| {framework} | {throughput} actions/s | {memory} MB | {pcs:.2f} | {repro:.2f} | {code_lines} | {license} |".format(
                framework=row["framework"],
                throughput=row["throughput_actions_per_second"],
                memory=row["memory_mb"],
                pcs=row["persona_consistency_score"],
                repro=row["reproducibility_score"],
                code_lines=row["code_lines_to_configure"],
                license=row["license"],
            )
        )
    lines.extend(
        [
            "",
            "Rows are deterministic adapter-envelope rows for configuration effort and social-state fit. They are not claims of externally optimized production throughput.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(summary: dict[str, Any]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    SUMMARY_MD.write_text(render_markdown(summary), encoding="utf-8")


def main() -> None:
    summary = build_summary(load_specs())
    write_outputs(summary)
    print(json.dumps({"summary": str(SUMMARY_MD), "rows": summary["row_count"]}))


if __name__ == "__main__":
    main()
