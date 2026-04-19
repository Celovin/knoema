from __future__ import annotations

from pathlib import Path


def test_phase42_effort_allocation_exists_with_assumptions() -> None:
    allocation = Path("docs/research/effort_allocation.md").read_text(encoding="utf-8")

    assert "Effort Allocation by Sub-task" in allocation
    assert "software-deliverable estimates only" in allocation
    assert "Total tracked hours | 78.25" in allocation


def test_phase42_effort_allocation_lists_all_budget_lanes() -> None:
    allocation = Path("docs/research/effort_allocation.md").read_text(encoding="utf-8")

    required = [
        "Core runtime and simulation",
        "UX and control surface",
        "Application B game delivery",
        "Application C research delivery",
        "Validation and benchmark",
        "Compliance and audit docs",
    ]

    missing = [item for item in required if item not in allocation]

    assert missing == []


def test_phase42_effort_allocation_covers_sixty_subtasks() -> None:
    allocation = Path("docs/research/effort_allocation.md").read_text(encoding="utf-8")

    for subtask_id in range(1, 61):
        assert f"| {subtask_id} |" in allocation
