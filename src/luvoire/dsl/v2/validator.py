"""Ethics, geometry, and parameter validation rules for Scenario DSL v2."""

from __future__ import annotations

from dataclasses import dataclass

from luvoire.dsl.v2.scenario import SYNTHETIC_EPSG_PREFIX, ScenarioV2
from luvoire.dsl.validator import DISALLOWED_PURPOSE_PHRASES

ADDITIONAL_DISALLOWED_PHRASES_V2 = (
    "individual risk score",
    "real address",
    "real coordinate",
    "real-world prediction",
)

ALL_DISALLOWED_PHRASES_V2 = DISALLOWED_PURPOSE_PHRASES + ADDITIONAL_DISALLOWED_PHRASES_V2


@dataclass(frozen=True, slots=True)
class ValidationIssueV2:
    code: str
    path: str
    message: str


def collect_validation_issues_v2(scenario: ScenarioV2) -> list[ValidationIssueV2]:
    issues: list[ValidationIssueV2] = []
    ethics = scenario.ethics
    if not ethics.fictional:
        issues.append(_issue("ethics.fictional", "Scenario must be fictional."))
    if not ethics.no_real_people:
        issues.append(
            _issue("ethics.no_real_people", "Scenario must not model real people.")
        )
    if not ethics.no_prediction:
        issues.append(
            _issue("ethics.no_prediction", "Scenario must not predict future harm.")
        )
    if not ethics.no_suspect_scoring:
        issues.append(
            _issue("ethics.no_suspect_scoring", "Scenario must not score suspects.")
        )
    if ethics.sensitive_domain and not (ethics.irb_notes or "").strip():
        issues.append(
            _issue(
                "ethics.irb_notes",
                "Sensitive scenarios require IRB or review notes.",
            )
        )

    if ethics.no_real_geometry and scenario.environment.epsg is not None:
        epsg = scenario.environment.epsg
        if not epsg.startswith(SYNTHETIC_EPSG_PREFIX):
            issues.append(
                _issue(
                    "environment.epsg",
                    (
                        "ethics.no_real_geometry=true requires environment.epsg "
                        f"to start with '{SYNTHETIC_EPSG_PREFIX}' "
                        f"(got {epsg!r})."
                    ),
                )
            )

    for index, agent in enumerate(scenario.agents):
        if not agent.synthetic:
            issues.append(
                _issue(f"agents[{index}].synthetic", "Agents must be synthetic.")
            )

    for path, text in _text_fields(scenario):
        normalized = text.casefold()
        for phrase in ALL_DISALLOWED_PHRASES_V2:
            if phrase in normalized:
                issues.append(
                    ValidationIssueV2(
                        code="disallowed_purpose",
                        path=path,
                        message=f"Disallowed purpose phrase: {phrase}",
                    )
                )
    return issues


def validate_scenario_v2(scenario: ScenarioV2) -> None:
    issues = collect_validation_issues_v2(scenario)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"scenario v2 validation failed: {details}")


def _text_fields(scenario: ScenarioV2) -> list[tuple[str, str]]:
    fields: list[tuple[str, str]] = [
        ("title", scenario.title),
        ("description", scenario.description),
    ]
    fields.extend(
        (f"agents[{index}].background", agent.background)
        for index, agent in enumerate(scenario.agents)
    )
    fields.extend(
        (f"events[{index}].description", event.description)
        for index, event in enumerate(scenario.events)
    )
    fields.extend(
        (f"metrics[{index}].description", metric.description)
        for index, metric in enumerate(scenario.metrics)
    )
    return fields


def _issue(path: str, message: str) -> ValidationIssueV2:
    return ValidationIssueV2(code="ethics_guardrail", path=path, message=message)


__all__ = [
    "ADDITIONAL_DISALLOWED_PHRASES_V2",
    "ALL_DISALLOWED_PHRASES_V2",
    "ValidationIssueV2",
    "collect_validation_issues_v2",
    "validate_scenario_v2",
]
