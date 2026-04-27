"""Luvoire exogenous shock subpackage — synthetic event overlays.

This subpackage provides a synthetic event catalogue that overlays
time-and-space modifiers on a synthetic urban grid (see
:mod:`luvoire.geo.synthetic_grid`). It is consumed by RAT v1 scenarios to
test counterfactual interventions such as "what if a CCTV were installed
on this cell?" or "what if a festival increases crowd density on this
cell during these ticks?".

All shocks defined here are **synthetic**: they do not refer to any real
event, real coordinate, or real address. The CPTED helpers in
:mod:`luvoire.shock.cpted` likewise express stylised environmental
interventions and intentionally do not produce per-place risk scores or
deployment guidance.

Public surface:

* :class:`Shock`, :class:`Catalog`, :data:`ShockKind`,
  :func:`synthetic_festival` — :mod:`luvoire.shock.catalog`.
* :class:`ShockScheduler` — :mod:`luvoire.shock.scheduler`.
* :func:`cpted_lighting_install`, :func:`cpted_cctv_install`,
  :func:`cpted_natural_surveillance` — :mod:`luvoire.shock.cpted`.
"""

from __future__ import annotations

from luvoire.shock.catalog import (
    Catalog,
    Shock,
    ShockKind,
    synthetic_festival,
)
from luvoire.shock.cpted import (
    cpted_cctv_install,
    cpted_lighting_install,
    cpted_natural_surveillance,
)
from luvoire.shock.scheduler import ShockScheduler

__all__ = [
    "Catalog",
    "Shock",
    "ShockKind",
    "ShockScheduler",
    "cpted_cctv_install",
    "cpted_lighting_install",
    "cpted_natural_surveillance",
    "synthetic_festival",
]
