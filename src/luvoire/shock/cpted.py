"""CPTED helpers — synthetic environmental design shocks.

Crime Prevention Through Environmental Design (CPTED) is a body of
practice that links the physical environment (lighting, sightlines,
surveillance) to opportunity reduction. The helpers in this module
express three common interventions as :class:`luvoire.shock.catalog.Shock`
records of kind ``infrastructure_change`` so they can be plugged into a
:class:`luvoire.shock.scheduler.ShockScheduler` for counterfactual
analysis on a synthetic urban grid.

Synthetic only:

* No per-place risk score is produced or implied.
* No real coordinate, address, or jurisdiction is referenced.
* The default magnitudes are stylised guesses, not calibrated effect
  sizes from any real CPTED intervention. Changing them will not
  generalise to real-world deployments.
* Nothing in this module is intended to support operational deployment
  of physical interventions; it exists to test RAT v1 simulations under
  hypothetical conditions.
"""

from __future__ import annotations

from luvoire.shock.catalog import Shock

_DEFAULT_END_TICK = 10**9
"""Sentinel used to express 'permanent for the duration of a simulation'."""


def _build_infrastructure_shock(
    shock_id: str,
    cell_ids: tuple[str, ...],
    start_tick: int,
    end_tick: int,
    magnitude: float,
    description: str,
) -> Shock:
    return Shock(
        shock_id=shock_id,
        kind="infrastructure_change",
        start_tick=start_tick,
        end_tick=end_tick,
        affected_cells=cell_ids,
        magnitude=magnitude,
        description=description,
    )


def cpted_lighting_install(
    cell_ids: tuple[str, ...],
    start_tick: int = 0,
    end_tick: int = _DEFAULT_END_TICK,
    magnitude: float = -0.3,
) -> Shock:
    """Return an ``infrastructure_change`` shock for installing lighting.

    The default ``magnitude`` of ``-0.3`` reduces the guardianship gap on
    the affected cells when applied via
    :meth:`luvoire.shock.scheduler.ShockScheduler.apply_to_guardianship`.
    """

    return _build_infrastructure_shock(
        shock_id="cpted-lighting-install",
        cell_ids=cell_ids,
        start_tick=start_tick,
        end_tick=end_tick,
        magnitude=magnitude,
        description="synthetic CPTED lighting install (closes guardianship gap)",
    )


def cpted_cctv_install(
    cell_ids: tuple[str, ...],
    start_tick: int = 0,
    end_tick: int = _DEFAULT_END_TICK,
    magnitude: float = -0.4,
) -> Shock:
    """Return an ``infrastructure_change`` shock for installing CCTV.

    The default ``magnitude`` of ``-0.4`` reduces the guardianship gap on
    the affected cells.
    """

    return _build_infrastructure_shock(
        shock_id="cpted-cctv-install",
        cell_ids=cell_ids,
        start_tick=start_tick,
        end_tick=end_tick,
        magnitude=magnitude,
        description="synthetic CPTED CCTV install (closes guardianship gap)",
    )


def cpted_natural_surveillance(
    cell_ids: tuple[str, ...],
    start_tick: int = 0,
    end_tick: int = _DEFAULT_END_TICK,
    magnitude: float = -0.2,
) -> Shock:
    """Return an ``infrastructure_change`` shock for natural surveillance uplift.

    The default ``magnitude`` of ``-0.2`` reduces the guardianship gap on
    the affected cells (e.g. opening sightlines, removing visual
    obstructions, mixed-use frontage).
    """

    return _build_infrastructure_shock(
        shock_id="cpted-natural-surveillance",
        cell_ids=cell_ids,
        start_tick=start_tick,
        end_tick=end_tick,
        magnitude=magnitude,
        description="synthetic CPTED natural surveillance uplift",
    )


__all__ = [
    "cpted_cctv_install",
    "cpted_lighting_install",
    "cpted_natural_surveillance",
]
