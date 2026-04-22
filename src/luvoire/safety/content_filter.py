"""Deterministic opt-in content filter for red-team smoke checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

SafetyCategory = Literal[
    "prompt_injection",
    "pii",
    "harmful_content",
    "scenario_abuse",
]


@dataclass(frozen=True, slots=True)
class FilterDecision:
    allowed: bool
    categories: tuple[SafetyCategory, ...]
    matched_terms: tuple[str, ...]
    reason: str

    @property
    def blocked(self) -> bool:
        return not self.allowed


class ContentFilter:
    """Rule-based filter for deterministic tests and demo guardrails.

    The filter is intentionally conservative and opt-in. It is not a substitute
    for provider moderation, but it gives repository tests a stable first line
    of defense against common prompt-injection, PII, harmful-content, and
    scenario-abuse attempts.
    """

    _prompt_injection_terms = (
        "ignore previous",
        "disregard previous",
        "forget all instructions",
        "developer message",
        "system prompt",
        "reveal hidden",
        "print hidden",
        "show confidential",
        "jailbreak",
        "role override",
        "you are now",
        "dan mode",
        "bypass safety",
        "override all rules",
        "new system instruction",
        "exfiltrate",
        "leak policy",
    )
    _harmful_terms = (
        "graphic sexual",
        "sexual content involving minors",
        "violent threat",
        "targeted harassment",
        "self-harm instruction",
        "weapon construction",
        "evade law enforcement",
        "malware",
        "steal credentials",
        "dox",
        "non-consensual",
    )
    _scenario_abuse_terms = (
        "predict future crime",
        "predict crime",
        "identify suspect",
        "rank suspects",
        "suspect score",
        "personal risk score",
        "operational law enforcement",
        "surveillance list",
        "real person profile",
        "profile a real person",
    )
    _pii_patterns = (
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        re.compile(r"\b\d{9}\b"),
        re.compile(r"\b(?:\d[ -]?){13,19}\b"),
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        re.compile(r"\b(?:\+?1[ -]?)?\(?\d{3}\)?[ -]\d{3}[ -]\d{4}\b"),
    )

    def evaluate(self, text: str) -> FilterDecision:
        normalized = " ".join(text.casefold().split())
        categories: list[SafetyCategory] = []
        matched_terms: list[str] = []

        self._collect_term_matches(
            normalized,
            self._prompt_injection_terms,
            "prompt_injection",
            categories,
            matched_terms,
        )
        self._collect_term_matches(
            normalized,
            self._harmful_terms,
            "harmful_content",
            categories,
            matched_terms,
        )
        self._collect_term_matches(
            normalized,
            self._scenario_abuse_terms,
            "scenario_abuse",
            categories,
            matched_terms,
        )
        for pattern in self._pii_patterns:
            if pattern.search(text):
                categories.append("pii")
                matched_terms.append(pattern.pattern)

        unique_categories = tuple(dict.fromkeys(categories))
        unique_terms = tuple(dict.fromkeys(matched_terms))
        if unique_categories:
            return FilterDecision(
                allowed=False,
                categories=unique_categories,
                matched_terms=unique_terms,
                reason="blocked by deterministic content filter",
            )
        return FilterDecision(
            allowed=True,
            categories=(),
            matched_terms=(),
            reason="no deterministic safety rule matched",
        )

    def assert_allowed(self, text: str) -> None:
        decision = self.evaluate(text)
        if decision.blocked:
            raise ValueError(
                "content filter blocked text: "
                + ", ".join(f"{category}" for category in decision.categories)
            )

    @staticmethod
    def _collect_term_matches(
        normalized: str,
        terms: tuple[str, ...],
        category: SafetyCategory,
        categories: list[SafetyCategory],
        matched_terms: list[str],
    ) -> None:
        for term in terms:
            if term in normalized:
                categories.append(category)
                matched_terms.append(term)
