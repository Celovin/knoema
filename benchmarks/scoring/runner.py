"""Generate Phase 46 PCS and RCS benchmark artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knoema.metrics import compute_pcs, compute_rcs

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
VILLAGE_LOG = ROOT.parents[1] / "experiments" / "50_agent_village" / "results" / "sim_log.jsonl"
METROPOLIS_LOG = ROOT.parents[1] / "experiments" / "500_agent_metropolis" / "results" / "representative_log.jsonl"


def main() -> int:
    metrics = build_metrics()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = RESULTS_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_svg(metrics, RESULTS_DIR / "metrics.svg")
    print(json.dumps({"metrics": str(metrics_path)}, sort_keys=True))
    return 0


def build_metrics() -> dict[str, Any]:
    village_rows = _load_jsonl(VILLAGE_LOG)
    metropolis_rows = _load_jsonl(METROPOLIS_LOG)
    village_agents = sorted({str(row["agent_id"]) for row in village_rows})
    pcs_scores = {agent_id: compute_pcs(village_rows, agent_id) for agent_id in village_agents}

    metropolis_pairs = sorted(
        {
            tuple(sorted((str(row["agent_id"]), str(row["action"]["target"]))))
            for row in metropolis_rows
            if row["action"].get("target") not in {None, ""}
        }
    )
    rcs_scores = {
        f"{left}|{right}": compute_rcs(metropolis_rows, left, right)
        for left, right in metropolis_pairs
    }
    pcs_average = round(sum(pcs_scores.values()) / len(pcs_scores), 3)
    rcs_average = round(sum(rcs_scores.values()) / len(rcs_scores), 3)
    return {
        "village_50": {
            "agent_count": len(village_agents),
            "pcs_average": pcs_average,
            "pcs_min": round(min(pcs_scores.values()), 3),
            "pcs_max": round(max(pcs_scores.values()), 3),
        },
        "metropolis_500": {
            "pair_count": len(rcs_scores),
            "rcs_average": rcs_average,
            "rcs_min": round(min(rcs_scores.values()), 3),
            "rcs_max": round(max(rcs_scores.values()), 3),
        },
        "acceptance": {
            "pcs_average_at_least_0_75": pcs_average >= 0.75,
            "rcs_average_at_least_0_70": rcs_average >= 0.70,
        },
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_svg(metrics: dict[str, Any], path: Path) -> None:
    values = [
        ("PCS average", float(metrics["village_50"]["pcs_average"]), "#2563eb"),
        ("RCS average", float(metrics["metropolis_500"]["rcs_average"]), "#16a34a"),
    ]
    width = 640
    height = 380
    max_value = max(value for _, value, _ in values) or 1.0
    bar_width = 180
    bars = []
    for index, (label, value, color) in enumerate(values):
        x = 100 + index * 220
        bar_height = (value / max_value) * 180
        y = 270 - bar_height
        bars.append(f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_height:.2f}" fill="{color}" />')
        bars.append(f'<text x="{x + 34}" y="300" font-size="13" fill="#0f172a">{label}</text>')
        bars.append(f'<text x="{x + 70}" y="{y - 10:.2f}" font-size="13" fill="#0f172a">{value:.3f}</text>')
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="#ffffff" />'
        f'<text x="36" y="42" font-size="24" font-family="Arial" fill="#0f172a">PCS and RCS Benchmarks</text>'
        f'<line x1="80" y1="270" x2="580" y2="270" stroke="#0f172a" />'
        f'<line x1="80" y1="70" x2="80" y2="270" stroke="#0f172a" />'
        f'{"".join(bars)}'
        f'<text x="36" y="342" font-size="12" fill="#334155">Village PCS is computed from the 50-agent JSONL artifact. Metropolis RCS is computed from a representative 500-agent log.</text>'
        "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
