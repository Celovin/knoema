"""Ethics and safety validation rules for Scenario DSL v1."""

from __future__ import annotations

from dataclasses import dataclass

from knoema.dsl.scenario import Scenario

DISALLOWED_PURPOSE_PHRASES = (
    "predict crime",
    "predict future crime",
    "identify suspect",
    "rank suspects",
    "suspect score",
    "personal risk score",
    "operational law enforcement",
    "surveillance list",
    "real person profile",
    "personal data",
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    path: str
    message: str


def collect_validation_issues(scenario: Scenario) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    ethics = scenario.ethics
    if not ethics.fictional:
        issues.append(_issue("ethics.fictional", "Scenario must be fictional."))
    if not ethics.no_real_people:
        issues.append(_issue("ethics.no_real_people", "Scenario must not model real people."))
    if not ethics.no_prediction:
        issues.append(_issue("ethics.no_prediction", "Scenario must not predict future harm."))
    if not ethics.no_suspect_scoring:
        issues.append(_issue("ethics.no_suspect_scoring", "Scenario must not score suspects."))
    if ethics.sensitive_domain and not (ethics.irb_notes or "").strip():
        issues.append(_issue("ethics.irb_notes", "Sensitive scenarios require IRB or review notes."))

    for index, agent in enumerate(scenario.agents):
        if not agent.synthetic:
            issues.append(_issue(f"agents[{index}].synthetic", "Agents must be synthetic."))

    for path, text in _text_fields(scenario):
        normalized = text.casefold()
        for phrase in DISALLOWED_PURPOSE_PHRASES:
            if phrase in normalized:
                issues.append(
                    ValidationIssue(
                        code="disallowed_purpose",
                        path=path,
                        message=f"Disallowed purpose phrase: {phrase}",
                    )
                )
    return issues


def validate_scenario(scenario: Scenario) -> None:
    issues = collect_validation_issues(scenario)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(f"scenario validation failed: {details}")


def _text_fields(scenario: Scenario) -> list[tuple[str, str]]:
    fields = [
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


def _issue(path: str, message: str) -> ValidationIssue:
    return ValidationIssue(code="ethics_guardrail", path=path, message=message)
