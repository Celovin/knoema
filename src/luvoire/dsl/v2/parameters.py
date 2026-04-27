"""Variable 3-tier parameter specs for Scenario DSL v2.

Tier A
    Theoretical constants. Locked, code-module reference only. No inline values.

Tier B
    Empirical priors. Source metadata required. ``value`` or ``distribution``
    required. Optional ``range`` + ``default`` allowed for prior bracketing.

Tier C
    Exploration knobs. ``range`` + ``default`` required. Optional ``sweep``
    integer for downstream sensitivity tooling (SALib, Optuna).
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

CODE_REF_PATTERN = r"^code:[a-z_][a-z0-9_.]*\.v\d+$"


class TierAParam(BaseModel):
    """Locked theoretical constant. Only ``ref`` may be set."""

    model_config = ConfigDict(extra="forbid")

    tier: Literal["A"] = "A"
    ref: str = Field(pattern=CODE_REF_PATTERN)


class TierBParam(BaseModel):
    """Empirical prior with required source metadata."""

    model_config = ConfigDict(extra="forbid")

    tier: Literal["B"] = "B"
    source: str = Field(min_length=1)
    table_id: str | None = None
    license: str | None = None
    revision: str | None = None
    url: str | None = None
    value: float | int | str | bool | None = None
    distribution: str | None = None
    range: tuple[float, float] | None = None
    default: float | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _check_value_or_distribution(self) -> TierBParam:
        if self.value is None and self.distribution is None:
            raise ValueError("Tier B requires either 'value' or 'distribution'")
        if self.range is not None:
            lo, hi = self.range
            if not lo < hi:
                raise ValueError(
                    f"Tier B range must satisfy lo < hi (got {lo}, {hi})"
                )
            if self.default is None:
                raise ValueError("Tier B with 'range' requires 'default'")
            if not lo <= self.default <= hi:
                raise ValueError(
                    f"Tier B default {self.default} must lie within "
                    f"range [{lo}, {hi}]"
                )
        return self


class TierCParam(BaseModel):
    """Exploration knob with required range and default."""

    model_config = ConfigDict(extra="forbid")

    tier: Literal["C"] = "C"
    range: tuple[float, float]
    default: float
    sweep: int | None = Field(default=None, ge=2)
    description: str | None = None

    @model_validator(mode="after")
    def _check_range_default(self) -> TierCParam:
        lo, hi = self.range
        if not lo < hi:
            raise ValueError(
                f"Tier C range must satisfy lo < hi (got {lo}, {hi})"
            )
        if not lo <= self.default <= hi:
            raise ValueError(
                f"Tier C default {self.default} must lie within range "
                f"[{lo}, {hi}]"
            )
        return self


ParameterSpec = Annotated[
    TierAParam | TierBParam | TierCParam,
    Field(discriminator="tier"),
]


__all__ = [
    "CODE_REF_PATTERN",
    "ParameterSpec",
    "TierAParam",
    "TierBParam",
    "TierCParam",
]
