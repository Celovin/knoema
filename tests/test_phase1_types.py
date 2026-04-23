"""Phase 1 tests for shared types, protocols, and config loading."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from luvoire import Action, Memory, Personality, WorldEvent, load_config
from luvoire.protocols import LLMClient, MemoryRetriever, MemoryWriter, PromptRenderable
from luvoire.types import Emotion


def test_personality_requires_unit_interval_traits() -> None:
    with pytest.raises(ValueError, match=r"openness must be between 0\.0 and 1\.0"):
        Personality(
            openness=1.1,
            conscientiousness=0.5,
            extraversion=0.4,
            agreeableness=0.6,
            neuroticism=0.3,
        )


def test_personality_round_trip_with_all_thirty_traits() -> None:
    personality = Personality(
        openness=0.7,
        conscientiousness=0.6,
        extraversion=0.4,
        agreeableness=0.55,
        neuroticism=0.3,
        honesty_humility=0.8,
        machiavellianism=0.2,
        narcissism=0.1,
        psychopathy=0.0,
        sadism=0.0,
        kantianism=0.7,
        humanism=0.8,
        faith_in_humanity=0.6,
        risk_tolerance=0.4,
        locus_of_control=0.7,
        need_for_cognition=0.65,
        trait_empathy=0.75,
        care_harm=0.7,
        fairness=0.8,
        binding_morals=0.5,
        self_direction=0.75,
        stimulation=0.55,
        hedonism=0.45,
        achievement=0.7,
        power=0.3,
        security=0.6,
        conformity=0.4,
        tradition=0.5,
        benevolence=0.8,
        universalism=0.7,
    )

    payload = personality.to_dict()
    restored = Personality.from_dict(payload)

    assert len(payload) == 30
    assert restored.machiavellianism == 0.2
    assert restored.universalism == 0.7


def test_emotion_accepts_pad_boundaries() -> None:
    emotion = Emotion(valence=-1.0, arousal=1.0, dominance=0.0)

    assert emotion.valence == -1.0
    assert emotion.arousal == 1.0
    assert emotion.dominance == 0.0


def test_memory_and_action_imports_work_with_valid_instances() -> None:
    moment = datetime(2026, 4, 18, 9, 30)
    memory = Memory(
        id="mem-001",
        agent_id="alice",
        timestamp=moment,
        content="Shared breakfast with roommate.",
        memory_type="episodic",
        importance=0.75,
        embedding=[0.1, 0.2, 0.3],
    )
    action = Action(
        agent_id="alice",
        timestamp=moment,
        action_type="speak",
        target="bob",
        content="Good morning.",
        location="Dorm Room 201",
    )

    assert memory.embedding == [0.1, 0.2, 0.3]
    assert action.target == "bob"


def test_world_event_rejects_blank_participants() -> None:
    with pytest.raises(ValueError, match="participants\\[1\\] must not be blank"):
        WorldEvent(
            timestamp=datetime(2026, 4, 18, 10, 0),
            event_type="meeting",
            participants=["alice", " "],
            location="Lab A",
            description="Planning session",
        )


def test_load_config_merges_yaml_with_environment_overrides(tmp_path: Path) -> None:
    config_path = tmp_path / "luvoire.yaml"
    config_path.write_text(
        "\n".join(
            [
                "llm:",
                "  primary_provider: anthropic",
                "memory:",
                "  short_term_capacity: 20",
                "runtime:",
                "  tick_duration_minutes: 15",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(
        config_path,
        environ={
            "LUVOIRE_MEMORY__SHORT_TERM_CAPACITY": "32",
            "LUVOIRE_LOGGING__JSON": "true",
            "LUVOIRE_LLM__OPENAI_BASE_URL": "http://localhost:8000/v1",
        },
    )

    assert config.llm.primary_provider == "anthropic"
    assert config.llm.openai_base_url == "http://localhost:8000/v1"
    assert config.memory.short_term_capacity == 32
    assert config.runtime.tick_duration_minutes == 15
    assert config.logging.json_output is True


def test_runtime_protocols_support_structural_typing() -> None:
    class DemoPrompt:
        def to_system_prompt(self) -> str:
            return "You are a dormitory roommate."

    class DemoStore:
        def add(self, memory: Memory) -> None:
            self.last_memory = memory

        def retrieve(
            self,
            query: str,
            k: int = 5,
            recency_bias: float = 0.3,
        ) -> list[Memory]:
            return []

    class DemoLLM:
        def complete(self, messages: list[dict[str, str]], **kwargs: object) -> str:
            return messages[0]["content"]

    assert isinstance(DemoPrompt(), PromptRenderable)
    assert isinstance(DemoStore(), MemoryWriter)
    assert isinstance(DemoStore(), MemoryRetriever)
    assert isinstance(DemoLLM(), LLMClient)
