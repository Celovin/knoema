"""Pattern-Oriented Modeling (POM) 3-gate validation subpackage.

This subpackage implements the Grimm-style POM validation gates from the
Luvoire realism roadmap section 7.3:

* **G1** time-of-day distribution,
* **G2** activity-diversity distribution,
* **G3** synthetic hotspot distribution (structural pattern only).

Each gate computes the Kolmogorov-Smirnov distance between a simulated
empirical distribution (binned histogram) and a target reference and is
"passed" when the distance falls below a configurable threshold. The
composite :func:`score_pom` aggregates the per-gate distances into a single
``[0.0, 1.0]`` score (higher is better) plus a boolean ``all_gates_passed``
flag.

The implementation depends only on numpy and the Python standard library
so the POM gates remain importable from a clean editable install.
"""

from luvoire.pom.gates import (
    GateConfig,
    GateResult,
    evaluate_gate,
    evaluate_three_gates,
)
from luvoire.pom.patterns import (
    Pattern,
    activity_diversity_pattern,
    hotspot_distribution_pattern,
    pattern_from_samples,
    time_of_day_pattern,
)
from luvoire.pom.scorer import PomScore, score_pom

__all__ = [
    "GateConfig",
    "GateResult",
    "Pattern",
    "PomScore",
    "activity_diversity_pattern",
    "evaluate_gate",
    "evaluate_three_gates",
    "hotspot_distribution_pattern",
    "pattern_from_samples",
    "score_pom",
    "time_of_day_pattern",
]
