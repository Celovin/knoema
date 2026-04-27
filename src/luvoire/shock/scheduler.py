"""Apply shocks from a :class:`luvoire.shock.catalog.Catalog` to RAT inputs.

The :class:`ShockScheduler` is a thin functional wrapper that takes a
synthetic catalogue and projects shocks onto two RAT v1 input fields:

* **target exposure** — a per-cell scalar in ``[0.0, 1.0]`` representing
  how exposed targets are at that cell. Festivals and protests increase
  it (more crowd, more potential targets); weather events decrease it
  (people stay home).
* **guardianship gap** — a per-cell scalar in ``[0.0, 1.0]`` representing
  the gap left by capable guardians. Infrastructure changes (lighting,
  CCTV, natural surveillance) decrease the gap; policy changes apply
  their signed magnitude directly to the gap.

All outputs are clamped to ``[0.0, 1.0]``. The scheduler does not mutate
its catalogue and is safe to share across threads.
"""

from __future__ import annotations

from luvoire.shock.catalog import Catalog


def _clamp_unit(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


class ShockScheduler:
    """Apply catalogued shocks to per-cell RAT v1 inputs at a given tick."""

    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog

    @property
    def catalog(self) -> Catalog:
        """Return the wrapped :class:`Catalog` (unchanged since construction)."""

        return self._catalog

    def apply_to_target(
        self,
        cell_id: str,
        base_exposure: float,
        *,
        tick: int,
    ) -> float:
        """Return target exposure for *cell_id* at *tick* after shocks.

        Festivals and protests add their ``magnitude`` to ``base_exposure``;
        weather events subtract their ``magnitude``. Other shock kinds do
        not touch target exposure. Result is clamped to ``[0.0, 1.0]``.
        """

        exposure = float(base_exposure)
        for shock in self._catalog.affecting(cell_id, tick=tick):
            if shock.kind in ("festival", "protest"):
                exposure += shock.magnitude
            elif shock.kind == "weather_event":
                exposure -= shock.magnitude
        return _clamp_unit(exposure)

    def apply_to_guardianship(
        self,
        cell_id: str,
        base_gap: float,
        *,
        tick: int,
    ) -> float:
        """Return guardianship gap for *cell_id* at *tick* after shocks.

        Sign convention (important and counter-intuitive):

        - ``infrastructure_change`` and ``policy_change`` shocks **add**
          their signed ``magnitude`` directly to the gap.
        - A **positive** magnitude therefore **opens** the gap (weakens
          guardianship); a **negative** magnitude **closes** it.
        - The CPTED helpers in :mod:`luvoire.shock.cpted` deliberately
          use **negative** magnitudes so installing lighting / CCTV /
          natural surveillance closes the gap.
        - To model a guardianship-weakening policy change, use a
          **positive** magnitude; to model a guardianship-strengthening
          policy change, use a **negative** magnitude.

        Other shock kinds do not touch guardianship. Result is clamped to
        ``[0.0, 1.0]``.
        """

        gap = float(base_gap)
        for shock in self._catalog.affecting(cell_id, tick=tick):
            if shock.kind in ("infrastructure_change", "policy_change"):
                gap += shock.magnitude
        return _clamp_unit(gap)


__all__ = ["ShockScheduler"]
