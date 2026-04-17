"""Knoema Engine — LLM-based multi-agent social simulation engine.

Copyright (c) 2026 Celovin. MIT License.
"""

from knoema.config import KnoemaConfig, load_config
from knoema.decision import DecisionEngine, decide
from knoema.emotion import EmotionState, EmotionStimulus
from knoema.environment import Environment, EnvironmentContext
from knoema.llm import AnthropicClient, LLMCallRecord, LLMGateway, LocalClient, OpenAIClient
from knoema.memory import (
    HashEmbeddingEncoder,
    MemorySummarizer,
    ShortTermMemoryBuffer,
    SQLiteFaissMemoryStore,
)
from knoema.persona import Persona
from knoema.protocols import LLMClient, MemoryRetriever, MemoryWriter, PromptRenderable
from knoema.relationship import InteractionOutcome, Relationship, RelationshipGraph
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.types import (
    Action,
    AgentID,
    Emotion,
    Memory,
    MemoryType,
    Personality,
    RelationshipType,
    WorldEvent,
)

__version__ = "0.1.0"
__author__ = "Celovin"
__license__ = "MIT"

__all__ = [
    "Action",
    "AgentID",
    "AnthropicClient",
    "DecisionEngine",
    "Emotion",
    "EmotionState",
    "EmotionStimulus",
    "Environment",
    "EnvironmentContext",
    "HashEmbeddingEncoder",
    "InteractionOutcome",
    "KnoemaConfig",
    "LLMCallRecord",
    "LLMClient",
    "LLMGateway",
    "LocalClient",
    "Memory",
    "MemoryRetriever",
    "MemorySummarizer",
    "MemoryType",
    "MemoryWriter",
    "OpenAIClient",
    "Persona",
    "Personality",
    "PromptRenderable",
    "Relationship",
    "RelationshipGraph",
    "RelationshipType",
    "SQLiteFaissMemoryStore",
    "ShortTermMemoryBuffer",
    "SimulationLogEntry",
    "Simulator",
    "WorldEvent",
    "__version__",
    "decide",
    "load_config",
]
