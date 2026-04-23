"""Schema for human-editable ODD protocol markdown fragments."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OddReport:
    purpose_and_patterns: str
    entities_state_variables_scales: str
    process_overview_and_scheduling: str
    design_concepts: str
    initialization: str
    input_data: str
    submodels: str
    generated_on: str | None = None

    def section_items(self) -> tuple[tuple[str, str], ...]:
        return (
            ("Purpose and Patterns", self.purpose_and_patterns),
            ("Entities, State Variables, and Scales", self.entities_state_variables_scales),
            ("Process Overview and Scheduling", self.process_overview_and_scheduling),
            ("Design Concepts", self.design_concepts),
            ("Initialization", self.initialization),
            ("Input Data", self.input_data),
            ("Submodels", self.submodels),
        )


TODO_STUB = "TODO: author this section"

__all__ = ["TODO_STUB", "OddReport"]
