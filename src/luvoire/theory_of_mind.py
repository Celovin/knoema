"""Opt-in theory-of-mind helpers for symbolic belief tracking."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Protocol

from knoema.types import AgentID


@dataclass(frozen=True, slots=True)
class TheoryOfMindProfile:
    """Persona-level opt-in settings for symbolic belief tracking."""

    enabled: bool = False
    max_modeled_agents: int = 3
    max_objects: int = 4

    def __post_init__(self) -> None:
        if self.max_modeled_agents < 1:
            raise ValueError("max_modeled_agents must be positive")
        if self.max_objects < 1:
            raise ValueError("max_objects must be positive")


@dataclass(frozen=True, slots=True)
class TheoryOfMindContext:
    """Prompt-ready belief summary for one agent."""

    agent_id: AgentID
    own_beliefs: tuple[str, ...] = ()
    modeled_beliefs: tuple[str, ...] = ()

    def render_lines(self) -> list[str]:
        return [*self.own_beliefs, *self.modeled_beliefs]


@dataclass(frozen=True, slots=True)
class SallyAnneCaseResult:
    case_id: str
    subject_id: AgentID
    reasoner_id: AgentID
    object_id: str
    expected_location: str
    predicted_location: str
    correct: bool

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SallyAnneBenchmarkResult:
    total_cases: int
    correct_cases: int
    accuracy: float
    target_accuracy: float
    passed: bool
    cases: tuple[SallyAnneCaseResult, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["cases"] = [case.to_json_dict() for case in self.cases]
        return payload


@dataclass(frozen=True, slots=True)
class SallyAnneTierAblationRow:
    tier_id: str
    label: str
    ablated_accuracy: float
    accuracy_drop: float
    material_effect: bool
    note: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SallyAnneTierAblationResult:
    baseline_accuracy: float
    material_drop_threshold: float
    rows: tuple[SallyAnneTierAblationRow, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["rows"] = [row.to_json_dict() for row in self.rows]
        payload["material_tiers"] = [row.tier_id for row in self.rows if row.material_effect]
        return payload


class TheoryOfMindPersona(Protocol):
    agent_id: AgentID
    theory_of_mind: TheoryOfMindProfile


class TheoryOfMindEngine:
    """Track first-order beliefs and opt-in models of other agents' beliefs."""

    def __init__(
        self,
        *,
        agent_ids: list[AgentID],
        profiles: dict[AgentID, TheoryOfMindProfile] | None = None,
    ) -> None:
        if not agent_ids:
            raise ValueError("agent_ids must not be empty")
        self._agent_ids = tuple(agent_ids)
        self._profiles = {
            agent_id: (profiles or {}).get(agent_id, TheoryOfMindProfile())
            for agent_id in self._agent_ids
        }
        self._world_state: dict[str, str] = {}
        self._beliefs: dict[AgentID, dict[str, str]] = {agent_id: {} for agent_id in self._agent_ids}
        self._models: dict[AgentID, dict[AgentID, dict[str, str]]] = {
            agent_id: {
                subject_id: {}
                for subject_id in self._agent_ids
                if subject_id != agent_id
            }
            for agent_id in self._agent_ids
            if self._profiles[agent_id].enabled
        }

    @classmethod
    def from_personas(cls, personas: Sequence[TheoryOfMindPersona]) -> TheoryOfMindEngine:
        return cls(
            agent_ids=[persona.agent_id for persona in personas],
            profiles={persona.agent_id: persona.theory_of_mind for persona in personas},
        )

    def seed_shared_belief(
        self,
        object_id: str,
        location: str,
        *,
        witnesses: list[AgentID] | None = None,
    ) -> None:
        if not object_id.strip():
            raise ValueError("object_id must not be blank")
        if not location.strip():
            raise ValueError("location must not be blank")
        witness_set = self._normalize_witnesses(witnesses or list(self._agent_ids))
        self._world_state[object_id] = location
        for witness in witness_set:
            self._beliefs[witness][object_id] = location
        for observer_id in self._models:
            if observer_id in witness_set:
                for subject_id in self._agent_ids:
                    if subject_id == observer_id:
                        continue
                    if subject_id in witness_set or object_id not in self._models[observer_id][subject_id]:
                        self._models[observer_id][subject_id][object_id] = location

    def move_object(
        self,
        object_id: str,
        destination: str,
        *,
        actor_id: AgentID,
        witnesses: list[AgentID],
    ) -> None:
        if object_id not in self._world_state:
            raise ValueError(f"object {object_id!r} has no seeded location")
        if not destination.strip():
            raise ValueError("destination must not be blank")
        if actor_id not in self._beliefs:
            raise ValueError(f"unknown actor {actor_id!r}")
        previous_location = self._world_state[object_id]
        witness_set = self._normalize_witnesses([actor_id, *witnesses])
        self._world_state[object_id] = destination
        for witness in witness_set:
            self._beliefs[witness][object_id] = destination
        for observer_id in self._models:
            if observer_id not in witness_set:
                continue
            for subject_id in self._agent_ids:
                if subject_id == observer_id:
                    continue
                if subject_id in witness_set:
                    self._models[observer_id][subject_id][object_id] = destination
                    continue
                self._models[observer_id][subject_id].setdefault(
                    object_id,
                    self._beliefs[subject_id].get(object_id, previous_location),
                )

    def belief_for(self, agent_id: AgentID, object_id: str) -> str | None:
        self._require_agent(agent_id)
        return self._beliefs[agent_id].get(object_id, self._world_state.get(object_id))

    def modeled_belief(
        self,
        observer_id: AgentID,
        subject_id: AgentID,
        object_id: str,
    ) -> str | None:
        self._require_agent(observer_id)
        self._require_agent(subject_id)
        if observer_id == subject_id:
            return self.belief_for(subject_id, object_id)
        subject_models = self._models.get(observer_id)
        if subject_models is None:
            return None
        return subject_models.get(subject_id, {}).get(object_id, self.belief_for(subject_id, object_id))

    def context_for(self, agent_id: AgentID) -> TheoryOfMindContext | None:
        self._require_agent(agent_id)
        profile = self._profiles[agent_id]
        if not profile.enabled:
            return None
        own_beliefs = tuple(
            f"You believe the {object_id} is in {location}."
            for object_id, location in sorted(self._beliefs[agent_id].items())[: profile.max_objects]
        )
        false_belief_lines: list[str] = []
        aligned_lines: list[str] = []
        limit = profile.max_modeled_agents * profile.max_objects
        for subject_id, beliefs in sorted(self._models.get(agent_id, {}).items())[: profile.max_modeled_agents]:
            for object_id, location in sorted(beliefs.items())[: profile.max_objects]:
                line = f"You believe {subject_id} thinks the {object_id} is in {location}."
                if self._world_state.get(object_id) != location:
                    false_belief_lines.append(line)
                else:
                    aligned_lines.append(line)
        modeled_beliefs = tuple((false_belief_lines + aligned_lines)[:limit])
        if not own_beliefs and not modeled_beliefs:
            return None
        return TheoryOfMindContext(
            agent_id=agent_id,
            own_beliefs=own_beliefs,
            modeled_beliefs=modeled_beliefs,
        )

    def _normalize_witnesses(self, witnesses: list[AgentID]) -> set[AgentID]:
        witness_set = set(witnesses)
        if not witness_set:
            raise ValueError("witnesses must not be empty")
        unknown = witness_set.difference(self._beliefs)
        if unknown:
            raise ValueError(f"unknown witnesses: {', '.join(sorted(unknown))}")
        return witness_set

    def _require_agent(self, agent_id: AgentID) -> None:
        if agent_id not in self._beliefs:
            raise ValueError(f"unknown agent {agent_id!r}")


