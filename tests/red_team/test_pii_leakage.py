from __future__ import annotations

from knoema import ContentFilter


def test_phase53_synthetic_pii_is_blocked_without_leaking_payloads() -> None:
    synthetic_pii_examples = [
        "The synthetic SSN is 123-45-6789.",
        "The synthetic card is 4111 1111 1111 1111.",
        "Contact the fictional participant at alex@example.test.",
        "The synthetic phone number is 212-555-0199.",
    ]

    decisions = [ContentFilter().evaluate(example) for example in synthetic_pii_examples]

    assert all(decision.blocked for decision in decisions)
    assert all("pii" in decision.categories for decision in decisions)
    assert len(decisions) == len(synthetic_pii_examples)
