"""Deterministic trace grading helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from luvoire.export.finetuning import RunLogInput, parse_run_log


@dataclass(frozen=True, slots=True)
class TraceCriterionScore:
    name: str
    weight: float
    score: float
    rationale: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "weight": self.weight,
            "score": self.score,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class TraceGradeReport:
    trace_id: str
    item_count: int
    weighted_score: float
    passes_default_gate: bool
    criteria: tuple[TraceCriterionScore, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "trace_id": self.trace_id,
            "item_count": self.item_count,
            "weighted_score": self.weighted_score,
            "passes_default_gate": self.passes_default_gate,
            "criteria": [criterion.to_json_dict() for criterion in self.criteria],
        }


def grade_trace_report(
    run_log: RunLogInput,
    *,
    trace_id: str | None = None,
) -> TraceGradeReport:
    """Grade a trace with a deterministic rubric over structure and behavior."""

    rows = parse_run_log(run_log)
    action_rows = [row for row in rows if isinstance(row.get("action"), Mapping)]
    if not action_rows:
        raise ValueError("run log must contain at least one action row")

    criteria = (
        _criterion(
            "structural_validity",
            weight=0.35,
            score=_structural_validity(action_rows),
            rationale="checks required identifiers and action payload fields",
        ),
        _criterion(
            "timeline_continuity",
            weight=0.25,
            score=_timeline_continuity(action_rows),
            rationale="checks whether ticks cover a coherent contiguous window",
        ),
        _criterion(
            "interaction_richness",
            weight=0.20,
            score=_interaction_richness(action_rows),
            rationale="checks whether the trace contains directed or social actions",
        ),
        _criterion(
            "behavioral_variety",
            weight=0.20,
            score=_behavioral_variety(action_rows),
            rationale="checks whether the trace uses more than one action mode",
        ),
    )
    weighted = round(sum(criterion.weight * criterion.score for criterion in criteria), 3)
    resolved_trace_id = trace_id or _default_trace_id(run_log)
    return TraceGradeReport(
        trace_id=resolved_trace_id,
        item_count=len(action_rows),
        weighted_score=weighted,
        passes_default_gate=weighted >= 0.65,
        criteria=criteria,
    )


def _criterion(name: str, *, weight: float, score: float, rationale: str) -> TraceCriterionScore:
    return TraceCriterionScore(
        name=name,
        weight=weight,
        score=round(max(0.0, min(score, 1.0)), 3),
        rationale=rationale,
    )


def _structural_validity(rows: list[dict[str, Any]]) -> float:
    valid = 0
    for row in rows:
        action = dict(row["action"])
        if (
            str(row.get("agent_id", "")).strip()
            and str(action.get("action_type", "")).strip()
            and str(action.get("location", row.get("location", ""))).strip()
            and str(action.get("content", "")).strip()
        ):
            valid += 1
    return valid / len(rows)


def _timeline_continuity(rows: list[dict[str, Any]]) -> float:
    ticks = sorted({int(row.get("tick", 0)) for row in rows})
    if not ticks:
        return 0.0
    span = (ticks[-1] - ticks[0]) + 1
    if span <= 0:
        return 0.0
    return len(ticks) / span


def _interaction_richness(rows: list[dict[str, Any]]) -> float:
    social = 0
    for row in rows:
        action = dict(row["action"])
        action_type = str(action.get("action_type", "")).strip().lower()
        target = action.get("target")
        if target not in {None, ""} or action_type in {"speak", "approach", "help", "argue"}:
            social += 1
    return social / len(rows)


def _behavioral_variety(rows: list[dict[str, Any]]) -> float:
    action_types = {
        str(dict(row["action"]).get("action_type", "")).strip().lower()
        for row in rows
        if str(dict(row["action"]).get("action_type", "")).strip()
    }
    if not action_types:
        return 0.0
    return min(len(action_types) / 4.0, 1.0)


def _default_trace_id(run_log: RunLogInput) -> str:
    if isinstance(run_log, Path):
        return run_log.stem
    return "trace"


__all__ = ["TraceCriterionScore", "TraceGradeReport", "grade_trace_report"]
