"""Synthetic shock catalogue — typed events that modulate cells over ticks.

A :class:`Shock` is a frozen dataclass describing a stylised exogenous
event (a festival, a protest, a policy change, a weather event, or an
infrastructure change) that affects one or more synthetic-grid cells over
a closed tick interval ``[start_tick, end_tick]``. The :class:`Catalog`
wraps a tuple of :class:`Shock` and is itself immutable: :meth:`Catalog.add`
returns a new catalog rather than mutating in place.

All values are synthetic and do not reference any real event or real
location. The ``magnitude`` field is a unit-less signed effect size in
``[-1.0, 1.0]``; consumers (e.g. :class:`luvoire.shock.scheduler.ShockScheduler`)
decide how to interpret the sign per shock kind.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ShockKind = Literal[
    "festival",
    "protest",
    "policy_change",
    "weather_event",
    "infrastructure_change",
]
"""Closed enumeration of shock kinds recognised by the scheduler."""

_VALID_KINDS: frozenset[str] = frozenset(
    {
        "festival",
        "protest",
        "policy_change",
        "weather_event",
        "infrastructure_change",
    }
)


@dataclass(frozen=True, slots=True)
class Shock:
    """A single synthetic shock affecting a set of cells over a tick window.

    Attributes:
        shock_id: Stable string id for the shock. Round-trips through
            :meth:`Catalog.to_dict` / :meth:`Catalog.from_dict`.
        kind: One of :data:`ShockKind`.
        start_tick: First tick at which the shock is active (inclusive).
        end_tick: Last tick at which the shock is active (inclusive).
            Must satisfy ``start_tick <= end_tick``.
        affected_cells: Non-empty tuple of synthetic-grid cell ids.
        magnitude: Signed effect size in ``[-1.0, 1.0]``.
        description: Free-text description (synthetic, no real-world
            referents).

    Construction-time validation rejects invalid tick ranges, an empty
    ``affected_cells`` tuple, magnitudes outside ``[-1.0, 1.0]``, and
    unknown ``kind`` values.
    """

    shock_id: str
    kind: ShockKind
    start_tick: int
    end_tick: int
    affected_cells: tuple[str, ...]
    magnitude: float
    description: str = ""

    def __post_init__(self) -> None:
        if self.kind not in _VALID_KINDS:
            raise ValueError(
                f"unknown shock kind {self.kind!r}; expected one of "
                f"{sorted(_VALID_KINDS)}"
            )
        if self.start_tick > self.end_tick:
            raise ValueError(
                f"start_tick must be <= end_tick, got "
                f"start_tick={self.start_tick} end_tick={self.end_tick}"
            )
        if not isinstance(self.affected_cells, tuple):
            # Type hint ``tuple[str, ...]`` is not enforced at runtime.
            # Reject lists / generators so external mutation cannot leak
            # into a frozen Shock instance shared across catalogs.
            raise TypeError(
                f"affected_cells must be a tuple, got "
                f"{type(self.affected_cells).__name__}"
            )
        if not self.affected_cells:
            raise ValueError("affected_cells must be non-empty")
        if not -1.0 <= self.magnitude <= 1.0:
            raise ValueError(
                f"magnitude must be in [-1.0, 1.0], got {self.magnitude}"
            )

    def is_active_at(self, tick: int) -> bool:
        """Return whether the shock is active at *tick* (inclusive endpoints)."""

        return self.start_tick <= tick <= self.end_tick

    def affects(self, cell_id: str) -> bool:
        """Return whether *cell_id* is in :attr:`affected_cells`."""

        return cell_id in self.affected_cells

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly dict representation."""

        return {
            "shock_id": self.shock_id,
            "kind": self.kind,
            "start_tick": self.start_tick,
            "end_tick": self.end_tick,
            "affected_cells": list(self.affected_cells),
            "magnitude": self.magnitude,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> Shock:
        """Reconstruct a :class:`Shock` from :meth:`to_dict` output."""

        kind_raw = payload["kind"]
        if not isinstance(kind_raw, str) or kind_raw not in _VALID_KINDS:
            raise ValueError(f"unknown shock kind {kind_raw!r}")
        cells_raw = payload["affected_cells"]
        if not isinstance(cells_raw, (list, tuple)):
            raise TypeError("affected_cells must be a list or tuple of str")
        cells: tuple[str, ...] = tuple(str(c) for c in cells_raw)
        shock_id = payload["shock_id"]
        if not isinstance(shock_id, str):
            raise TypeError("shock_id must be a str")
        start_tick = payload["start_tick"]
        end_tick = payload["end_tick"]
        if not isinstance(start_tick, int) or isinstance(start_tick, bool):
            raise TypeError("start_tick must be an int")
        if not isinstance(end_tick, int) or isinstance(end_tick, bool):
            raise TypeError("end_tick must be an int")
        magnitude = payload["magnitude"]
        if not isinstance(magnitude, (int, float)) or isinstance(magnitude, bool):
            raise TypeError("magnitude must be a real number")
        description = payload.get("description", "")
        if not isinstance(description, str):
            raise TypeError("description must be a str")
        kind: ShockKind = kind_raw  # type: ignore[assignment]
        return cls(
            shock_id=shock_id,
            kind=kind,
            start_tick=int(start_tick),
            end_tick=int(end_tick),
            affected_cells=cells,
            magnitude=float(magnitude),
            description=description,
        )


@dataclass(frozen=True, slots=True)
class Catalog:
    """An immutable tuple of :class:`Shock` with query helpers.

    The catalogue does not enforce uniqueness of ``shock_id``; callers
    that need uniqueness should check before :meth:`add`.
    """

    shocks: tuple[Shock, ...] = field(default_factory=tuple)

    def __len__(self) -> int:
        return len(self.shocks)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self.shocks)

    def add(self, shock: Shock) -> Catalog:
        """Return a new catalogue with *shock* appended.

        The receiver is not mutated.
        """

        return Catalog(shocks=(*self.shocks, shock))

    def active_at(self, tick: int) -> tuple[Shock, ...]:
        """Return shocks active at *tick* (inclusive endpoints)."""

        return tuple(s for s in self.shocks if s.is_active_at(tick))

    def affecting(
        self,
        cell_id: str,
        *,
        tick: int | None = None,
    ) -> tuple[Shock, ...]:
        """Return shocks whose ``affected_cells`` contains *cell_id*.

        When *tick* is provided, the result is further filtered to shocks
        active at that tick.
        """

        if tick is None:
            return tuple(s for s in self.shocks if s.affects(cell_id))
        return tuple(
            s for s in self.shocks if s.affects(cell_id) and s.is_active_at(tick)
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-friendly dict representation."""

        return {"shocks": [s.to_dict() for s in self.shocks]}

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> Catalog:
        """Reconstruct a :class:`Catalog` from :meth:`to_dict` output."""

        raw = payload.get("shocks", [])
        if not isinstance(raw, (list, tuple)):
            raise TypeError("shocks must be a list or tuple")
        items: list[Shock] = []
        for entry in raw:
            if not isinstance(entry, dict):
                raise TypeError("each shock entry must be a dict")
            items.append(Shock.from_dict(entry))
        return cls(shocks=tuple(items))


def synthetic_festival(
    start_tick: int,
    end_tick: int,
    cells: tuple[str, ...],
    magnitude: float = 0.5,
    *,
    shock_id: str = "synthetic-festival",
    description: str = "synthetic festival increasing crowd density on affected cells",
) -> Shock:
    """Return a canonical synthetic festival :class:`Shock`.

    Useful as a fixture in counterfactual tests. The default
    ``magnitude`` of ``0.5`` represents a moderate positive uplift in
    target exposure on the affected cells.
    """

    return Shock(
        shock_id=shock_id,
        kind="festival",
        start_tick=start_tick,
        end_tick=end_tick,
        affected_cells=cells,
        magnitude=magnitude,
        description=description,
    )


__all__ = [
    "Catalog",
    "Shock",
    "ShockKind",
    "synthetic_festival",
]