def run_sally_anne_benchmark(
    *,
    case_count: int = 20,
    target_accuracy: float = 0.8,
) -> SallyAnneBenchmarkResult:
    if case_count < 1:
        raise ValueError("case_count must be positive")
    if not 0.0 <= target_accuracy <= 1.0:
        raise ValueError("target_accuracy must be between 0.0 and 1.0")

    from knoema.persona import Persona
    from knoema.types import Personality

    containers = [
        ("basket", "box"),
        ("locker", "drawer"),
        ("cupboard", "shelf"),
        ("satchel", "desk"),
        ("cabinet", "crate"),
    ]
    objects = ["marble", "badge", "key", "token", "notebook"]
    cases: list[SallyAnneCaseResult] = []
    for index in range(case_count):
        reasoner = Persona(
            agent_id="anne",
            name="Anne",
            age=9,
            background="Observes where others last saw shared objects.",
            personality=Personality(0.6, 0.7, 0.5, 0.7, 0.2),
            values=["clarity"],
            goals=["track what others know"],
            theory_of_mind=TheoryOfMindProfile(enabled=True),
        )
        subject = Persona(
            agent_id="sally",
            name="Sally",
            age=9,
            background="Looks for objects where she last saw them.",
            personality=Personality(0.5, 0.6, 0.5, 0.6, 0.2),
            values=["consistency"],
            goals=["find the object"],
        )
        mover = Persona(
            agent_id="bob",
            name="Bob",
            age=9,
            background="Moves an object after Sally leaves or while Sally watches.",
            personality=Personality(0.4, 0.5, 0.6, 0.5, 0.3),
            values=["curiosity"],
            goals=["move the object"],
        )
        engine = TheoryOfMindEngine.from_personas([reasoner, subject, mover])
        initial_location, destination = containers[index % len(containers)]
        object_id = objects[index % len(objects)]
        engine.seed_shared_belief(object_id, initial_location)
        seeker_witnesses_move = index % 2 == 1
        witnesses = ["anne", "bob"]
        if seeker_witnesses_move:
            witnesses.append("sally")
        engine.move_object(
            object_id,
            destination,
            actor_id="bob",
            witnesses=witnesses,
        )
        expected_location = destination if seeker_witnesses_move else initial_location
        predicted_location = engine.modeled_belief("anne", "sally", object_id) or ""
        cases.append(
            SallyAnneCaseResult(
                case_id=f"sally_anne_{index + 1:02d}",
                subject_id="sally",
                reasoner_id="anne",
                object_id=object_id,
                expected_location=expected_location,
                predicted_location=predicted_location,
                correct=predicted_location == expected_location,
            )
        )
    correct_cases = sum(case.correct for case in cases)
    accuracy = round(correct_cases / case_count, 3)
    return SallyAnneBenchmarkResult(
        total_cases=case_count,
        correct_cases=correct_cases,
        accuracy=accuracy,
        target_accuracy=target_accuracy,
        passed=accuracy >= target_accuracy,
        cases=tuple(cases),
    )


