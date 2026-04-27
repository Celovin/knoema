"""Deterministic Saltelli/Sobol sensitivity helpers (numpy-only).

This subpackage provides a small, fully deterministic Saltelli sampling and
Sobol first-order / total-order index estimator for use with synthetic models
such as :func:`luvoire.theory.rat.opportunity_event`.

The implementation follows Saltelli 2002 plus the radial-A/B/AB convention
used by SALib v1.4+. We deliberately keep the surface tiny and dependency-free
beyond numpy so the sensitivity panels remain reproducible from a clean
``pip install -e .`` install without optional research extras.
"""

from luvoire.sensitivity.sobol import (
    SaltelliSamples,
    SobolIndices,
    saltelli_sample,
    sobol_indices,
)

__all__ = [
    "SaltelliSamples",
    "SobolIndices",
    "saltelli_sample",
    "sobol_indices",
]
