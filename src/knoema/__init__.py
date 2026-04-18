"""Knoema Engine — LLM-based multi-agent social simulation engine.

Copyright (c) 2026 Celovin. MIT License.
"""

from knoema.benchmark import (
    BenchmarkConfig,
    BenchmarkReport,
    BenchmarkRun,
    ComparisonRow,
    build_comparison_rows,
    build_village_personas,
    format_markdown_report,
    run_knoema_benchmark,
)
from knoema.config import KnoemaConfig, load_config
from knoema.decision import DecisionEngine, decide
from knoema.dsl import Scenario, load_scenario
from knoema.emotion import EmotionState, EmotionStimulus
from knoema.environment import Environment, EnvironmentContext
from knoema.game import NPC, GameSession, NPCResponse
from knoema.llm import (
    AnthropicClient,
    LlamaCppClient,
    LLMCallRecord,
    LLMGateway,
    LocalClient,
    LocalLLMError,
    OllamaClient,
    OpenAIClient,
    VLLMClient,
)
from knoema.memory import (
    HashEmbeddingEncoder,
    MemorySearchResult,
    MemorySummarizer,
    RetrievalWeights,
    ShortTermMemoryBuffer,
    SQLiteFaissMemoryStore,
)
from knoema.persona import Persona
from knoema.prompts import (
    SUPPORTED_PROMPT_LANGUAGES,
    PromptLanguage,
    normalize_prompt_language,
    render_decision_user_prompt,
    render_persona_system_prompt,
)
from knoema.protocols import LLMClient, MemoryRetriever, MemoryWriter, PromptRenderable
from knoema.relationship import InteractionOutcome, Relationship, RelationshipGraph
from knoema.simulator import SimulationLogEntry, Simulator
from knoema.telemetry import (
    NullTelemetryClient,
    TelemetryClient,
    TelemetryEvent,
    TelemetrySettings,
    build_cli_properties,
    build_env_telemetry_client,
    load_or_create_anonymous_id,
    telemetry_opt_in_from_env,
)
from knoema.theory_of_mind import (
    SallyAnneBenchmarkResult,
    SallyAnneCaseResult,
    TheoryOfMindContext,
    TheoryOfMindEngine,
    TheoryOfMindProfile,
    run_sally_anne_benchmark,
)
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

__version__ = "0.1.1"
__author__ = "Celovin"
__license__ = "MIT"

__all__ = [
    "NPC",
    "SUPPORTED_PROMPT_LANGUAGES",
    "Action",
    "AgentID",
    "AnthropicClient",
    "BenchmarkConfig",
    "BenchmarkReport",
    "BenchmarkRun",
    "ComparisonRow",
    "DecisionEngine",
    "Emotion",
    "EmotionState",
    "EmotionStimulus",
    "Environment",
    "EnvironmentContext",
    "GameSession",
    "HashEmbeddingEncoder",
    "InteractionOutcome",
    "KnoemaConfig",
    "LLMCallRecord",
    "LLMClient",
    "LLMGateway",
    "LlamaCppClient",
    "LocalClient",
    "LocalLLMError",
    "Memory",
    "MemoryRetriever",
    "MemorySearchResult",
    "MemorySummarizer",
    "MemoryType",
    "MemoryWriter",
    "NPCResponse",
    "NullTelemetryClient",
    "OllamaClient",
    "OpenAIClient",
    "Persona",
    "Personality",
    "PromptLanguage",
    "PromptRenderable",
    "Relationship",
    "RelationshipGraph",
    "RelationshipType",
    "RetrievalWeights",
    "SQLiteFaissMemoryStore",
    "SallyAnneBenchmarkResult",
    "SallyAnneCaseResult",
    "Scenario",
    "ShortTermMemoryBuffer",
    "SimulationLogEntry",
    "Simulator",
    "TelemetryClient",
    "TelemetryEvent",
    "TelemetrySettings",
    "TheoryOfMindContext",
    "TheoryOfMindEngine",
    "TheoryOfMindProfile",
    "VLLMClient",
    "WorldEvent",
    "__version__",
    "build_cli_properties",
    "build_comparison_rows",
    "build_env_telemetry_client",
    "build_village_personas",
    "decide",
    "format_markdown_report",
    "load_config",
    "load_or_create_anonymous_id",
    "load_scenario",
    "normalize_prompt_language",
    "render_decision_user_prompt",
    "render_persona_system_prompt",
    "run_knoema_benchmark",
    "run_sally_anne_benchmark",
    "telemetry_opt_in_from_env",
]
