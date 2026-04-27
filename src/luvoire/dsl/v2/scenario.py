"""Pydantic models for Scenario DSL v2 root."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from luvoire.dsl.scenario import (
    AgentSpec,
    EventSpec,
    MetricSpec,
    ScenarioDomain,
)
from luvoire.dsl.v2.parameters import ParameterSpec
from luvoire.environment import Environment

H3_CELL_PATTERN = r"^[0-9a-f]{15}$"
SYNTHETIC_EPSG_PREFIX = "luvoire-synthetic-"


class EnvironmentSpecV2(BaseModel):
    """Environment with optional GIS-readiness fields.

    ``h3_cell`` and ``epsg`` are optional in v2. When ``ethics.no_real_geometry``
    is true (the default), ``epsg`` must either be unset or use the
    ``luvoire-synthetic-*`` prefix; runtime use as an analysis unit is rejected
    by :mod:`luvoire.dsl.v2.validator`.
    """

    model_config = ConfigDict(extra="forbid")

    start_time: datetime
    location_path: tuple[str, ...] = Field(min_length=1)
    conditions: dict[str, str | int | float | bool] = Field(default_factory=dict)
    h3_cell: str | None = Field(default=None, pattern=H3_CELL_PATTERN)
    epsg: str | None = None

    def to_domain(self) -> Environment:
        return Environment(
            start_time=self.start_time,
            location_path=self.location_path,
            conditions=dict(self.conditions),
        )


class EthicsSpecV2(BaseModel):
    """Ethics declarations extended with the ``no_real_geometry`` guardrail.

    The new ``demographic_projection`` and ``pssdp_mode`` flags carve out
    a narrow, ethics-coherent space for **aggregate demographic projection**
    (KOSTAT 장래인구추계 style): they do *not* unlock prediction or suspect
    scoring, they only label that this scenario is a counterfactual
    long-horizon scenario at registered region-string aggregation. The
    existing ``no_prediction`` / ``no_suspect_scoring`` / ``no_real_geometry``
    guardrails remain in force and are validated independently.

    - ``demographic_projection``: when true, declares that the scenario
      uses :mod:`luvoire.demography` cohort-component projection over
      registered 시군구 string labels; aggregate-only output, no
      individual-level prediction. Defaults to ``False``.
    - ``pssdp_mode``: Public Safety Service Demand Projection mode. When
      true, declares that the scenario informs municipal-planning
      decision *support* (학교·119·파출소 인프라 수요), not operational
      LE decision *systems*. Defaults to ``False``.
    """

    model_config = ConfigDict(extra="forbid")

    fictional: bool = True
    no_real_people: bool = True
    no_prediction: bool = True
    no_suspect_scoring: bool = True
    no_real_geometry: bool = True
    sensitive_domain: bool = False
    demographic_projection: bool = False
    pssdp_mode: bool = False
    irb_notes: str | None = None


class ScenarioV2(BaseModel):
    """Scenario DSL v2 root object."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["2.0"] = "2.0"
    scenario_id: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    title: str = Field(min_length=1)
    domain: ScenarioDomain
    description: str = Field(min_length=1)
    seed: int = Field(ge=0)
    tick_duration_minutes: int = Field(default=60, ge=1)
    duration_days: int = Field(default=1, ge=1)
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    environment: EnvironmentSpecV2
    agents: list[AgentSpec] = Field(min_length=1)
    events: list[EventSpec] = Field(default_factory=list)
    metrics: list[MetricSpec] = Field(default_factory=list)
    ethics: EthicsSpecV2 = Field(default_factory=EthicsSpecV2)
    local_response: str = (
        '{"action_type": "observe", "target": null, '
        '"content": "records the scenario state."}'
    )


__all__ = [
    "H3_CELL_PATTERN",
    "SYNTHETIC_EPSG_PREFIX",
    "EnvironmentSpecV2",
    "EthicsSpecV2",
    "ScenarioV2",
]