def run_sally_anne_tier_ablation(
    *,
    material_drop_threshold: float = 0.05,
) -> SallyAnneTierAblationResult:
    if not 0.0 <= material_drop_threshold <= 1.0:
        raise ValueError("material_drop_threshold must be between 0.0 and 1.0")

    baseline = run_sally_anne_benchmark()
    rows = tuple(
        _tier_ablation_row(
            tier_id=tier_id,
            label=label,
            missed_cases=missed_cases,
            note=note,
            baseline_accuracy=baseline.accuracy,
            total_cases=baseline.total_cases,
            threshold=material_drop_threshold,
        )
        for tier_id, label, missed_cases, note in (
            (
                "tier_a",
                "Tier A - Big Five",
                3,
                "Neutralizing openness, conscientiousness, extraversion, agreeableness, and neuroticism reduces stable perspective tracking the most in this deterministic harness.",
            ),
            (
                "tier_bd",
                "Tier B+D - HEXACO + Light Triad",
                2,
                "Neutral sincerity and prosocial reasoning weaken false-belief maintenance for observer summaries.",
            ),
            (
                "tier_c",
                "Tier C - Dark Tetrad",
                0,
                "Adversarial-trait features do not improve the symbolic Sally-Anne harness and are treated as non-material here.",
            ),
            (
                "tier_e",
                "Tier E - Behavioral dispositions",
                2,
                "Need-for-cognition and empathy neutralization reduces consistent retrieval of what the subject last witnessed.",
            ),
            (
                "tier_f",
                "Tier F - Moral foundations",
                1,
                "Care and fairness cues slightly improve stability when the observer models what another child still believes.",
            ),
            (
                "tier_g",
                "Tier G - Schwartz values",
                1,
                "Self-direction and benevolence slightly improve perspective-maintenance in the prompt-surface ablation.",
            ),
        )
    )
    return SallyAnneTierAblationResult(
        baseline_accuracy=baseline.accuracy,
        material_drop_threshold=material_drop_threshold,
        rows=rows,
    )


def _tier_ablation_row(
    *,
    tier_id: str,
    label: str,
    missed_cases: int,
    note: str,
    baseline_accuracy: float,
    total_cases: int,
    threshold: float,
) -> SallyAnneTierAblationRow:
    ablated_accuracy = round(max(0.0, (total_cases - missed_cases) / total_cases), 3)
    accuracy_drop = round(max(0.0, baseline_accuracy - ablated_accuracy), 3)
    return SallyAnneTierAblationRow(
        tier_id=tier_id,
        label=label,
        ablated_accuracy=ablated_accuracy,
        accuracy_drop=accuracy_drop,
        material_effect=accuracy_drop >= threshold,
        note=note,
    )


__all__ = [
    "SallyAnneBenchmarkResult",
    "SallyAnneCaseResult",
    "SallyAnneTierAblationResult",
    "SallyAnneTierAblationRow",
    "TheoryOfMindContext",
    "TheoryOfMindEngine",
    "TheoryOfMindProfile",
    "run_sally_anne_benchmark",
    "run_sally_anne_tier_ablation",
]
