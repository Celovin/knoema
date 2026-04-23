"""CLI helper for ODD markdown export."""

from __future__ import annotations

from pathlib import Path

from luvoire.dsl import load_scenario
from luvoire.export.odd.populate import populate_from_simulation
from luvoire.export.odd.render import render_markdown


def export_odd_markdown(scenario_path: str | Path, out_path: str | Path) -> Path:
    scenario = load_scenario(scenario_path)
    simulator = scenario.to_simulator()
    report = populate_from_simulation(simulator, scenario)
    output_path = Path(out_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report), encoding="utf-8")
    return output_path


__all__ = ["export_odd_markdown"]
