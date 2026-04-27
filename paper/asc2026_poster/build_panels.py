"""Build the four-panel ASC 2026 methodology poster figure set.

Outputs deterministic PDFs (and matching SVGs) into ``paper/asc2026_poster/``:

1. ``panel_method_3tier.pdf`` — Scenario DSL v2 variable 3-tier exposure.
2. ``panel_theory_rat.pdf`` — RAT three-component spatio-temporal convergence.
3. ``panel_sensitivity_sobol.pdf`` — Sobol first-order/total-order indices
   recomputed live from ``experiments/rat_sensitivity/results/sobol_indices.json``.
4. ``panel_replay_hash.pdf`` — Same-seed replay-equality table backed by
   ``scripts/verify_replay_shas.py`` baselines.

Run:

    python paper/asc2026_poster/build_panels.py

This module ships no external dependencies beyond matplotlib + numpy + pyyaml,
all of which are already in ``[dev]``. The script is fully deterministic and
produces byte-identical PDFs across reruns when matplotlib's font cache is
warm.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from luvoire.theory.rat import DEFAULT_CONVERGENCE_THRESHOLD  # noqa: E402

OUT_DIR = Path(__file__).parent
SOBOL_RESULTS = (
    ROOT / "experiments" / "rat_sensitivity" / "results" / "sobol_indices.json"
)
REPLAY_SHAS_PY = ROOT / "scripts" / "verify_replay_shas.py"

PALETTE_TIER = {"A": "#1f6feb", "B": "#9a67ea", "C": "#2c974b"}
PALETTE_RAT = {
    "Motivated actor": "#d1495b",
    "Suitable target": "#edae49",
    "Capable guardian (gap)": "#00798c",
}


def _save(fig: plt.Figure, name: str) -> None:
    pdf_path = OUT_DIR / f"{name}.pdf"
    svg_path = OUT_DIR / f"{name}.svg"
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(svg_path, bbox_inches="tight")
    plt.close(fig)


def panel_method_3tier() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    rows = [
        (
            "Tier A — Theoretical constant",
            "code:luvoire.theory.rat.v1",
            "Locked. YAML cannot redefine the convergence rule.",
            PALETTE_TIER["A"],
        ),
        (
            "Tier B — Empirical prior",
            'source: "KOSTAT 2024 Time Use Survey"',
            "Required source metadata; value or distribution.",
            PALETTE_TIER["B"],
        ),
        (
            "Tier C — Exploration knob",
            "guardianship_density: range [0.1, 0.9]",
            "Required range and default; sweep-friendly.",
            PALETTE_TIER["C"],
        ),
    ]
    for index, (title, sample, note, color) in enumerate(rows):
        y = 2 - index
        ax.add_patch(
            mpatches.FancyBboxPatch(
                (0.04, y - 0.40),
                0.92,
                0.80,
                boxstyle="round,pad=0.02",
                linewidth=0,
                facecolor=color,
                alpha=0.13,
            )
        )
        ax.text(0.07, y + 0.20, title, fontsize=12, weight="bold", color=color)
        ax.text(
            0.07,
            y - 0.05,
            sample,
            fontsize=10,
            family="monospace",
        )
        ax.text(0.07, y - 0.30, note, fontsize=9, color="#444444")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-0.6, 2.6)
    ax.set_axis_off()
    ax.set_title(
        "Scenario DSL v2 — Variable 3-tier exposure",
        loc="left",
        fontsize=13,
        weight="bold",
    )
    ax.text(
        0.04,
        -0.55,
        "CI lint enforces tier-specific keys; replay hash invariants are unchanged.",
        fontsize=8,
        color="#555555",
    )
    _save(fig, "panel_method_3tier")


def panel_theory_rat() -> None:
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    centers = {
        "Motivated actor": (0.30, 0.60),
        "Suitable target": (0.70, 0.60),
        "Capable guardian (gap)": (0.50, 0.30),
    }
    for label, (cx, cy) in centers.items():
        circle = mpatches.Circle(
            (cx, cy),
            radius=0.18,
            color=PALETTE_RAT[label],
            alpha=0.30,
            linewidth=0,
        )
        ax.add_patch(circle)
        ax.text(
            cx,
            cy + 0.21,
            label,
            ha="center",
            fontsize=10,
            weight="bold",
            color="#222222",
        )
    ax.text(
        0.50,
        0.495,
        "opportunity_event\nrat_v1_synthetic_opportunity",
        ha="center",
        fontsize=9.5,
        family="monospace",
        color="#222222",
    )
    ax.text(
        0.50,
        0.05,
        f"convergence_score = motivation * exposure * gap "
        f">= {DEFAULT_CONVERGENCE_THRESHOLD} (locked threshold)",
        ha="center",
        fontsize=9,
        color="#444444",
    )
    ax.text(
        0.50,
        0.94,
        "Three components must converge in the same tick and same/adjacent cell.",
        ha="center",
        fontsize=10,
        color="#222222",
    )
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title(
        "Routine activity theory v1 — synthetic convergence",
        loc="left",
        fontsize=13,
        weight="bold",
    )
    _save(fig, "panel_theory_rat")


def panel_sensitivity_sobol() -> None:
    payload = json.loads(SOBOL_RESULTS.read_text(encoding="utf-8"))
    variables = ("motivation", "exposure", "gap")
    first = [payload["variables"][v]["first_order"] for v in variables]
    total = [payload["variables"][v]["total_order"] for v in variables]
    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    x = np.arange(len(variables))
    width = 0.34
    ax.bar(
        x - width / 2,
        first,
        width=width,
        color="#1f6feb",
        label="First-order $S_i$",
    )
    ax.bar(
        x + width / 2,
        total,
        width=width,
        color="#9a67ea",
        label="Total-order $S_{T_i}$",
    )
    ax.set_xticks(x)
    ax.set_xticklabels([v.capitalize() for v in variables])
    ax.set_ylim(0.0, max(total) * 1.25)
    ax.set_ylabel("Sobol index")
    ax.set_title(
        f"Sensitivity sweep — n = {payload['n']}, "
        f"{payload['model_evaluations']} evaluations, seed = {payload['seed']}",
        loc="left",
        fontsize=12,
        weight="bold",
    )
    ax.legend(loc="upper right", frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for index, (s1, st) in enumerate(zip(first, total, strict=True)):
        ax.text(index - width / 2, s1 + 0.01, f"{s1:.3f}", ha="center", fontsize=9)
        ax.text(index + width / 2, st + 0.01, f"{st:.3f}", ha="center", fontsize=9)
    ax.text(
        0.0,
        -0.18,
        (
            "Total-order > first-order across all three components: the "
            "multiplicative convergence rule produces strong interaction "
            "effects ≈ 30%."
        ),
        transform=ax.transAxes,
        fontsize=8,
        color="#555555",
    )
    _save(fig, "panel_sensitivity_sobol")


def panel_replay_hash() -> None:
    text = REPLAY_SHAS_PY.read_text(encoding="utf-8")
    baselines: list[tuple[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith('"demo/replay/'):
            continue
        try:
            path_part, sha_part = line.split('": "', 1)
        except ValueError:
            continue
        rel_path = path_part.lstrip('"')
        sha = sha_part.split('"', 1)[0]
        baselines.append((rel_path.replace("demo/replay/", ""), sha[:16] + "…"))
    fig, ax = plt.subplots(figsize=(8.5, 4.0))
    ax.set_axis_off()
    ax.set_title(
        f"Replay-hash invariants — {len(baselines)} baselines locked",
        loc="left",
        fontsize=13,
        weight="bold",
    )
    columns = ("Artifact", "SHA-256 (first 16 hex)")
    cell_text = [list(row) for row in baselines]
    table = ax.table(
        cellText=cell_text,
        colLabels=columns,
        cellLoc="left",
        colLoc="left",
        loc="upper left",
        bbox=[0.0, 0.10, 1.0, 0.78],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    for (row, _col), cell in table.get_celld().items():
        cell.set_linewidth(0.4)
        cell.set_edgecolor("#dddddd")
        if row == 0:
            cell.set_facecolor("#f0f4ff")
            cell.set_text_props(weight="bold")
    ax.text(
        0.0,
        0.02,
        (
            "Each release runs scripts/verify_replay_shas.py; any drift halts "
            "the verification gate. Same (seed, config, code) → same hash."
        ),
        transform=ax.transAxes,
        fontsize=8,
        color="#555555",
    )
    _save(fig, "panel_replay_hash")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_method_3tier()
    panel_theory_rat()
    panel_sensitivity_sobol()
    panel_replay_hash()
    print(f"wrote 4 panels to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
