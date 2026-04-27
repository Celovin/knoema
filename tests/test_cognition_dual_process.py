"""Tests for luvoire.cognition.dual_process."""

from __future__ import annotations

import pytest

from luvoire.cognition.dual_process import (
    RoutingDecision,
    TriggerSignal,
    route_decision,
)


def test_no_triggers_routes_to_sys1() -> None:
    decision = route_decision([])
    assert decision.route == "sys1_habit"
    assert decision.score == 0.0
    assert decision.triggered_by == ()


def test_high_weight_trigger_escalates_to_sys2() -> None:
    decision = route_decision([TriggerSignal("anomaly", 0.7)])
    assert decision.route == "sys2_reflect"
    assert decision.score == pytest.approx(0.7)
    assert decision.triggered_by == ("anomaly",)


def test_score_clipped_to_one() -> None:
    decision = route_decision(
        [TriggerSignal("a", 0.6), TriggerSignal("b", 0.6)]
    )
    assert decision.score == pytest.approx(1.0)


def test_threshold_zero_always_routes_to_sys2() -> None:
    decision = route_decision([], threshold=0.0)
    assert decision.route == "sys2_reflect"


def test_threshold_one_requires_full_score() -> None:
    decision = route_decision(
        [TriggerSignal("only", 0.99)], threshold=1.0
    )
    assert decision.route == "sys1_habit"


def test_invalid_threshold_rejected() -> None:
    with pytest.raises(ValueError, match="threshold"):
        route_decision([], threshold=2.0)


def test_negative_weight_rejected() -> None:
    with pytest.raises(ValueError, match="negative weight"):
        route_decision([TriggerSignal("bad", -0.1)])


def test_decision_dataclass_is_frozen() -> None:
    decision = route_decision([TriggerSignal("x", 0.6)])
    assert isinstance(decision, RoutingDecision)
    with pytest.raises((AttributeError, TypeError)):
        decision.route = "sys1_habit"  # type: ignore[misc]


def test_zero_weight_signals_do_not_show_in_triggered_by() -> None:
    decision = route_decision(
        [TriggerSignal("noise", 0.0), TriggerSignal("real", 0.6)]
    )
    assert decision.triggered_by == ("real",)
