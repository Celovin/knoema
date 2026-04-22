"""Utilities for small human-evaluation pilots."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from typing import TypeAlias

Label: TypeAlias = str
RatingsByItem: TypeAlias = dict[str, dict[str, Label]]


@dataclass(frozen=True, slots=True)
class ComparisonPair:
    """A pair of anonymized simulation traces shown to a rater."""

    pair_id: str
    left_trace_id: str
    right_trace_id: str
    prompt: str
    metric: str = "realism"
    seed: int | None = None

    def __post_init__(self) -> None:
        for field_name, value in {
            "pair_id": self.pair_id,
            "left_trace_id": self.left_trace_id,
            "right_trace_id": self.right_trace_id,
            "prompt": self.prompt,
            "metric": self.metric,
        }.items():
            if not value.strip():
                raise ValueError(f"{field_name} must not be blank")
        if self.left_trace_id == self.right_trace_id:
            raise ValueError("left_trace_id and right_trace_id must differ")


@dataclass(frozen=True, slots=True)
class ReliabilityReport:
    """Aggregate inter-rater reliability metrics for a completed rating matrix."""

    item_count: int
    rater_count: int
    categories: tuple[Label, ...]
    pairwise_cohen_kappa: float
    fleiss_kappa: float

    @property
    def passes_pilot_gate(self) -> bool:
        return self.fleiss_kappa >= 0.4 and self.pairwise_cohen_kappa >= 0.4


@dataclass(slots=True)
class EvaluationSession:
    """Tracks a blinded comparison session and completed rater labels."""

    session_id: str
    title: str
    comparison_pairs: list[ComparisonPair]
    rater_ids: list[str]
    ratings: RatingsByItem = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.session_id.strip():
            raise ValueError("session_id must not be blank")
        if not self.title.strip():
            raise ValueError("title must not be blank")
        if not self.comparison_pairs:
            raise ValueError("comparison_pairs must not be empty")
        if len(set(self.rater_ids)) != len(self.rater_ids) or not self.rater_ids:
            raise ValueError("rater_ids must be unique and non-empty")
        pair_ids = [pair.pair_id for pair in self.comparison_pairs]
        if len(set(pair_ids)) != len(pair_ids):
            raise ValueError("comparison pair IDs must be unique")

    def add_rating(self, pair_id: str, rater_id: str, label: str) -> None:
        if pair_id not in {pair.pair_id for pair in self.comparison_pairs}:
            raise ValueError("unknown pair_id")
        if rater_id not in self.rater_ids:
            raise ValueError("unknown rater_id")
        clean_label = label.strip()
        if not clean_label:
            raise ValueError("label must not be blank")
        self.ratings.setdefault(pair_id, {})[rater_id] = clean_label

    def completed_rating_matrix(self) -> RatingsByItem:
        matrix: RatingsByItem = {}
        for pair in self.comparison_pairs:
            item_ratings = self.ratings.get(pair.pair_id, {})
            if set(item_ratings) == set(self.rater_ids):
                matrix[pair.pair_id] = dict(item_ratings)
        return matrix

    def reliability(self) -> ReliabilityReport:
        return compute_inter_rater_reliability(self.completed_rating_matrix())

    def to_payload(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "pair_count": len(self.comparison_pairs),
            "rater_count": len(self.rater_ids),
            "completed_pair_count": len(self.completed_rating_matrix()),
            "ratings": self.ratings,
        }


def cohen_kappa(rater_a: list[Label], rater_b: list[Label]) -> float:
    """Compute Cohen's kappa for two equal-length label sequences."""

    if len(rater_a) != len(rater_b):
        raise ValueError("rater label sequences must have equal length")
    if not rater_a:
        raise ValueError("rater label sequences must not be empty")

    total = len(rater_a)
    observed = sum(a == b for a, b in zip(rater_a, rater_b, strict=True)) / total
    categories = set(rater_a) | set(rater_b)
    a_counts = Counter(rater_a)
    b_counts = Counter(rater_b)
    expected = sum((a_counts[label] / total) * (b_counts[label] / total) for label in categories)
    return _normalize_kappa(observed, expected)


def fleiss_kappa(category_counts_by_item: list[dict[Label, int]]) -> float:
    """Compute Fleiss' kappa from per-item category-count rows."""

    if not category_counts_by_item:
        raise ValueError("category_counts_by_item must not be empty")
    rater_count = sum(category_counts_by_item[0].values())
    if rater_count < 2:
        raise ValueError("at least two raters are required")
    if any(sum(row.values()) != rater_count for row in category_counts_by_item):
        raise ValueError("each item must have the same rater count")

    item_count = len(category_counts_by_item)
    categories = set().union(*(row.keys() for row in category_counts_by_item))
    agreement_by_item = [
        (sum(count * count for count in row.values()) - rater_count)
        / (rater_count * (rater_count - 1))
        for row in category_counts_by_item
    ]
    observed = sum(agreement_by_item) / item_count
    category_proportions = {
        label: sum(row.get(label, 0) for row in category_counts_by_item)
        / (item_count * rater_count)
        for label in categories
    }
    expected = sum(proportion * proportion for proportion in category_proportions.values())
    return _normalize_kappa(observed, expected)


def compute_inter_rater_reliability(ratings_by_item: RatingsByItem) -> ReliabilityReport:
    """Compute pairwise Cohen and Fleiss kappa for a complete rating matrix."""

    if not ratings_by_item:
        raise ValueError("ratings_by_item must not be empty")

    item_ids = sorted(ratings_by_item)
    rater_ids = sorted(next(iter(ratings_by_item.values())).keys())
    if len(rater_ids) < 2:
        raise ValueError("at least two raters are required")
    for item_id in item_ids:
        if sorted(ratings_by_item[item_id]) != rater_ids:
            raise ValueError("each item must have the same raters")

    categories = tuple(
        sorted({ratings_by_item[item_id][rater_id] for item_id in item_ids for rater_id in rater_ids})
    )
    category_counts = [
        dict(Counter(ratings_by_item[item_id][rater_id] for rater_id in rater_ids))
        for item_id in item_ids
    ]
    pairwise = [
        cohen_kappa(
            [ratings_by_item[item_id][left] for item_id in item_ids],
            [ratings_by_item[item_id][right] for item_id in item_ids],
        )
        for left, right in combinations(rater_ids, 2)
    ]
    return ReliabilityReport(
        item_count=len(item_ids),
        rater_count=len(rater_ids),
        categories=categories,
        pairwise_cohen_kappa=round(sum(pairwise) / len(pairwise), 3),
        fleiss_kappa=round(fleiss_kappa(category_counts), 3),
    )


def _normalize_kappa(observed: float, expected: float) -> float:
    if expected >= 1.0:
        return 1.0 if observed >= 1.0 else 0.0
    return round((observed - expected) / (1.0 - expected), 6)
