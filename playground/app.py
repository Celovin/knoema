"""Gradio app for the Knoema Playground."""

from __future__ import annotations

import base64
import csv
import hashlib
import json
import math
import tempfile
import threading
import uuid
import zipfile
from collections import Counter
from collections.abc import Generator
from datetime import UTC, datetime
from functools import lru_cache
from html import escape
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, TypeAlias, cast
from urllib.parse import quote

import gradio as gr
import plotly.graph_objects as go
import yaml
from plotly.colors import qualitative
from plotly.subplots import make_subplots
from scipy.stats import chi2_contingency, mannwhitneyu  # type: ignore[import-untyped]
from scipy.stats import t as student_t

from knoema.community import (
    community_gallery_markdown,
    community_scenario_by_id,
    community_scenario_choices,
)
from knoema.export.finetuning import export_finetuning_jsonl
from knoema.reproducibility import generate_run_fingerprint, verification_guide_markdown
from knoema.research import (
    PowerAnalysisPlan,
    ZenodoDepositResult,
    estimate_sample_size,
    submit_zenodo_bundle,
    summarize_seed_tick_effect,
)
from knoema.scenario_synthesis import ScenarioSynthesisError, scenario_to_yaml, synthesize_scenario

try:
    from .analysis.fairness_audit import FairnessAuditReport, audit_trait_action_fairness
    from .hexaco_questionnaire import (
        HEXACO_DOMAINS,
        HEXACO_QUESTIONNAIRE_ITEMS,
        QUESTIONNAIRE_MODE_HEXACO,
        QUESTIONNAIRE_MODE_SLIDERS,
        QUESTIONNAIRE_RESPONSE_DEFAULT,
        derive_personality_from_questionnaire,
        questionnaire_apply_label,
        questionnaire_default_responses,
        questionnaire_domain_items,
        questionnaire_domain_label,
        questionnaire_empty_summary,
        questionnaire_intro_markdown,
        questionnaire_mode_choices,
        questionnaire_mode_label,
        questionnaire_panel_label,
        questionnaire_summary_markdown,
        score_hexaco_questionnaire,
    )
    from .prereg_templates import prereg_template_by_id, prereg_template_choices
    from .simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        AGENT_EDITOR_SLOT_COUNT,
        PERSONA_TRAIT_DEFAULTS,
        PERSONA_TRAIT_FIELDS,
        PlaygroundResult,
        Provider,
        _prepare_playground_run,
        advance_player_session,
        agent_editor_defaults,
        build_playground_hint,
        compute_trait_correlation_study,
        cross_model_action_correlations,
        cross_model_overlap_ratio,
        cultural_prior_choices,
        cultural_prior_trait_values,
        environment_note,
        host_key_active,
        load_environment_presets,
        persona_choices,
        persona_trait_values,
        playground_result_from_artifacts,
        routine_preset_choices,
        routine_preset_text,
        run_cross_model_comparison,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
        scenario_label,
        seed_persona_suggestions,
        start_player_session,
        trait_correlation_summary,
    )
    from .voice import (
        stt_engine_choices,
        synthesize_text_to_audio,
        transcribe_player_audio,
        tts_engine_choices,
    )
except ImportError:  # pragma: no cover - Hugging Face runs app.py as a script.
    from analysis.fairness_audit import FairnessAuditReport, audit_trait_action_fairness
    from hexaco_questionnaire import (
        HEXACO_DOMAINS,
        HEXACO_QUESTIONNAIRE_ITEMS,
        QUESTIONNAIRE_MODE_HEXACO,
        QUESTIONNAIRE_MODE_SLIDERS,
        QUESTIONNAIRE_RESPONSE_DEFAULT,
        derive_personality_from_questionnaire,
        questionnaire_apply_label,
        questionnaire_default_responses,
        questionnaire_domain_items,
        questionnaire_domain_label,
        questionnaire_empty_summary,
        questionnaire_intro_markdown,
        questionnaire_mode_choices,
        questionnaire_mode_label,
        questionnaire_panel_label,
        questionnaire_summary_markdown,
        score_hexaco_questionnaire,
    )
    from prereg_templates import prereg_template_by_id, prereg_template_choices
    from simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        AGENT_EDITOR_SLOT_COUNT,
        PERSONA_TRAIT_DEFAULTS,
        PERSONA_TRAIT_FIELDS,
        PlaygroundResult,
        Provider,
        _prepare_playground_run,
        advance_player_session,
        agent_editor_defaults,
        build_playground_hint,
        compute_trait_correlation_study,
        cross_model_action_correlations,
        cross_model_overlap_ratio,
        cultural_prior_choices,
        cultural_prior_trait_values,
        environment_note,
        host_key_active,
        load_environment_presets,
        persona_choices,
        persona_trait_values,
        playground_result_from_artifacts,
        routine_preset_choices,
        routine_preset_text,
        run_cross_model_comparison,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
        scenario_label,
        seed_persona_suggestions,
        start_player_session,
        trait_correlation_summary,
    )
    from voice import (
        stt_engine_choices,
        synthesize_text_to_audio,
        transcribe_player_audio,
        tts_engine_choices,
    )


STATIC_DIR = Path(__file__).resolve().parent / "static"
FORCE_GRAPH_HTML_PATH = STATIC_DIR / "force_graph.html"
FORCE_GRAPH_VENDOR_PATH = STATIC_DIR / "vendor" / "3d-force-graph.min.js"
FORCE_GRAPH_CDN_URL = (
    "https://cdn.jsdelivr.net/npm/3d-force-graph@1.79.0/dist/3d-force-graph.min.js"
)
if STATIC_DIR.exists():
    gr.set_static_paths(paths=[STATIC_DIR])


KOREAN_CHOICE = "한국어"
LANGUAGE_CHOICES = [KOREAN_CHOICE, "English"]
PLAYGROUND_DEFAULT_SCENARIO = "Office team conflict"
PLAYGROUND_QUICK_START_SCENARIOS = (
    "Dorm: two agents",
    "Village: ten agents",
    PLAYGROUND_DEFAULT_SCENARIO,
)
CROSS_MODEL_CHOICES: tuple[tuple[str, str], ...] = (
    ("GPT", "GPT"),
    ("Claude", "Claude"),
    ("Replay", "Replay"),
)
TUTORIAL_STORAGE_KEY = "knoema_tutorial_completed"
THEME_STORAGE_KEY = "knoema_theme_mode"
TUTORIAL_STEPS = {
    "ko": [
        {
            "selector": "#scenario-dropdown",
            "title": "시나리오 선택",
            "body": "실행할 사회 시나리오를 여기서 고릅니다.",
        },
        {
            "selector": "#environment-preset",
            "title": "환경 프리셋",
            "body": "지리, 시간대, 군중감 같은 기본 맥락을 빠르게 바꿉니다.",
        },
        {
            "selector": "#agent-count-slider",
            "title": "에이전트 수",
            "body": "시나리오 기본값을 덮어쓰고 참여 인원을 조정합니다.",
        },
        {
            "selector": "#extended-personality-panel",
            "title": "성격 차원",
            "body": "Big Five와 확장 성격 차원을 tier별로 조정합니다.",
        },
        {
            "selector": "#mode-radio",
            "title": "실행 모드",
            "body": "Replay only는 API 키 없이도 결정론적으로 재생됩니다.",
        },
        {
            "selector": "#run-button",
            "title": "실행",
            "body": "현재 설정으로 시뮬레이션을 시작합니다.",
        },
        {
            "selector": "#relationship-graph",
            "title": "관계 그래프",
            "body": "3D 관계 그래프와 타임라인으로 결과를 읽습니다.",
        },
        {
            "selector": "#export-panel",
            "title": "내보내기",
            "body": "로그 다운로드와 후속 분석용 아티팩트가 이 영역에 모입니다.",
        },
    ],
    "en": [
        {
            "selector": "#scenario-dropdown",
            "title": "Pick a scenario",
            "body": "Choose the social situation you want to replay.",
        },
        {
            "selector": "#environment-preset",
            "title": "Environment preset",
            "body": "Swap the geographic and temporal context without editing YAML.",
        },
        {
            "selector": "#agent-count-slider",
            "title": "Agent count",
            "body": "Override the scenario default and scale the cast up or down.",
        },
        {
            "selector": "#extended-personality-panel",
            "title": "Personality dimensions",
            "body": "Big Five and the extended trait tiers live in this area.",
        },
        {
            "selector": "#mode-radio",
            "title": "Mode",
            "body": "Replay only runs without an API key.",
        },
        {
            "selector": "#run-button",
            "title": "Run",
            "body": "Start the simulation with the current controls.",
        },
        {
            "selector": "#relationship-graph",
            "title": "Relationship graph",
            "body": "Read the 3D graph and timeline to inspect the run.",
        },
        {
            "selector": "#export-panel",
            "title": "Export",
            "body": "Downloads and exported artifacts are collected here.",
        },
    ],
}


TRAIT_COPY = {
    "openness": {
        "ko": {
            "label": "개방성",
            "info": "새로운 경험과 변화에 얼마나 열려 있는지 나타냅니다.",
        },
        "en": {
            "label": "Openness",
            "info": "Curiosity and openness to new experience. Higher = more receptive to change.",
        },
    },
    "conscientiousness": {
        "ko": {
            "label": "성실성",
            "info": "계획성, 자기통제, 목표 지속성을 나타냅니다.",
        },
        "en": {
            "label": "Conscientiousness",
            "info": "Self-discipline and goal-directedness. Higher = more consistent follow-through.",
        },
    },
    "extraversion": {
        "ko": {
            "label": "외향성",
            "info": "사교성과 자극 추구 성향을 나타냅니다.",
        },
        "en": {
            "label": "Extraversion",
            "info": "Sociability and stimulation seeking. Higher = energized by people and events.",
        },
    },
    "agreeableness": {
        "ko": {
            "label": "친화성",
            "info": "협력성과 공감, 배려 성향을 나타냅니다.",
        },
        "en": {
            "label": "Agreeableness",
            "info": "Cooperation and empathy. Higher = avoids conflict and prioritizes others.",
        },
    },
    "neuroticism": {
        "ko": {
            "label": "정서 불안정성",
            "info": "스트레스와 부정 정서에 얼마나 민감한지 나타냅니다.",
        },
        "en": {
            "label": "Emotional volatility (Neuroticism)",
            "info": "Sensitivity to stress and negative emotion. Higher = more frequent worry or irritation.",
        },
    },
    "honesty_humility": {
        "ko": {
            "label": "정직-겸손 (HEXACO)",
            "info": "진실성, 공정성, 지위 남용 억제를 나타냅니다.",
        },
        "en": {
            "label": "Honesty-Humility (HEXACO)",
            "info": "Sincerity, fairness, and resistance to status exploitation. Higher = less willing to deceive or dominate.",
        },
    },
    "machiavellianism": {
        "ko": {
            "label": "마키아벨리즘 (Dark Tetrad)",
            "info": "전략적 조작과 수단적 계산 성향을 나타냅니다.",
        },
        "en": {
            "label": "Machiavellianism (Dark Tetrad)",
            "info": "Strategic manipulation and instrumental reasoning. Higher = more willing to exploit others for goals.",
        },
    },
    "narcissism": {
        "ko": {
            "label": "나르시시즘 (Dark Tetrad)",
            "info": "과시, 특권의식, 인정 욕구를 나타냅니다.",
        },
        "en": {
            "label": "Narcissism (Dark Tetrad)",
            "info": "Need for admiration and self-importance. Higher = stronger status seeking and ego defense.",
        },
    },
    "psychopathy": {
        "ko": {
            "label": "사이코패시 (Dark Tetrad)",
            "info": "충동성, 냉담함, 낮은 죄책감을 나타냅니다.",
        },
        "en": {
            "label": "Psychopathy (Dark Tetrad)",
            "info": "Callousness, impulsivity, and low remorse. Higher = more reckless, consequence-blind action.",
        },
    },
    "sadism": {
        "ko": {
            "label": "사디즘 (Dark Tetrad)",
            "info": "타인의 고통에 대한 둔감함과 가학적 선택 경향을 나타냅니다.",
        },
        "en": {
            "label": "Sadism (Dark Tetrad)",
            "info": "Comfort with others' pain. Higher = more likely to select cruel or punitive behavior.",
        },
    },
    "kantianism": {
        "ko": {
            "label": "칸트주의 (Light Triad)",
            "info": "타인을 수단이 아닌 목적으로 대하려는 성향입니다.",
        },
        "en": {
            "label": "Kantianism (Light Triad)",
            "info": "Treats others as ends, not just means. Higher = stronger respect for autonomy and dignity.",
        },
    },
    "humanism": {
        "ko": {
            "label": "인본주의 (Light Triad)",
            "info": "모든 사람의 존엄과 가치를 중시하는 정도입니다.",
        },
        "en": {
            "label": "Humanism (Light Triad)",
            "info": "Views people as worthy of care and dignity. Higher = more equal regard for others.",
        },
    },
    "faith_in_humanity": {
        "ko": {
            "label": "인간 신뢰 (Light Triad)",
            "info": "타인의 선의와 협력을 기본적으로 신뢰하는 정도입니다.",
        },
        "en": {
            "label": "Faith in humanity (Light Triad)",
            "info": "Default trust in others' goodwill. Higher = expects cooperation and good intent.",
        },
    },
    "risk_tolerance": {
        "ko": {
            "label": "위험 감수성",
            "info": "불확실성을 감수하고 더 큰 변동성을 받아들이는 정도입니다.",
        },
        "en": {
            "label": "Risk tolerance",
            "info": "Comfort with uncertain outcomes. Higher = accepts bolder moves.",
        },
    },
    "locus_of_control": {
        "ko": {
            "label": "통제 위치",
            "info": "결과가 자신의 행동으로 바뀐다고 믿는 정도입니다.",
        },
        "en": {
            "label": "Locus of control",
            "info": "Belief that outcomes can be shaped by one's own actions. Higher = more internal control orientation.",
        },
    },
    "need_for_cognition": {
        "ko": {
            "label": "인지 욕구",
            "info": "복잡한 사고와 분석 자체를 즐기는 정도입니다.",
        },
        "en": {
            "label": "Need for cognition",
            "info": "Enjoyment of analysis and deep thinking. Higher = more reflective, deliberative reasoning.",
        },
    },
    "trait_empathy": {
        "ko": {
            "label": "특성 공감",
            "info": "타인의 감정을 자동적으로 읽고 맞추는 경향입니다.",
        },
        "en": {
            "label": "Trait empathy",
            "info": "Baseline sensitivity to others' feelings. Higher = more automatic emotional attunement.",
        },
    },
    "care_harm": {
        "ko": {
            "label": "배려 / 위해 회피",
            "info": "타인을 보호하고 해를 줄이려는 우선순위입니다.",
        },
        "en": {
            "label": "Care / Harm avoidance",
            "info": "Priority on protecting others from harm. Higher = reduces punitive or indifferent choices.",
        },
    },
    "fairness": {
        "ko": {
            "label": "공정성",
            "info": "상호성, 정의, 동등 대우를 중시하는 정도입니다.",
        },
        "en": {
            "label": "Fairness",
            "info": "Priority on reciprocity, justice, and equal treatment. Higher = resists favoritism.",
        },
    },
    "binding_morals": {
        "ko": {
            "label": "결속 도덕",
            "info": "충성, 권위, 신성 같은 집단 결속 규범을 중시하는 정도입니다.",
        },
        "en": {
            "label": "Binding morals",
            "info": "Priority on loyalty, authority, and sanctity. Higher = values cohesion and norm protection.",
        },
    },
    "self_direction": {
        "ko": {
            "label": "자기 지향",
            "info": "자율성, 창의성, 독립 판단을 중시하는 정도입니다.",
        },
        "en": {
            "label": "Self-direction",
            "info": "Values autonomy, creativity, and independent judgment. Higher = more self-directed exploration.",
        },
    },
    "stimulation": {
        "ko": {
            "label": "자극",
            "info": "새로움, 흥분, 도전을 얼마나 추구하는지 나타냅니다.",
        },
        "en": {
            "label": "Stimulation",
            "info": "Values novelty, excitement, and challenge. Higher = seeks dynamic situations.",
        },
    },
    "hedonism": {
        "ko": {
            "label": "쾌락",
            "info": "즐거움과 감각적 만족을 우선하는 정도입니다.",
        },
        "en": {
            "label": "Hedonism",
            "info": "Values pleasure and enjoyment. Higher = prioritizes comfort and immediate reward.",
        },
    },
    "achievement": {
        "ko": {
            "label": "성취",
            "info": "성과, 유능함, 사회적 인정 획득을 중시하는 정도입니다.",
        },
        "en": {
            "label": "Achievement",
            "info": "Values competence, success, and visible accomplishment. Higher = pursues performance goals.",
        },
    },
    "power": {
        "ko": {
            "label": "권력",
            "info": "영향력, 지위, 자원 통제를 추구하는 정도입니다.",
        },
        "en": {
            "label": "Power",
            "info": "Values status, influence, and control over resources. Higher = seeks leverage and rank.",
        },
    },
    "security": {
        "ko": {
            "label": "안전",
            "info": "예측 가능성과 안정, 질서 유지를 중시하는 정도입니다.",
        },
        "en": {
            "label": "Security",
            "info": "Values safety, stability, and predictability. Higher = favors orderly low-risk paths.",
        },
    },
    "conformity": {
        "ko": {
            "label": "순응",
            "info": "규칙 준수와 자기 억제를 중시하는 정도입니다.",
        },
        "en": {
            "label": "Conformity",
            "info": "Values rule-following and restraint. Higher = suppresses disruptive or norm-breaking acts.",
        },
    },
    "tradition": {
        "ko": {
            "label": "전통",
            "info": "문화와 관습의 지속성을 중시하는 정도입니다.",
        },
        "en": {
            "label": "Tradition",
            "info": "Values inherited customs and cultural continuity. Higher = defers to established practices.",
        },
    },
    "benevolence": {
        "ko": {
            "label": "박애 (Benevolence)",
            "info": "가까운 사람들의 안녕을 지키려는 경향입니다.",
        },
        "en": {
            "label": "Benevolence",
            "info": "Values the welfare of close others. Higher = protects people in the local circle.",
        },
    },
    "universalism": {
        "ko": {
            "label": "보편주의",
            "info": "집단 바깥까지 포함한 정의와 포용을 중시하는 정도입니다.",
        },
        "en": {
            "label": "Universalism",
            "info": "Values welfare across all people and nature. Higher = prioritizes justice and inclusiveness beyond the in-group.",
        },
    },
}

BASE_LABELS = {
    "ko": {
        "header": (
            "# Knoema Playground\n\n"
            "브라우저에서 지속형 에이전트 시뮬레이션을 실행합니다. **재생 전용**은 API 키 없이 결정론적 데모로 동작하고, "
            "OpenAI 또는 Anthropic 키를 입력하면 실시간 LLM 호출을 사용할 수 있습니다. API 키는 현재 요청에만 사용되며 디스크에 저장되지 않습니다."
        ),
        "scenario": "시나리오",
        "environment": "환경 프리셋",
        "environment_default": "university_dorm_evening",
        "environment_info": "지리, 시간대, 가시성, 군집감 같은 기본 맥락을 빠르게 바꾸는 프리셋입니다.",
        "mode": "모드",
        "replay": "재생 전용",
        "api_key": "API 키",
        "api_key_ph": "OpenAI/Anthropic 사용 시 입력, 재생 전용이면 비워 두세요",
        "model": "모델",
        "agent_panel": "주요 에이전트 성격",
        "extended_panel": "확장 성격 차원",
        "extended_panel_note": "추가 25개 차원을 tier별로 조정합니다. 기본값은 학술 중립값입니다.",
        "tier_a_panel": "Tier A - 기본 성격 (Big Five)",
        "tier_bd_panel": "Tier B+D - 도덕성 (HEXACO + Light Triad)",
        "tier_c_panel": "Tier C - 병리 성격 (Dark Tetrad)",
        "tier_e_panel": "Tier E - 행동 성향",
        "tier_f_panel": "Tier F - 도덕 기반",
        "tier_g_panel": "Tier G - 보편적 가치관 (Schwartz 10)",
        "dark_tetrad_notice": (
            "<div class='knoema-muted'>병리 성격 차원은 학술 연구와 가상 시나리오 재현 목적에 한해 노출됩니다.</div>"
        ),
        "name": "이름",
        "age": "나이",
        "persona_preset": "성격 아키타입",
        "persona_preset_info": "25개 연구용 아키타입 벡터 중 하나를 불러와 현재 슬라이더를 채웁니다.",
        "agents": "에이전트 수",
        "agents_info": "시나리오 기본값을 넘기면 마지막 에이전트를 바탕으로 추가 인물을 자동 생성합니다.",
        "ticks": "틱 수",
        "run": "시뮬레이션 실행",
        "summary": "실행 요약",
        "action_chart": "액션 타입 분해도",
        "tick_scrubber": "틱 스크러버",
        "tick_focus": "선택된 틱",
        "tick_focus_empty": "아직 선택된 틱 정보가 없습니다.",
        "timeline": "타임라인",
        "graph": "관계 그래프",
        "export_panel": "결과 내보내기",
        "jsonl": "JSONL 로그",
        "download": "JSONL 다운로드",
        "lang": "언어",
    },
    "en": {
        "header": (
            "# Knoema Playground\n\n"
            "Run a short persistent-agent simulation in the browser. Use **Replay only** for a deterministic no-key demo, "
            "or provide your own API key for a live LLM-backed run. API keys are used only for the current request and are not written to disk."
        ),
        "scenario": "Scenario",
        "environment": "Environment preset",
        "environment_default": "university_dorm_evening",
        "environment_info": "Geographic, temporal, visibility, and crowding context. All locations are fictional composites.",
        "mode": "Mode",
        "replay": "Replay only",
        "api_key": "API key",
        "api_key_ph": "Required for OpenAI/Anthropic, leave blank for Replay only",
        "model": "Model",
        "agent_panel": "Primary agent personality",
        "extended_panel": "Extended personality dimensions",
        "extended_panel_note": "Tune 25 additional dimensions grouped by academic tier. Defaults start at neutral values.",
        "tier_a_panel": "Tier A - Big Five",
        "tier_bd_panel": "Tier B+D - HEXACO + Light Triad",
        "tier_c_panel": "Tier C - Dark Tetrad",
        "tier_e_panel": "Tier E - Behavioral dispositions",
        "tier_f_panel": "Tier F - Moral foundations",
        "tier_g_panel": "Tier G - Schwartz 10 values",
        "dark_tetrad_notice": (
            "<div class='knoema-muted'>Dark Tetrad dimensions are exposed for academic research and fictional scenario replay only.</div>"
        ),
        "name": "Name",
        "age": "Age",
        "persona_preset": "Persona archetype",
        "persona_preset_info": "Load one of 25 research-oriented archetype vectors as a starting point for the current sliders.",
        "agents": "Agents",
        "agents_info": "How many agents take part. Extras above the scenario default are auto-generated.",
        "ticks": "Ticks",
        "run": "Run simulation",
        "summary": "Run summary",
        "action_chart": "Action type breakdown",
        "tick_scrubber": "Tick scrubber",
        "tick_focus": "Tick focus",
        "tick_focus_empty": "No tick focus data yet.",
        "memory_inspector": "Memory inspector",
        "memory_agent": "Agent",
        "memory_empty": "No memory snapshot yet.",
        "memory_batch": "Batch mode aggregates multiple seeds. Run a single simulation to inspect per-agent memories.",
        "memory_short_term": "Short-term memory",
        "memory_short_term_empty": "No short-term memories yet.",
        "memory_long_term": "Retrieved long-term memory",
        "memory_long_term_empty": "No long-term retrievals yet.",
        "memory_monologue": "Inner monologue",
        "memory_monologue_empty": "No inner monologues yet.",
        "memory_emotion": "Emotion trajectory",
        "memory_emotion_empty": "No emotion trajectory yet.",
        "memory_multi_hint": "Showing memory details for the first selected agent. The chart includes every selected agent.",
        "spatial_heatmap_panel": "Spatial heatmap",
        "spatial_heatmap": "Spatial heatmap",
        "spatial_heatmap_empty": "No spatial occupancy data yet.",
        "spatial_heatmap_batch": "Spatial heatmap is available in single-run mode only.",
        "action_flow_panel": "Action flow",
        "action_flow": "Action flow",
        "action_flow_empty": "No action flow data yet.",
        "action_flow_batch": "Action flow is available in single-run mode only.",
        "mini_map_panel": "2D mini-map",
        "mini_map": "2D mini-map",
        "mini_map_empty": "No location data yet.",
        "mini_map_batch": "2D mini-map is available in single-run mode only.",
        "timeline": "Timeline",
        "threads_tab": "Conversation threads",
        "threads_empty": "No conversation threads yet. Run a scenario with directed speech to group replies together.",
        "threads_batch": "Conversation threads are available in single-run mode only.",
        "graph": "Relationship graph",
        "export_panel": "Result exports",
        "jsonl": "JSONL log",
        "download": "Download JSONL",
        "lang": "Language",
    },
}


def _build_labels() -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    for language, base in BASE_LABELS.items():
        merged = dict(base)
        for field_name, localized in TRAIT_COPY.items():
            merged[field_name] = localized[language]["label"]
            merged[f"{field_name}_info"] = localized[language]["info"]
        labels[language] = merged
    return labels


LABELS = _build_labels()
LABELS["ko"]["html_report_button"] = "HTML 보고서 내보내기"
LABELS["ko"]["html_report_download"] = "HTML 보고서 다운로드"
LABELS["ko"]["html_report_title"] = "Knoema Playground HTML 보고서"
LABELS["ko"]["generated_at"] = "생성 시각"
LABELS["ko"]["csv_bundle_button"] = "CSV 묶음 내보내기"
LABELS["ko"]["csv_bundle_download"] = "CSV 묶음 다운로드"
LABELS["ko"]["finetuning_format"] = "파인튜닝 포맷"
LABELS["ko"]["finetuning_button"] = "파인튜닝 데이터 내보내기"
LABELS["ko"]["finetuning_download"] = "파인튜닝 JSONL 다운로드"
LABELS["ko"]["latex_table_button"] = "LaTeX 표 내보내기"
LABELS["ko"]["latex_table_download"] = "LaTeX 표 다운로드"
LABELS["en"]["html_report_button"] = "Export HTML report"
LABELS["en"]["html_report_download"] = "Download HTML report"
LABELS["en"]["html_report_title"] = "Knoema Playground HTML report"
LABELS["en"]["generated_at"] = "Generated at"
LABELS["en"]["csv_bundle_button"] = "Export CSV bundle"
LABELS["en"]["csv_bundle_download"] = "Download CSV bundle"
LABELS["en"]["finetuning_format"] = "Fine-tuning format"
LABELS["en"]["finetuning_button"] = "Export fine-tuning dataset"
LABELS["en"]["finetuning_download"] = "Download fine-tuning JSONL"
LABELS["en"]["latex_table_button"] = "Export LaTeX table"
LABELS["en"]["latex_table_download"] = "Download LaTeX table"
LABELS["ko"]["mirofish_panel"] = "고급 페르소나 랩"
LABELS["ko"]["seed_prompt"] = "시드 프롬프트"
LABELS["ko"]["seed_prompt_placeholder"] = "예: 분주한 항구 술집, 세 명의 NPC, 경쟁과 협력"
LABELS["ko"]["seed_prompt_apply"] = "시드로 3명 페르소나 생성"
LABELS["ko"]["seed_prompt_empty"] = "시드 프롬프트를 입력하면 첫 3명 에이전트와 초기 관계 초안을 채웁니다."
LABELS["ko"]["scenario_synthesis_panel"] = "자연어 시나리오 생성"
LABELS["ko"]["scenario_synthesis_input"] = "시나리오 설명"
LABELS["ko"]["scenario_synthesis_placeholder"] = "예: 중세 시장에서 상인 3명과 고객 2명이 가격을 협상한다"
LABELS["ko"]["scenario_synthesis_button"] = "시나리오 생성"
LABELS["ko"]["scenario_synthesis_empty"] = "상황을 설명하면 에이전트 초안, 이벤트, YAML을 생성합니다."
LABELS["ko"]["community_gallery_panel"] = "커뮤니티 시나리오 갤러리"
LABELS["ko"]["community_gallery_scenario"] = "커뮤니티 시나리오"
LABELS["ko"]["community_gallery_load"] = "선택한 시나리오 불러오기"
LABELS["ko"]["community_gallery_empty"] = "GitHub 기반 커뮤니티 시나리오를 선택해 Playground 초안으로 불러옵니다."
LABELS["ko"]["event_injections"] = "이벤트 주입"
LABELS["ko"]["event_injections_placeholder"] = (
    "0 | Tavern Bar | 전령이 봉인된 편지를 들고 뛰어든다 | agent_1,agent_2 | urgent_news"
)
LABELS["ko"]["initial_relationships"] = "초기 관계 시드"
LABELS["ko"]["initial_relationships_placeholder"] = "agent_1 | agent_2 | 동료 | 0.55 | 0.70 | 0.30"
LABELS["ko"]["live_streaming"] = "실시간 WebSocket 스트리밍"
LABELS["ko"]["live_streaming_info"] = "재생 전용 모드에서 틱 단위로 UI를 갱신합니다."
LABELS["ko"]["theme"] = "테마"
LABELS["ko"]["theme_info"] = "라이트, 다크, 자동 중 하나를 선택하고 브라우저에 저장합니다."
LABELS["ko"]["theme_auto"] = "자동"
LABELS["ko"]["theme_light"] = "라이트"
LABELS["ko"]["theme_dark"] = "다크"
LABELS["ko"]["graph_a11y"] = "관계 그래프 요약"
LABELS["ko"]["report_agent_panel"] = "ReportAgent 질의응답"
LABELS["ko"]["report_agent_question"] = "실행 질문"
LABELS["ko"]["report_agent_run"] = "현재 실행 요약 답변"
LABELS["ko"]["report_agent_empty"] = "시뮬레이션을 실행한 뒤 질문하면 JSONL 기반 요약을 돌려줍니다."
LABELS["ko"]["competitive_panel"] = "경쟁 비교"
LABELS["ko"]["competitive_intro"] = "연구용 사회 시뮬레이션, 예측 샌드박스, 오케스트레이션 프레임워크를 같은 표면에서 비교합니다."
LABELS["ko"]["compare_panel"] = "A/B 비교"
LABELS["ko"]["compare_seed_a"] = "비교 시드 A"
LABELS["ko"]["compare_seed_b"] = "비교 시드 B"
LABELS["ko"]["compare_button"] = "두 시드 비교"
LABELS["ko"]["compare_empty"] = "같은 설정으로 두 시드를 돌려 차이를 비교합니다."
LABELS["ko"]["cross_model_panel"] = "모델 비교"
LABELS["ko"]["cross_model_models"] = "비교할 모델"
LABELS["ko"]["cross_model_button"] = "모델 A/B/C 비교 실행"
LABELS["ko"]["cross_model_empty"] = "같은 시나리오를 GPT, Claude, Replay로 나란히 실행합니다."
LABELS["ko"]["cross_model_diff"] = "모델 간 차이"
LABELS["ko"]["fairness_panel"] = "공정성 / 편향 감사"
LABELS["ko"]["fairness_plot"] = "trait-action 효과 크기 히트맵"
LABELS["ko"]["fairness_empty"] = "실행 후 trait-action 편향 신호를 여기서 점검합니다."
LABELS["ko"]["repro_certificate_button"] = "재현성 인증서 내보내기"
LABELS["ko"]["repro_certificate_download"] = "재현성 인증서 다운로드"
LABELS["ko"]["interview_panel"] = "에이전트 인터뷰"
LABELS["ko"]["interview_agent"] = "에이전트 ID"
LABELS["ko"]["interview_question"] = "인터뷰 질문"
LABELS["ko"]["interview_button"] = "인터뷰 생성"
LABELS["ko"]["interview_empty"] = "런 이후 에이전트 ID와 질문을 넣으면 최근 기억과 행동을 바탕으로 답변합니다."
LABELS["en"]["mirofish_panel"] = "Advanced persona lab"
LABELS["en"]["seed_prompt"] = "Seed prompt"
LABELS["en"]["seed_prompt_placeholder"] = "Example: a crowded harbor tavern with three NPCs balancing rivalry and cooperation"
LABELS["en"]["seed_prompt_apply"] = "Generate three personas from seed"
LABELS["en"]["seed_prompt_empty"] = "Enter a seed prompt to fill the first three agent editors and draft initial relationship seeds."
LABELS["en"]["scenario_synthesis_panel"] = "Generate scenario from natural language"
LABELS["en"]["scenario_synthesis_input"] = "Describe your scenario"
LABELS["en"]["scenario_synthesis_placeholder"] = "Example: a medieval market where 3 merchants and 2 customers negotiate prices"
LABELS["en"]["scenario_synthesis_button"] = "Generate scenario"
LABELS["en"]["scenario_synthesis_empty"] = "Describe a situation to draft agents, events, and YAML."
LABELS["en"]["community_gallery_panel"] = "Community scenario gallery"
LABELS["en"]["community_gallery_scenario"] = "Community scenario"
LABELS["en"]["community_gallery_load"] = "Load selected scenario"
LABELS["en"]["community_gallery_empty"] = "Choose a GitHub-backed community scenario and load it as a Playground draft."
LABELS["en"]["event_injections"] = "Event injections"
LABELS["en"]["event_injections_placeholder"] = "0 | Tavern Bar | A courier bursts in with a sealed letter | agent_1,agent_2 | urgent_news"
LABELS["en"]["initial_relationships"] = "Initial relationship seeds"
LABELS["en"]["initial_relationships_placeholder"] = "agent_1 | agent_2 | colleague | 0.55 | 0.70 | 0.30"
LABELS["en"]["live_streaming"] = "Live WebSocket streaming"
LABELS["en"]["live_streaming_info"] = "In Replay only mode, update the UI once per tick through the Phase 44 stream route."
LABELS["en"]["theme"] = "Theme"
LABELS["en"]["theme_info"] = "Choose Light, Dark, or Auto and persist the preference in local storage."
LABELS["en"]["theme_auto"] = "Auto"
LABELS["en"]["theme_light"] = "Light"
LABELS["en"]["theme_dark"] = "Dark"
LABELS["en"]["graph_a11y"] = "Graph summary"
LABELS["en"]["report_agent_panel"] = "ReportAgent Q&A"
LABELS["en"]["report_agent_question"] = "Run question"
LABELS["en"]["report_agent_run"] = "Answer from current run"
LABELS["en"]["report_agent_empty"] = "Run a scenario first, then ask a question to get a JSONL-grounded summary."
LABELS["en"]["competitive_panel"] = "Competitive comparison"
LABELS["en"]["competitive_intro"] = "Compare research simulators, prediction sandboxes, and orchestration frameworks side by side."
LABELS["ko"]["prereg_panel"] = "OSF 사전등록"
LABELS["ko"]["prereg_template"] = "템플릿 라이브러리"
LABELS["ko"]["prereg_title"] = "연구 제목"
LABELS["ko"]["prereg_hypotheses"] = "가설 / 연구 질문"
LABELS["ko"]["prereg_design"] = "연구 설계"
LABELS["ko"]["prereg_outcomes"] = "주요 / 보조 지표"
LABELS["ko"]["prereg_analysis"] = "분석 계획"
LABELS["ko"]["prereg_freeze"] = "실행 후 파라미터 고정"
LABELS["ko"]["prereg_deviations"] = "일탈 로그"
LABELS["ko"]["prereg_button"] = "사전등록 내보내기"
LABELS["ko"]["prereg_download"] = "사전등록 다운로드"
LABELS["ko"]["prereg_preview_empty"] = "연구 정보로 OSF 사전등록 초안을 미리 봅니다."
LABELS["en"]["prereg_panel"] = "OSF pre-registration"
LABELS["en"]["prereg_template"] = "Pick from template library"
LABELS["en"]["prereg_title"] = "Study title"
LABELS["en"]["prereg_hypotheses"] = "Hypotheses / research questions"
LABELS["en"]["prereg_design"] = "Study design"
LABELS["en"]["prereg_outcomes"] = "Primary / secondary outcomes"
LABELS["en"]["prereg_analysis"] = "Analysis plan"
LABELS["en"]["prereg_freeze"] = "Freeze parameters after run"
LABELS["en"]["prereg_deviations"] = "Deviation log"
LABELS["en"]["prereg_button"] = "Export pre-registration"
LABELS["en"]["prereg_download"] = "Download pre-registration"
LABELS["en"]["prereg_preview_empty"] = "Preview the OSF-style registration draft here."
LABELS["ko"]["prereg_planned_n"] = "계획 표본수"
LABELS["ko"]["prereg_power_test"] = "검정력 분석 검정"
LABELS["ko"]["prereg_power_effect"] = "효과 크기"
LABELS["ko"]["prereg_power_alpha"] = "유의수준"
LABELS["ko"]["prereg_power_target"] = "목표 검정력"
LABELS["ko"]["prereg_power_summary"] = "검정력 분석 요약"
LABELS["en"]["prereg_planned_n"] = "Planned sample size"
LABELS["en"]["prereg_power_test"] = "Power analysis test"
LABELS["en"]["prereg_power_effect"] = "Effect size"
LABELS["en"]["prereg_power_alpha"] = "Alpha"
LABELS["en"]["prereg_power_target"] = "Target power"
LABELS["en"]["prereg_power_summary"] = "Power analysis summary"
LABELS["ko"]["replication_button"] = "재현 패키지 내보내기"
LABELS["ko"]["replication_download"] = "재현 패키지 다운로드"
LABELS["en"]["replication_button"] = "Export replication package"
LABELS["en"]["replication_download"] = "Download replication package"
LABELS["ko"]["reviewer_mode"] = "리뷰어 모드"
LABELS["ko"]["prereg_data_generation"] = "데이터 생성 절차"
LABELS["ko"]["prereg_factor_design"] = "요인 설계 행렬"
LABELS["ko"]["prereg_performance_metrics"] = "성능 지표"
LABELS["ko"]["prereg_aggregation"] = "집계 계획"
LABELS["en"]["prereg_data_generation"] = "Data generation process"
LABELS["en"]["prereg_factor_design"] = "Factor design matrix"
LABELS["en"]["prereg_performance_metrics"] = "Performance metrics"
LABELS["en"]["prereg_aggregation"] = "Aggregation plan"
LABELS["ko"]["deposit_panel"] = "Zenodo / arXiv 등록"
LABELS["ko"]["deposit_creators"] = "저자 정보 (줄바꿈 구분, 선택 | 소속)"
LABELS["ko"]["deposit_description"] = "데이터셋 설명"
LABELS["ko"]["deposit_keywords"] = "키워드"
LABELS["ko"]["deposit_token"] = "Zenodo 접근 토큰"
LABELS["ko"]["deposit_sandbox"] = "Zenodo 샌드박스 사용"
LABELS["ko"]["deposit_publish"] = "업로드 직후 즉시 공개"
LABELS["ko"]["deposit_button"] = "등록 패킷 만들기"
LABELS["ko"]["deposit_download"] = "등록 번들 다운로드"
LABELS["ko"]["deposit_status"] = "아직 등록 패킷이 없습니다."
LABELS["en"]["deposit_panel"] = "Zenodo / arXiv deposit"
LABELS["en"]["deposit_creators"] = "Creators (one per line, optional | affiliation)"
LABELS["en"]["deposit_description"] = "Dataset description"
LABELS["en"]["deposit_keywords"] = "Keywords"
LABELS["en"]["deposit_token"] = "Zenodo access token"
LABELS["en"]["deposit_sandbox"] = "Use Zenodo sandbox"
LABELS["en"]["deposit_publish"] = "Publish immediately after upload"
LABELS["en"]["deposit_button"] = "Create deposit packet"
LABELS["en"]["deposit_download"] = "Download deposit bundle"
LABELS["en"]["deposit_status"] = "No deposit packet yet."
LABELS["en"]["reviewer_mode"] = "Reviewer mode"
LABELS["ko"]["advanced_research_mode"] = "고급 연구 모드"
LABELS["ko"]["advanced_research_ack"] = "IRB 형식의 가상 연구 고지에 동의합니다."
LABELS["ko"]["advanced_research_notice"] = (
    "Dark Tetrad 컨트롤과 민감한 가상 시나리오가 활성화됩니다. "
    "합성 데이터 또는 완전 동의를 받은 데이터에서만 사용하고, IRB/심사 기록을 남기며, 운영 주장(operational claims)은 피하세요."
)
LABELS["ko"]["advanced_research_locked"] = "고급 연구 모드는 Dark Tetrad 슬라이더와 민감한 시나리오를 숨겨 둡니다."
LABELS["en"]["advanced_research_mode"] = "Advanced research mode"
LABELS["en"]["advanced_research_ack"] = "I acknowledge the IRB-style fictional-research notice."
LABELS["en"]["advanced_research_notice"] = (
    "This unlocks Dark Tetrad controls and sensitive fictional scenarios. "
    "Use only with synthetic or fully consented data, record IRB/review notes, and avoid operational claims."
)
LABELS["en"]["advanced_research_locked"] = "Advanced research mode keeps Dark Tetrad sliders and sensitive scenarios hidden."
LABELS["en"]["compare_panel"] = "A/B compare"
LABELS["en"]["compare_seed_a"] = "Compare seed A"
LABELS["en"]["compare_seed_b"] = "Compare seed B"
LABELS["en"]["compare_button"] = "Compare two seeds"
LABELS["en"]["compare_empty"] = "Run the current setup twice with two seeds and inspect the delta."
LABELS["en"]["cross_model_panel"] = "Compare models"
LABELS["en"]["cross_model_models"] = "Models"
LABELS["en"]["cross_model_button"] = "Run model A/B/C compare"
LABELS["en"]["cross_model_empty"] = "Run the same scenario through GPT, Claude, and Replay side by side."
LABELS["en"]["cross_model_diff"] = "Cross-model differences"
LABELS["en"]["fairness_panel"] = "Bias audit"
LABELS["en"]["fairness_plot"] = "Trait-action effect size heatmap"
LABELS["en"]["fairness_empty"] = "Run a scenario to inspect trait-action fairness and bias signals."
LABELS["en"]["repro_certificate_button"] = "Export reproducibility certificate"
LABELS["en"]["repro_certificate_download"] = "Download reproducibility certificate"
LABELS["en"]["interview_panel"] = "Agent interview"
LABELS["en"]["interview_agent"] = "Agent ID"
LABELS["en"]["interview_question"] = "Interview question"
LABELS["en"]["interview_button"] = "Generate interview"
LABELS["en"]["interview_empty"] = "After a run, provide an agent id and question to synthesize an answer from recent memories and actions."
LABELS["ko"]["cultural_prior"] = "문화 사전 분포"
LABELS["ko"]["cultural_prior_info"] = "선택한 문화 모듈이 Schwartz 가치와 도덕 기반의 기본값을 먼저 이동시킵니다."
LABELS["ko"]["monologue_panel"] = "내적 독백"
LABELS["ko"]["monologue_empty"] = "아직 기록된 내적 독백이 없습니다."
LABELS["en"]["cultural_prior"] = "Cultural prior"
LABELS["en"]["cultural_prior_info"] = (
    "The selected cultural module shifts Schwartz and moral-foundation defaults before any archetype override."
)
LABELS["en"]["monologue_panel"] = "Inner monologue"
LABELS["en"]["monologue_empty"] = "No inner monologues yet."
LABELS["ko"]["htn_enabled"] = "계층 계획 활성화 (HTN)"
LABELS["ko"]["htn_info"] = "현재 버전에서는 주요 에이전트 1명에 적용됩니다."
LABELS["ko"]["planning_depth"] = "계획 깊이"
LABELS["ko"]["planning_depth_info"] = "HTN이 시작할 때 최대 5단계까지 계획을 분해합니다."
LABELS["ko"]["current_plan_panel"] = "현재 계획"
LABELS["ko"]["current_plan_empty"] = "아직 생성된 HTN 계획이 없습니다."
LABELS["ko"]["agent_panel"] = "에이전트 성격"
LABELS["ko"]["agent_tab_prefix"] = "에이전트"
LABELS["ko"]["agent_tab_disabled"] = "이 슬롯을 사용하려면 에이전트 수를 늘리세요."
LABELS["en"]["htn_enabled"] = "Enable hierarchical planning (HTN)"
LABELS["en"]["htn_info"] = "Applies to the primary agent in the current playground layout."
LABELS["en"]["planning_depth"] = "Planning depth"
LABELS["en"]["planning_depth_info"] = "Decompose the top goal into a hierarchy up to 5 levels deep."
LABELS["en"]["current_plan_panel"] = "Current plan"
LABELS["en"]["current_plan_empty"] = "No HTN plan has been generated yet."
LABELS["en"]["agent_panel"] = "Agent personalities"
LABELS["en"]["agent_tab_prefix"] = "Agent"
LABELS["en"]["agent_tab_disabled"] = "Increase the agent count to unlock this editor."
LABELS["ko"]["player_mode"] = "플레이어 모드"
LABELS["ko"]["player_input"] = "플레이어 행동"
LABELS["ko"]["player_input_placeholder"] = "예: Bjorn에게 맥주 1개 주문"
LABELS["ko"]["player_submit"] = "행동 실행"
LABELS["ko"]["player_status"] = "플레이어 진행 상태"
LABELS["ko"]["player_voice_input"] = "음성 입력"
LABELS["ko"]["player_voice_output"] = "에이전트 음성 응답"
LABELS["ko"]["player_stt_engine"] = "STT 엔진"
LABELS["ko"]["player_tts_engine"] = "TTS 엔진"
LABELS["en"]["player_mode"] = "Player mode"
LABELS["en"]["player_input"] = "Player action"
LABELS["en"]["player_input_placeholder"] = "Example: Ask Bjorn for one beer"
LABELS["en"]["player_submit"] = "Submit action"
LABELS["en"]["player_status"] = "Player session status"
LABELS["en"]["player_voice_input"] = "Voice input"
LABELS["en"]["player_voice_output"] = "Agent voice response"
LABELS["en"]["player_stt_engine"] = "STT engine"
LABELS["en"]["player_tts_engine"] = "TTS engine"
LABELS["ko"]["routine_preset"] = "일일 루틴 프리셋"
LABELS["ko"]["routine_preset_info"] = "학생, 직장인, 야간 근로자, NPC 상인, 자유 상태 중 하나를 선택할 수 있습니다."
LABELS["ko"]["routine_text"] = "일일 루틴 (선택)"
LABELS["ko"]["routine_text_info"] = "YAML 목록으로 start_hour, end_hour, location_path, default_action을 입력합니다."
LABELS["ko"]["routine_text_placeholder"] = "- start_hour: 7\n  end_hour: 9\n  location_path: [Town, Tavern, Kitchen]\n  default_action: craft_item"
LABELS["en"]["routine_preset"] = "Daily routine preset"
LABELS["en"]["routine_preset_info"] = "Choose a student, office worker, night-shift, shopkeeper, or free no-routine template."
LABELS["en"]["routine_text"] = "Daily routine (optional)"
LABELS["en"]["routine_text_info"] = "Paste a YAML list with start_hour, end_hour, location_path, and default_action."
LABELS["en"]["routine_text_placeholder"] = "- start_hour: 7\n  end_hour: 9\n  location_path: [Town, Tavern, Kitchen]\n  default_action: craft_item"
LABELS["ko"]["trait_matrix_panel"] = "특성 상관 / 제거 실험"
LABELS["ko"]["trait_matrix_plot"] = "특성 상관 행렬"
LABELS["ko"]["trait_matrix_summary"] = "특성 제거 실험 요약"
LABELS["ko"]["statistics_panel"] = "통계 분석"
LABELS["ko"]["statistics_batch_only"] = "통계 분석은 배치 모드에서만 계산됩니다."
LABELS["ko"]["statistics_insufficient"] = "통계 분석에는 최소 4개 틱 배치 요약이 필요합니다."
LABELS["en"]["trait_matrix_panel"] = "Trait correlation / ablation"
LABELS["en"]["trait_matrix_plot"] = "Trait correlation matrix"
LABELS["en"]["trait_matrix_summary"] = "Trait ablation summary"
LABELS["en"]["statistics_panel"] = "Statistical analysis"
LABELS["en"]["statistics_batch_only"] = "Statistical analysis is available in batch mode only."
LABELS["en"]["statistics_insufficient"] = "Statistical analysis needs at least four tick summaries."
LABELS["ko"]["batch_mode"] = "배치 모드"
LABELS["ko"]["batch_mode_info"] = "같은 시나리오를 여러 시드로 반복 실행해 집계합니다."
LABELS["ko"]["batch_runs"] = "반복 횟수"
LABELS["ko"]["batch_runs_info"] = "1~100회까지 반복 실행합니다. 단일 실행은 1회로 고정됩니다."
LABELS["ko"]["master_seed"] = "마스터 시드"
LABELS["ko"]["master_seed_info"] = "각 배치 시드는 마스터 시드와 실행 인덱스 조합으로 파생됩니다."
LABELS["en"]["batch_mode"] = "Batch mode"
LABELS["en"]["batch_mode_info"] = "Repeat the same scenario across multiple derived seeds and aggregate the outputs."
LABELS["en"]["batch_runs"] = "Batch runs"
LABELS["en"]["batch_runs_info"] = "Repeat the simulation 1 to 100 times. Single-run mode always uses 1."
LABELS["en"]["master_seed"] = "Master seed"
LABELS["en"]["master_seed_info"] = "Batch seeds are derived as master_seed + run_index."
LABELS["ko"]["memory_inspector"] = "메모리 인스펙터"
LABELS["ko"]["memory_agent"] = "에이전트"
LABELS["ko"]["memory_empty"] = "아직 메모리 스냅샷이 없습니다."
LABELS["ko"]["memory_batch"] = "배치 모드는 여러 시드를 집계합니다. 에이전트별 메모리는 단일 실행에서 확인하세요."
LABELS["ko"]["memory_short_term"] = "단기 기억"
LABELS["ko"]["memory_short_term_empty"] = "아직 단기 기억이 없습니다."
LABELS["ko"]["memory_long_term"] = "장기 기억 검색"
LABELS["ko"]["memory_long_term_empty"] = "아직 장기 기억 검색 결과가 없습니다."
LABELS["ko"]["memory_monologue"] = "내적 독백"
LABELS["ko"]["memory_monologue_empty"] = "아직 내적 독백이 없습니다."
LABELS["ko"]["memory_emotion"] = "감정 궤적"
LABELS["ko"]["memory_emotion_empty"] = "아직 감정 궤적이 없습니다."
LABELS["ko"]["memory_multi_hint"] = "메모리 상세는 첫 번째 선택 에이전트를 기준으로 보여주고, 차트는 선택한 모든 에이전트를 포함합니다."
LABELS["ko"]["spatial_heatmap_panel"] = "공간 히트맵"
LABELS["ko"]["spatial_heatmap"] = "공간 히트맵"
LABELS["ko"]["spatial_heatmap_empty"] = "아직 공간 점유 데이터가 없습니다."
LABELS["ko"]["spatial_heatmap_batch"] = "공간 히트맵은 단일 실행에서만 확인할 수 있습니다."
LABELS["ko"]["action_flow_panel"] = "행동 흐름도"
LABELS["ko"]["action_flow"] = "행동 흐름도"
LABELS["ko"]["action_flow_empty"] = "아직 행동 흐름 데이터가 없습니다."
LABELS["ko"]["action_flow_batch"] = "행동 흐름도는 단일 실행에서만 확인할 수 있습니다."
LABELS["ko"]["mini_map_panel"] = "2D 미니맵"
LABELS["ko"]["mini_map"] = "2D 미니맵"
LABELS["ko"]["mini_map_empty"] = "아직 위치 데이터가 없습니다."
LABELS["ko"]["mini_map_batch"] = "2D 미니맵은 단일 실행에서만 확인할 수 있습니다."
LABELS["ko"]["threads_tab"] = "대화 스레드"
LABELS["ko"]["threads_empty"] = "아직 대화 스레드가 없습니다. 직접 대상이 있는 발화가 나오는 시나리오를 실행하세요."
LABELS["ko"]["threads_batch"] = "대화 스레드는 단일 실행에서만 확인할 수 있습니다."
ENVIRONMENT_PRESETS = load_environment_presets()
GRAPH_HEIGHT_PX = 620
TIMELINE_MAX_HEIGHT_PX = 360
ACTION_CHART_HEIGHT_PX = 380
EMOTION_TRAJECTORY_MAX_AGENTS = 12
AGENT_COLOR_SEQUENCE: tuple[str, ...] = tuple(
    qualitative.Safe + qualitative.Set2 + qualitative.Pastel1 + qualitative.Dark2
)
ACTION_PATTERN_SEQUENCE: tuple[str, ...] = ("", "/", "\\", "x", "-", "|", "+", ".")
ACTION_FLOW_SELF_TYPES = frozenset({"alone", "move", "query_memory"})
ACTION_FLOW_COLOR_SEQUENCE: tuple[str, ...] = tuple(
    qualitative.Safe + qualitative.Set2 + qualitative.Pastel1 + qualitative.Dark2
)
COMPETITIVE_COMPARISON_ROWS: tuple[dict[str, object], ...] = (
    {
        "system": "Knoema",
        "focus_en": "Open-source social simulation engine",
        "focus_ko": "오픈소스 사회 시뮬레이션 엔진",
        "memory_en": "Persistent memory plus directed trust graph",
        "memory_ko": "지속 기억 + 방향성 신뢰 그래프",
        "repro_en": "Deterministic replay, YAML, JSONL, benchmark artifacts",
        "repro_ko": "결정론적 리플레이, YAML, JSONL, 벤치마크 산출물",
        "game_en": "Godot and Unity scaffolds",
        "game_ko": "Godot/Unity 스캐폴드",
        "license": "MIT",
        "reference": "https://github.com/Celovin/knoema",
    },
    {
        "system": "Stanford Generative Agents",
        "focus_en": "Academic prototype",
        "focus_ko": "학술 프로토타입",
        "memory_en": "Memory stream and reflection architecture",
        "memory_ko": "memory stream + reflection 구조",
        "repro_en": "Paper and demo code only (partial)",
        "repro_ko": "논문과 데모 코드 중심 (partial)",
        "game_en": "No packaged game SDK",
        "game_ko": "패키지형 게임 SDK 없음",
        "license": "MIT repository",
        "reference": "https://arxiv.org/abs/2304.03442",
    },
    {
        "system": "Google DeepMind Concordia",
        "focus_en": "Research library",
        "focus_ko": "연구용 라이브러리",
        "memory_en": "Component-based generative agents",
        "memory_ko": "컴포넌트 기반 generative agents",
        "repro_en": "Scenario code and package surface (partial)",
        "repro_ko": "시나리오 코드와 패키지 표면 (partial)",
        "game_en": "No packaged game SDK",
        "game_ko": "패키지형 게임 SDK 없음",
        "license": "Apache-2.0",
        "reference": "https://github.com/google-deepmind/concordia",
    },
    {
        "system": "CAMEL-AI",
        "focus_en": "General multi-agent framework",
        "focus_ko": "범용 멀티에이전트 프레임워크",
        "memory_en": "Stateful memory plus benchmark support",
        "memory_ko": "stateful memory + benchmark 지원",
        "repro_en": "Framework and benchmark surfaces (partial social-world focus)",
        "repro_ko": "프레임워크/벤치마크 표면 (사회 세계 특화는 partial)",
        "game_en": "No packaged game SDK",
        "game_ko": "패키지형 게임 SDK 없음",
        "license": "Apache-2.0",
        "reference": "https://github.com/camel-ai/camel",
    },
    {
        "system": "Microsoft AutoGen",
        "focus_en": "Agent orchestration framework",
        "focus_ko": "에이전트 오케스트레이션 프레임워크",
        "memory_en": "Application-defined state",
        "memory_ko": "애플리케이션 정의 상태",
        "repro_en": "App-dependent (partial)",
        "repro_ko": "앱 구현 의존 (partial)",
        "game_en": "No packaged game SDK",
        "game_ko": "패키지형 게임 SDK 없음",
        "license": "MIT",
        "reference": "https://github.com/microsoft/autogen",
    },
)
BENCHMARK_CAVEAT_SYNTHETIC = "synthetic local proxy"
BENCHMARK_CAVEAT_DETERMINISTIC = "deterministic local measurement"
BENCHMARK_CAVEAT_PUBLISHED = "published reference (not measured)"
BENCHMARK_EVIDENCE_ROWS: tuple[dict[str, str], ...] = (
    {
        "label_en": "LoCoMo-inspired long-term conversational retention proxy",
        "label_ko": "LoCoMo 장기 대화 유지 프록시",
        "metric_en": "score 1.000 / target 0.800",
        "metric_ko": "점수 1.000 / 목표 0.800",
        "caveat": BENCHMARK_CAVEAT_SYNTHETIC,
        "source": "benchmarks/memory_benchmark_integration/results/summary.json",
    },
    {
        "label_en": "MemoryAgentBench-inspired EventQA + FactConsolidation proxy",
        "label_ko": "MemoryAgentBench EventQA + FactConsolidation 프록시",
        "metric_en": "score 1.000 / target 0.800",
        "metric_ko": "점수 1.000 / 목표 0.800",
        "caveat": BENCHMARK_CAVEAT_SYNTHETIC,
        "source": "benchmarks/memory_benchmark_integration/results/summary.json",
    },
    {
        "label_en": "MemoryArena-inspired decision-relevant memory proxy",
        "label_ko": "MemoryArena 의사결정 연관 기억 프록시",
        "metric_en": "score 1.000 / target 0.600",
        "metric_ko": "점수 1.000 / 목표 0.600",
        "caveat": BENCHMARK_CAVEAT_SYNTHETIC,
        "source": "benchmarks/memory_benchmark_integration/results/summary.json",
    },
    {
        "label_en": "MLMF four-layer retention",
        "label_ko": "MLMF 4계층 유지율",
        "metric_en": "retention 0.875 vs published baseline 0.569",
        "metric_ko": "유지율 0.875, 공개 기준선 0.569 대비",
        "caveat": BENCHMARK_CAVEAT_DETERMINISTIC,
        "source": "experiments/mlmf_retention_benchmark/results/summary.json",
    },
    {
        "label_en": "ToM Sally-Anne",
        "label_ko": "ToM Sally-Anne",
        "metric_en": "baseline accuracy 1.000; material tiers tier_a, tier_bd, tier_e, tier_f, tier_g",
        "metric_ko": "기준 정확도 1.000, material tier는 tier_a, tier_bd, tier_e, tier_f, tier_g",
        "caveat": BENCHMARK_CAVEAT_DETERMINISTIC,
        "source": "experiments/theory_of_mind_ablation/results/summary.json",
    },
    {
        "label_en": "HTN scaling",
        "label_ko": "HTN 확장성",
        "metric_en": "depth-5 goal achievement 0.955 vs planning-off 0.565",
        "metric_ko": "깊이 5 목표 달성률 0.955, planning-off 0.565 대비",
        "caveat": BENCHMARK_CAVEAT_DETERMINISTIC,
        "source": "experiments/planning_depth/results/summary.json",
    },
    {
        "label_en": "ACE latency reference",
        "label_ko": "ACE 지연 시간 참고치",
        "metric_en": "198-200 ms target envelope",
        "metric_ko": "198-200 ms 목표 구간",
        "caveat": BENCHMARK_CAVEAT_PUBLISHED,
        "source": "benchmarks/formal_report/results/latency_comparison.json",
    },
    {
        "label_en": "Inworld latency reference",
        "label_ko": "Inworld 지연 시간 참고치",
        "metric_en": "130-250 ms first audio; 1000-3000 ms end-to-end guidance",
        "metric_ko": "첫 오디오 130-250 ms, 전체 파이프라인 가이드는 1000-3000 ms",
        "caveat": BENCHMARK_CAVEAT_PUBLISHED,
        "source": "benchmarks/formal_report/results/latency_comparison.json",
    },
)

BIG_FIVE_FIELDS = PERSONA_TRAIT_FIELDS[:5]
TIER_BD_FIELDS = (
    "honesty_humility",
    "kantianism",
    "humanism",
    "faith_in_humanity",
)
TIER_C_FIELDS = (
    "machiavellianism",
    "narcissism",
    "psychopathy",
    "sadism",
)
TIER_E_FIELDS = (
    "risk_tolerance",
    "locus_of_control",
    "need_for_cognition",
    "trait_empathy",
)
TIER_F_FIELDS = (
    "care_harm",
    "fairness",
    "binding_morals",
)
TIER_G_ROWS = (
    ("self_direction", "stimulation", "hedonism"),
    ("achievement", "power", "security"),
    ("conformity", "tradition"),
    ("benevolence", "universalism"),
)
TIER_G_FIELDS = tuple(field_name for row in TIER_G_ROWS for field_name in row)
HONESTY_HUMILITY_CAVEAT_COPY = {
    "ko": (
        "> 주의: Ashton & Lee 리뷰에 따르면 Honesty-Humility는 일부 비서구 표본에서 "
        "일관되게 재현되지 않았습니다. 이 슬라이더는 문화 중립적 사실이 아니라 탐색적 신호로 해석하세요."
    ),
    "ja": (
        "> 注意: Ashton と Lee のレビューでは、Honesty-Humility は一部の非西洋サンプルで "
        "一貫して再現されていません。このスライダーは文化中立の事実ではなく探索的な指標として扱ってください。"
    ),
    "zh": (
        "> 注意: Ashton 与 Lee 的综述指出, Honesty-Humility 在部分非西方样本中并未稳定复现。"
        "请将此滑块视为探索性信号, 而不是跨文化恒定真值。"
    ),
}


def _tutorial_head() -> str:
    return f"""
<style>
.knoema-tour-root {{
  position: fixed;
  inset: 0;
  z-index: 2147483645;
  pointer-events: none;
}}
.knoema-tour-root[data-open="true"] {{
  pointer-events: auto;
}}
.knoema-tour-backdrop {{
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.22);
}}
.knoema-tour-card {{
  position: absolute;
  width: min(360px, calc(100vw - 32px));
  background: #ffffff;
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.55);
  border-radius: 8px;
  box-shadow: 0 24px 64px rgba(15, 23, 42, 0.24);
  padding: 16px;
}}
.knoema-tour-card::before {{
  content: "";
  position: absolute;
  top: -10px;
  left: 28px;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-bottom: 10px solid #ffffff;
}}
.knoema-tour-counter {{
  font-size: 12px;
  color: #475569;
  margin-bottom: 6px;
}}
.knoema-tour-title {{
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}}
.knoema-tour-body {{
  font-size: 14px;
  line-height: 1.5;
  color: #334155;
  margin-bottom: 14px;
}}
.knoema-tour-controls {{
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}}
.knoema-tour-controls button {{
  border: 1px solid rgba(148, 163, 184, 0.55);
  background: #ffffff;
  color: #0f172a;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
}}
.knoema-tour-controls button[data-tour-action="next"] {{
  background: #0f172a;
  color: #ffffff;
}}
.knoema-tour-highlight {{
  position: relative;
  z-index: 2147483646 !important;
  border-radius: 8px;
  box-shadow:
    0 0 0 3px rgba(56, 189, 248, 0.7),
    0 0 0 9999px rgba(15, 23, 42, 0.18);
}}
@media (max-width: 720px) {{
  .knoema-tour-card {{
    left: 16px !important;
    right: 16px !important;
    top: auto !important;
    bottom: 16px !important;
    width: auto;
  }}
  .knoema-tour-card::before {{
    display: none;
  }}
  .knoema-tour-controls {{
    flex-direction: column;
    align-items: stretch;
  }}
}}
</style>
<script>
(() => {{
  const stepsByLang = {json.dumps(TUTORIAL_STEPS, ensure_ascii=False)};
  const storageKey = {json.dumps(TUTORIAL_STORAGE_KEY)};
  const koreanChoice = {json.dumps(KOREAN_CHOICE, ensure_ascii=False)};
  const labels = {{
    ko: {{ prev: "이전", next: "다음", finish: "완료", skip: "건너뛰기" }},
    en: {{ prev: "Previous", next: "Next", finish: "Finish", skip: "Skip" }},
  }};

  const state = {{
    index: 0,
    lang: "ko",
    steps: stepsByLang.ko,
    highlighted: null,
  }};

  function ensureRoot() {{
    let root = document.querySelector(".knoema-tour-root");
    if (root) return root;
    root = document.createElement("div");
    root.className = "knoema-tour-root";
    root.setAttribute("data-open", "false");
    root.innerHTML = `
      <div class="knoema-tour-backdrop" data-tour-action="skip"></div>
      <div class="knoema-tour-card" role="dialog" aria-modal="true" aria-live="polite">
        <div class="knoema-tour-counter"></div>
        <div class="knoema-tour-title"></div>
        <div class="knoema-tour-body"></div>
        <div class="knoema-tour-controls">
          <button type="button" data-tour-action="skip"></button>
          <button type="button" data-tour-action="prev"></button>
          <button type="button" data-tour-action="next"></button>
        </div>
      </div>
    `;
    root.addEventListener("click", (event) => {{
      const action = event.target instanceof HTMLElement ? event.target.dataset.tourAction : null;
      if (!action) return;
      if (action === "skip") {{
        close(true);
        return;
      }}
      if (action === "prev") {{
        state.index = Math.max(0, state.index - 1);
        render();
        return;
      }}
      if (action === "next") {{
        if (state.index >= state.steps.length - 1) {{
          close(true);
          return;
        }}
        state.index += 1;
        render();
      }}
    }});
    document.body.appendChild(root);
    return root;
  }}

  function clearHighlight() {{
    if (state.highlighted) {{
      state.highlighted.classList.remove("knoema-tour-highlight");
      state.highlighted = null;
    }}
  }}

  function positionCard(card, target) {{
    if (!target) {{
      card.style.left = "16px";
      card.style.top = "16px";
      return;
    }}
    const rect = target.getBoundingClientRect();
    const margin = 16;
    const preferredLeft = Math.min(
      window.innerWidth - card.offsetWidth - margin,
      Math.max(margin, rect.left),
    );
    const preferredTop = rect.bottom + margin;
    const aboveTop = rect.top - card.offsetHeight - margin;
    card.style.left = preferredLeft + "px";
    card.style.top = (aboveTop > margin ? aboveTop : preferredTop) + "px";
  }}

  function render() {{
    const root = ensureRoot();
    const card = root.querySelector(".knoema-tour-card");
    const step = state.steps[state.index];
    const target = document.querySelector(step.selector);
    clearHighlight();
    if (target) {{
      target.classList.add("knoema-tour-highlight");
      target.scrollIntoView({{ block: "center", behavior: "smooth", inline: "center" }});
      state.highlighted = target;
    }}
    root.querySelector(".knoema-tour-counter").textContent =
      String(state.index + 1) + " / " + String(state.steps.length);
    root.querySelector(".knoema-tour-title").textContent = step.title;
    root.querySelector(".knoema-tour-body").textContent = step.body;
    const buttonLabels = labels[state.lang];
    const prevButton = root.querySelector('[data-tour-action="prev"]');
    const nextButton = root.querySelector('[data-tour-action="next"]');
    const skipButton = root.querySelector('[data-tour-action="skip"]:not(.knoema-tour-backdrop)');
    prevButton.textContent = buttonLabels.prev;
    prevButton.disabled = state.index === 0;
    nextButton.textContent = state.index === state.steps.length - 1 ? buttonLabels.finish : buttonLabels.next;
    skipButton.textContent = buttonLabels.skip;
    requestAnimationFrame(() => positionCard(card, target));
  }}

  function close(markCompleted) {{
    clearHighlight();
    const root = ensureRoot();
    root.setAttribute("data-open", "false");
    root.style.display = "none";
    if (markCompleted) {{
      window.localStorage.setItem(storageKey, "1");
    }}
  }}

  function start(languageChoice) {{
    const root = ensureRoot();
    state.lang = languageChoice === koreanChoice ? "ko" : "en";
    state.steps = stepsByLang[state.lang];
    state.index = 0;
    root.style.display = "block";
    root.setAttribute("data-open", "true");
    render();
  }}

  window.KNOEMA_TUTORIAL = {{ start, close }};
  window.addEventListener("load", () => {{
    window.setTimeout(() => {{
      if (!window.localStorage.getItem(storageKey)) {{
        start(koreanChoice);
      }}
    }}, 900);
  }});
}})();
</script>
"""


TUTORIAL_HEAD = _tutorial_head()


def _theme_head() -> str:
    return f"""
<script>
(() => {{
  const storageKey = {json.dumps(THEME_STORAGE_KEY)};
  const koreanChoice = {json.dumps(KOREAN_CHOICE, ensure_ascii=False)};
  const labels = {{
    ko: {{
      auto: {json.dumps(LABELS["ko"]["theme_auto"], ensure_ascii=False)},
      light: {json.dumps(LABELS["ko"]["theme_light"], ensure_ascii=False)},
      dark: {json.dumps(LABELS["ko"]["theme_dark"], ensure_ascii=False)},
    }},
    en: {{
      auto: {json.dumps(LABELS["en"]["theme_auto"], ensure_ascii=False)},
      light: {json.dumps(LABELS["en"]["theme_light"], ensure_ascii=False)},
      dark: {json.dumps(LABELS["en"]["theme_dark"], ensure_ascii=False)},
    }},
  }};
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function languageKey(languageChoice) {{
    return languageChoice === koreanChoice ? "ko" : "en";
  }}

  function normalizeMode(value) {{
    if (value === "light" || value === labels.ko.light || value === labels.en.light) return "light";
    if (value === "dark" || value === labels.ko.dark || value === labels.en.dark) return "dark";
    return "auto";
  }}

  function readStoredMode() {{
    return normalizeMode(window.localStorage.getItem(storageKey));
  }}

  function resolvedMode(mode) {{
    return mode === "auto" ? (media.matches ? "dark" : "light") : mode;
  }}

  function applyMode(mode, persist) {{
    const normalized = normalizeMode(mode);
    const active = resolvedMode(normalized);
    document.documentElement.dataset.knoemaThemeMode = normalized;
    document.documentElement.dataset.knoemaTheme = active;
    document.documentElement.style.colorScheme = active;
    if (persist !== false) {{
      window.localStorage.setItem(storageKey, normalized);
    }}
    return normalized;
  }}

  function labelFor(mode, languageChoice) {{
    return labels[languageKey(languageChoice)][normalizeMode(mode)];
  }}

  media.addEventListener("change", () => {{
    if (readStoredMode() === "auto") {{
      applyMode("auto", false);
    }}
  }});

  window.KNOEMA_THEME = {{
    sync(languageChoice) {{
      return applyMode(readStoredMode(), false);
    }},
    setFromLabel(label, languageChoice) {{
      return applyMode(label, true);
    }},
    currentLabel(languageChoice) {{
      return labelFor(readStoredMode(), languageChoice);
    }},
  }};

  applyMode(readStoredMode(), false);
}})();
</script>
"""


THEME_HEAD = _theme_head()


def _accessibility_head() -> str:
    return f"""
<script>
(() => {{
  const koreanChoice = {json.dumps(KOREAN_CHOICE, ensure_ascii=False)};
  const labels = {{
    ko: {{
      tutorial: "튜토리얼 열기",
      run: "시뮬레이션 실행",
      theme: "테마 선택",
      tick: "틱 선택",
      graph: "관계 그래프. 실행 요약에 텍스트 대체 설명이 있습니다.",
      summary: "실행 요약 및 관계 그래프 대체 설명",
    }},
    en: {{
      tutorial: "Open tutorial walkthrough",
      run: "Run simulation",
      theme: "Theme selector",
      tick: "Tick selector",
      graph: "Relationship graph. The run summary contains a text alternative.",
      summary: "Run summary and relationship graph text alternative",
    }},
  }};

  function currentLang() {{
    const checked = Array.from(document.querySelectorAll('input[type="radio"]'))
      .find((input) => input.checked && input.value === koreanChoice);
    return checked ? "ko" : "en";
  }}

  function setAttr(element, name, value) {{
    if (element && element.getAttribute(name) !== value) {{
      element.setAttribute(name, value);
    }}
  }}

  function setLabel(id, label) {{
    const element = document.getElementById(id);
    setAttr(element, "aria-label", label);
  }}

  function applyA11y() {{
    const key = currentLang();
    const text = labels[key];
    setLabel("tutorial-button", text.tutorial);
    setLabel("run-button", text.run);
    setLabel("theme-mode-radio", text.theme);
    setLabel("tick-scrubber", text.tick);

    const summary = document.getElementById("run-summary");
    setAttr(summary, "role", "status");
    setAttr(summary, "aria-live", "polite");
    setAttr(summary, "aria-label", text.summary);

    const graph = document.getElementById("relationship-graph");
    setAttr(graph, "role", "img");
    setAttr(graph, "tabindex", "0");
    setAttr(graph, "aria-label", text.graph);
    setAttr(graph, "aria-describedby", "run-summary");
  }}

  window.addEventListener("load", applyA11y);
  new MutationObserver(applyA11y).observe(document.documentElement, {{ childList: true, subtree: true }});
}})();
</script>
"""


ACCESSIBILITY_HEAD = _accessibility_head()


def _reviewer_head() -> str:
    return """
<script>
window.KNOEMA_REVIEWER = {
  enabled: () => new URLSearchParams(window.location.search).get("reviewer") === "1",
  targetId: "reviewer-mode-toggle"
};
</script>
"""


REVIEWER_HEAD = _reviewer_head()


def _presentation_head() -> str:
    return """
<style>
:root.present-mode body,
:root.present-mode .gradio-container {
  width: 100vw !important;
  max-width: none !important;
  margin: 0 !important;
}
:root.present-mode .sidebar,
:root.present-mode [data-testid="sidebar"],
:root.present-mode header,
:root.present-mode footer,
:root.present-mode .footer,
:root.present-mode .api-docs {
  display: none !important;
}
:root.present-mode #topbar-row,
:root.present-mode #personality-panel,
:root.present-mode #mirofish-lab-panel {
  display: none !important;
}
:root.present-mode #run-button {
  position: fixed !important;
  right: 20px !important;
  bottom: 20px !important;
  z-index: 2147483000 !important;
}
.knoema-present-hint {
  position: fixed;
  left: 50%;
  top: 20px;
  transform: translateX(-50%);
  z-index: 2147483001;
  max-width: min(720px, calc(100vw - 32px));
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.92);
  color: #ffffff;
  box-shadow: 0 18px 48px rgba(15, 23, 42, 0.25);
  font: 14px/1.5 Inter, Segoe UI, Arial, sans-serif;
}
.knoema-present-hint[data-hidden="true"] {
  display: none;
}
</style>
<script>
(() => {
  const params = new URLSearchParams(window.location.search);
  const presentRequested = params.get("mode") === "present";
  const editableSelector = [
    "input:not([type='button']):not([type='submit'])",
    "textarea",
    "select"
  ].join(",");

  function ensureHint() {
    let hint = document.querySelector(".knoema-present-hint");
    if (hint) return hint;
    hint = document.createElement("div");
    hint.className = "knoema-present-hint";
    hint.textContent = "Presentation mode: Right/Left moves tabs, Space runs the scenario, Esc exits.";
    hint.setAttribute("data-hidden", "false");
    document.body.appendChild(hint);
    window.setTimeout(() => hint.setAttribute("data-hidden", "true"), 3000);
    return hint;
  }

  function setEditableDisabled(disabled) {
    document.querySelectorAll(editableSelector).forEach((element) => {
      const insideOutput = element.closest("#run-summary, #export-panel, #relationship-graph");
      if (insideOutput) return;
      if (disabled) {
        element.dataset.knoemaPresentDisabled = "1";
        element.setAttribute("disabled", "disabled");
      } else if (element.dataset.knoemaPresentDisabled === "1") {
        element.removeAttribute("disabled");
        delete element.dataset.knoemaPresentDisabled;
      }
    });
  }

  function applyPresentationMode(enabled) {
    document.documentElement.classList.toggle("present-mode", enabled);
    document.body?.classList.toggle("present-mode", enabled);
    if (enabled) {
      ensureHint();
    }
    setEditableDisabled(enabled);
  }

  function selectedTabIndex(tabs) {
    const index = tabs.findIndex((tab) => tab.getAttribute("aria-selected") === "true");
    return index >= 0 ? index : 0;
  }

  function moveTab(delta) {
    const tabs = Array.from(document.querySelectorAll('[role="tab"]'))
      .filter((tab) => tab.offsetParent !== null);
    if (!tabs.length) return;
    const next = (selectedTabIndex(tabs) + delta + tabs.length) % tabs.length;
    tabs[next].click();
    tabs[next].focus();
  }

  function exitPresentationMode() {
    params.delete("mode");
    const query = params.toString();
    const nextUrl = window.location.pathname + (query ? `?${query}` : "") + window.location.hash;
    window.history.replaceState({}, "", nextUrl);
    applyPresentationMode(false);
  }

  window.KNOEMA_PRESENTATION = { apply: applyPresentationMode, exit: exitPresentationMode };

  window.addEventListener("keydown", (event) => {
    if (!document.documentElement.classList.contains("present-mode")) return;
    const target = event.target;
    const editing = target instanceof HTMLElement && target.matches("input, textarea, select, [contenteditable='true']");
    if (event.key === "Escape") {
      event.preventDefault();
      exitPresentationMode();
      return;
    }
    if (editing) return;
    if (event.key === "ArrowRight") {
      event.preventDefault();
      moveTab(1);
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      moveTab(-1);
      return;
    }
    if (event.key === " ") {
      event.preventDefault();
      document.querySelector("#run-button")?.click();
    }
  });

  window.addEventListener("load", () => {
    applyPresentationMode(presentRequested);
    new MutationObserver(() => {
      if (document.documentElement.classList.contains("present-mode")) {
        setEditableDisabled(true);
      }
    }).observe(document.documentElement, { childList: true, subtree: true });
  });
})();
</script>
"""


PRESENTATION_HEAD = _presentation_head()
APP_HEAD = TUTORIAL_HEAD + THEME_HEAD + ACCESSIBILITY_HEAD + REVIEWER_HEAD + PRESENTATION_HEAD

FOOTER_CSS = f"""
:root {{
    --knoema-bg: #f5f7fb;
    --knoema-surface: #ffffff;
    --knoema-surface-alt: #edf2f7;
    --knoema-text: #102033;
    --knoema-muted: #526273;
    --knoema-border: rgba(100, 116, 139, 0.35);
    --knoema-accent: #0f766e;
    --knoema-accent-strong: #115e59;
    --knoema-focus: #f97316;
}}
:root[data-knoema-theme="dark"] {{
    --knoema-bg: #0f172a;
    --knoema-surface: #162033;
    --knoema-surface-alt: #1e293b;
    --knoema-text: #e5eef7;
    --knoema-muted: #c0cfdd;
    --knoema-border: rgba(148, 163, 184, 0.35);
    --knoema-accent: #34d399;
    --knoema-accent-strong: #10b981;
    --knoema-focus: #fbbf24;
}}
body,
.gradio-container {{
    background: var(--knoema-bg) !important;
    color: var(--knoema-text) !important;
}}
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4,
.gradio-container p,
.gradio-container label,
.gradio-container .prose,
.gradio-container .gr-markdown,
.gradio-container .gr-textbox,
.gradio-container .gr-number,
.gradio-container .gr-dropdown,
.gradio-container .gr-radio {{
    color: var(--knoema-text) !important;
}}
.gradio-container :is(.prose, .gr-markdown, [data-testid="markdown"]) :is(p, li, ul, ol, span, strong, em, code, pre, blockquote, h1, h2, h3, h4, h5, h6, a) {{
    color: var(--knoema-text) !important;
}}
.gradio-container .gr-box,
.gradio-container .gr-panel,
.gradio-container .gr-accordion,
.gradio-container .gr-form,
.gradio-container .block,
.gradio-container .wrap {{
    background: var(--knoema-surface) !important;
    border-color: var(--knoema-border) !important;
}}
.gradio-container input,
.gradio-container textarea,
.gradio-container select,
.gradio-container .cm-editor,
.gradio-container .cm-gutters {{
    background: var(--knoema-surface-alt) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
.gradio-container button {{
    border-color: var(--knoema-border) !important;
}}
.gradio-container :is(.gr-radio label, .wrap label.gr-radio, [data-testid="radio"] label, fieldset label) {{
    color: var(--knoema-text) !important;
    cursor: pointer !important;
    pointer-events: auto !important;
}}
.gradio-container :is(.block-label, .block-info, span, legend) {{
    color: var(--knoema-text) !important;
}}
.gradio-container :is(.gr-radio label span, [data-testid="radio"] label span, fieldset label span) {{
    color: var(--knoema-text) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .gr-radio label,
    [data-testid="radio"] label,
    fieldset label
) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border: 1px solid var(--knoema-border) !important;
}}
/* Make radio inputs and their checked state visible across themes */
.gradio-container :is(.gr-radio input[type="radio"], [data-testid="radio"] input[type="radio"], fieldset input[type="radio"]) {{
    accent-color: var(--knoema-accent) !important;
    width: 18px !important;
    height: 18px !important;
    opacity: 1 !important;
    visibility: visible !important;
    pointer-events: auto !important;
    cursor: pointer !important;
    appearance: auto !important;
    -webkit-appearance: auto !important;
    margin-right: 8px !important;
}}
.gradio-container :is(.gr-radio label:has(input[type="radio"]:checked), [data-testid="radio"] label:has(input[type="radio"]:checked)) {{
    background: var(--knoema-accent) !important;
    color: #ffffff !important;
    border-color: var(--knoema-accent-strong) !important;
}}
.gradio-container :is(.gr-radio label:has(input[type="radio"]:checked) span, [data-testid="radio"] label:has(input[type="radio"]:checked) span) {{
    color: #ffffff !important;
}}
/* Force native checkbox visibility + checked state */
.gradio-container input[type="checkbox"] {{
    appearance: auto !important;
    -webkit-appearance: auto !important;
    accent-color: var(--knoema-accent) !important;
    width: 18px !important;
    height: 18px !important;
    opacity: 1 !important;
    visibility: visible !important;
    pointer-events: auto !important;
    cursor: pointer !important;
    margin-right: 8px !important;
}}
.gradio-container .gr-checkbox label,
.gradio-container [data-testid="checkbox"] label {{
    cursor: pointer !important;
    pointer-events: auto !important;
    color: var(--knoema-text) !important;
}}
/* Number input spinners visible */
.gradio-container input[type="number"] {{
    color: var(--knoema-text) !important;
    background: var(--knoema-surface-alt) !important;
}}
.gradio-container input[type="number"]::-webkit-inner-spin-button,
.gradio-container input[type="number"]::-webkit-outer-spin-button {{
    opacity: 1 !important;
    filter: invert(0%);
}}
:root[data-knoema-theme="dark"] .gradio-container input[type="number"]::-webkit-inner-spin-button,
:root[data-knoema-theme="dark"] .gradio-container input[type="number"]::-webkit-outer-spin-button {{
    filter: invert(100%);
}}
/* Selected text contrast */
.gradio-container ::selection {{
    background: var(--knoema-accent) !important;
    color: #ffffff !important;
}}
/* Tabs: active tab text visible in both themes */
.gradio-container :is(.tab-nav button.selected, .tabs button.selected, [role="tab"][aria-selected="true"]) {{
    background: var(--knoema-accent) !important;
    border-color: var(--knoema-accent-strong) !important;
    color: #ffffff !important;
}}
.gradio-container :is(.tab-nav button, .tabs button, [role="tab"]) {{
    color: var(--knoema-text) !important;
}}
/* Force light-mode dark-bg sections (Code/Files components) to readable colors */
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .gr-file,
    [data-testid="file"],
    .gr-code,
    [data-testid="code"],
    .gr-code *,
    [data-testid="code"] *
) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .gr-accordion,
    [data-testid="accordion"],
    .tabitem,
    [role="tabpanel"],
    .tabs,
    .tab-nav,
    .gr-form,
    .gr-box,
    .gr-panel,
    .block,
    .wrap,
    .gr-dropdown,
    [data-testid="dropdown"],
    .gr-slider,
    [data-testid="slider"],
    .gr-dataframe,
    table,
    thead,
    tbody,
    tr,
    td,
    th,
    pre
) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .cm-editor,
    .cm-scroller,
    .cm-content,
    .cm-line,
    .cm-gutters,
    .cm-activeLine,
    .cm-activeLineGutter
) {{
    background: var(--knoema-surface-alt) !important;
    color: var(--knoema-text) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .tab-nav button,
    .tabs button,
    [role="tab"]
) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .gr-accordion *,
    [role="tabpanel"] *,
    .gr-file *,
    [data-testid="file"] *,
    .gr-code *,
    [data-testid="code"] *,
    .gr-dropdown *,
    [data-testid="dropdown"] *,
    .gr-slider *,
    [data-testid="slider"] *,
    .gr-dataframe *
) {{
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container input[type="range"] {{
    accent-color: var(--knoema-accent) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container button {{
    color: var(--knoema-text) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(button.primary, button[variant="primary"]) {{
    color: #ffffff !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .block-label,
    .block-info,
    .gr-form > label,
    .form > label,
    legend,
    .gr-text-input,
    span
) {{
    color: #102033 !important;
    opacity: 1 !important;
}}
.gradio-container button.primary,
.gradio-container button[variant="primary"] {{
    background: var(--knoema-accent) !important;
}}
.gradio-container button.secondary,
.gradio-container button[variant="secondary"] {{
    color: var(--knoema-text) !important;
}}
/* Light-mode: force non-primary buttons to surface bg so dark default bg + dark text doesn't go invisible */
:root:not([data-knoema-theme="dark"]) .gradio-container button:not(.primary):not([variant="primary"]) {{
    background: var(--knoema-surface) !important;
    border: 1px solid var(--knoema-border) !important;
    color: var(--knoema-text) !important;
}}
:root:not([data-knoema-theme="dark"]) .gradio-container button:not(.primary):not([variant="primary"]):hover {{
    background: var(--knoema-surface-alt) !important;
}}
/* Light-mode: block-label (the floating badge on Plot/Image/etc.) must use surface bg, not the dark default */
:root:not([data-knoema-theme="dark"]) .gradio-container :is(.block-label, [class*="block-label"], .label-wrap, [class*="label-wrap"]) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
/* Light-mode: inline code (backticks) inside markdown must be readable - used by timeline timestamps + benchmark caveat/source */
:root:not([data-knoema-theme="dark"]) .gradio-container :is(.prose, .gr-markdown, [data-testid="markdown"]) code {{
    background: var(--knoema-surface-alt) !important;
    color: var(--knoema-text) !important;
    border: 1px solid var(--knoema-border) !important;
    padding: 0.05em 0.35em !important;
    border-radius: 3px !important;
}}
/* Light-mode: any remaining label / file-preview / empty-state wrappers that default to dark */
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    label,
    .file-preview,
    [data-testid="file-preview"],
    .file,
    [data-testid="file"],
    .empty,
    [class*="empty-"],
    .download-link,
    .file-name
) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
/* Light-mode: textarea/input/textbox wrappers that still show dark bg because of Gradio default */
:root:not([data-knoema-theme="dark"]) .gradio-container :is(
    .gr-textbox,
    [data-testid="textbox"],
    .gr-textbox > *,
    [data-testid="textbox"] > *,
    .gr-text-input
) {{
    background: var(--knoema-surface) !important;
    color: var(--knoema-text) !important;
    border-color: var(--knoema-border) !important;
}}
.gradio-container *:focus-visible {{
    outline: 3px solid var(--knoema-focus) !important;
    outline-offset: 2px;
}}
footer {{display: none !important;}}
.footer {{display: none !important;}}
.api-docs {{display: none !important;}}
#topbar-row {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    align-items: flex-start;
}}
#topbar-row > * {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}
#topbar-row > div:has(#tutorial-button),
#topbar-row > div:has(.gr-radio) {{
    background: var(--knoema-surface) !important;
    border: 1px solid var(--knoema-border) !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}}
#relationship-graph,
#relationship-graph .js-plotly-plot,
#relationship-graph .plot-container,
#relationship-graph .knoema-force-graph-shell,
#relationship-graph .knoema-force-graph-frame {{
    min-height: {GRAPH_HEIGHT_PX}px;
}}
#relationship-graph .knoema-force-graph-shell {{
    width: 100%;
}}
#relationship-graph .knoema-force-graph-frame {{
    width: 100%;
    height: {GRAPH_HEIGHT_PX}px;
    border: 0;
    display: block;
    background: transparent;
}}
#timeline-panel {{
    max-height: {TIMELINE_MAX_HEIGHT_PX}px;
    overflow-y: auto;
}}
.knoema-hint {{
    color: var(--knoema-muted);
    font-size: 0.95rem;
}}
.knoema-hint p {{
    margin-bottom: 0;
}}
.knoema-muted {{
    color: var(--knoema-muted);
    font-size: 0.92rem;
}}
"""


def _language_key(language_choice: str) -> str:
    raw_choice = str(language_choice).strip()
    lowered_choice = raw_choice.lower()
    if raw_choice == KOREAN_CHOICE or lowered_choice in {"ko", "korean"}:
        return "ko"
    return "en"


def _honesty_humility_caveat_locale(language_choice: str) -> str:
    raw_choice = str(language_choice).strip()
    lowered_choice = raw_choice.lower()
    if raw_choice == KOREAN_CHOICE or lowered_choice in {"ko", "korean"}:
        return "ko"
    if raw_choice in {"日本語", "日本语"} or lowered_choice in {"ja", "japanese"}:
        return "ja"
    if raw_choice in {"中文", "简体中文", "繁體中文"} or lowered_choice in {"zh", "chinese"}:
        return "zh"
    return "en"


def _honesty_humility_caveat_markdown(language_choice: str) -> str:
    return HONESTY_HUMILITY_CAVEAT_COPY.get(
        _honesty_humility_caveat_locale(language_choice),
        "",
    )


def _honesty_humility_caveat_update(language_choice: str) -> dict[str, Any]:
    markdown = _honesty_humility_caveat_markdown(language_choice)
    return gr.update(value=markdown, visible=bool(markdown))


def _questionnaire_panel_update(mode: str) -> dict[str, Any]:
    visible = _questionnaire_mode_value(mode) == QUESTIONNAIRE_MODE_HEXACO
    return gr.update(visible=visible, open=visible)


def _apply_questionnaire_to_trait_sliders(
    language_choice: str,
    *responses: float,
) -> list[Any]:
    response_map = {
        item.item_id: int(value)
        for item, value in zip(HEXACO_QUESTIONNAIRE_ITEMS, responses, strict=True)
    }
    scores = score_hexaco_questionnaire(response_map)
    overrides = derive_personality_from_questionnaire(response_map)
    language = _language_key(language_choice)
    return [
        float(overrides[field_name])
        for field_name in PERSONA_TRAIT_FIELDS
    ] + [questionnaire_summary_markdown(scores, language)]


def _questionnaire_mode_updates(
    mode: str,
    language_choice: str,
    *responses: float,
) -> list[Any]:
    panel_update = _questionnaire_panel_update(mode)
    if _questionnaire_mode_value(mode) != QUESTIONNAIRE_MODE_HEXACO:
        return [
            panel_update,
            *[gr.update() for _ in PERSONA_TRAIT_FIELDS],
            questionnaire_empty_summary(_language_key(language_choice)),
        ]
    return [panel_update, *_apply_questionnaire_to_trait_sliders(language_choice, *responses)]


def _default_environment_id() -> str:
    return str(ENVIRONMENT_PRESETS[0]["id"])


def _preset_choices(language: str) -> list[tuple[str, str]]:
    label_key = "label_ko" if language == "ko" else "label_en"
    return [(str(preset[label_key]), str(preset["id"])) for preset in ENVIRONMENT_PRESETS]


def _persona_choices(language: str) -> list[tuple[str, str]]:
    return persona_choices(language, include_blank=True)


def _routine_preset_choices(language: str) -> list[tuple[str, str]]:
    return routine_preset_choices(language)


def _cultural_prior_choices(language: str) -> list[tuple[str, str]]:
    return cultural_prior_choices(language, include_blank=True)


def _provider_choices(language: str) -> list[tuple[str, str]]:
    labels = LABELS[language]
    return [
        (labels["replay"], "Replay only"),
        ("OpenAI", "OpenAI"),
        ("Anthropic", "Anthropic"),
        (labels["player_mode"], "Player mode"),
    ]


def _theme_choices(language: str) -> list[tuple[str, str]]:
    labels = LABELS[language]
    return [
        (labels["theme_auto"], "auto"),
        (labels["theme_light"], "light"),
        (labels["theme_dark"], "dark"),
    ]


def _normalize_theme_mode(choice: str | None) -> str:
    if choice in {"auto", "light", "dark"}:
        return choice
    for language in ("ko", "en"):
        labels = LABELS[language]
        if choice == labels["theme_light"]:
            return "light"
        if choice == labels["theme_dark"]:
            return "dark"
        if choice == labels["theme_auto"]:
            return "auto"
    return "auto"


def _theme_label(mode: str, language: str) -> str:
    labels = LABELS[language]
    if mode == "light":
        return labels["theme_light"]
    if mode == "dark":
        return labels["theme_dark"]
    return labels["theme_auto"]


def _normalize_provider(provider: str) -> str:
    if provider in {LABELS["ko"]["replay"], LABELS["en"]["replay"]}:
        return "Replay only"
    if provider in {LABELS["ko"]["player_mode"], LABELS["en"]["player_mode"]}:
        return "Player mode"
    if provider == "OpenAI":
        return "OpenAI"
    if provider == "Anthropic":
        return "Anthropic"
    return "Replay only"


def _provider_label(provider: str, language: str) -> str:
    labels = LABELS[language]
    if provider == "Replay only":
        return labels["replay"]
    if provider == "Player mode":
        return labels["player_mode"]
    return provider


RunOutputs = tuple[
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    str,
    go.Figure,
    dict[str, Any],
    str,
    dict[str, dict[str, list[dict[str, Any]]]],
    dict[str, Any],
    str,
    go.Figure,
    go.Figure,
    go.Figure,
    go.Figure,
]
NoopRunOutputs: TypeAlias = tuple[
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
]
RunWithPlayerModeOutputs: TypeAlias = tuple[
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
]
PlayerAdvanceOutputs: TypeAlias = tuple[
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
    Any,
]


AGENT_EDITOR_LANGUAGE_STATE_BLOCK = (
    6 + len(PERSONA_TRAIT_FIELDS) + len(HEXACO_QUESTIONNAIRE_ITEMS)
)


def _questionnaire_response_value(value: Any) -> int:
    try:
        candidate = int(value)
    except (TypeError, ValueError):
        return QUESTIONNAIRE_RESPONSE_DEFAULT
    if 1 <= candidate <= 5:
        return candidate
    return QUESTIONNAIRE_RESPONSE_DEFAULT


def _questionnaire_mode_value(value: Any) -> str:
    candidate = str(value or QUESTIONNAIRE_MODE_SLIDERS)
    if candidate in {QUESTIONNAIRE_MODE_SLIDERS, QUESTIONNAIRE_MODE_HEXACO}:
        return candidate
    return QUESTIONNAIRE_MODE_SLIDERS


def _agent_editor_state_blocks(*values: Any) -> list[dict[str, Any]] | None:
    if not values:
        return None
    expected = AGENT_EDITOR_SLOT_COUNT * AGENT_EDITOR_LANGUAGE_STATE_BLOCK
    if len(values) != expected:
        raise ValueError(
            "unexpected number of agent editor state values: "
            f"{len(values)} (expected {expected})"
        )
    blocks: list[dict[str, Any]] = []
    block_size = AGENT_EDITOR_LANGUAGE_STATE_BLOCK
    for slot_index in range(AGENT_EDITOR_SLOT_COUNT):
        offset = slot_index * block_size
        trait_start = offset + 6
        questionnaire_start = trait_start + len(PERSONA_TRAIT_FIELDS)
        blocks.append(
            {
                "persona_preset": str(values[offset]),
                "routine_preset": str(values[offset + 1]),
                "name": str(values[offset + 2]),
                "age": int(values[offset + 3]),
                "routine_text": str(values[offset + 4]),
                "personality_input_mode": _questionnaire_mode_value(values[offset + 5]),
                "personality": {
                    field_name: float(value)
                    for field_name, value in zip(
                        PERSONA_TRAIT_FIELDS,
                        values[trait_start:questionnaire_start],
                        strict=True,
                    )
                },
                "questionnaire_responses": {
                    item.item_id: _questionnaire_response_value(
                        values[questionnaire_start + item_index]
                    )
                    for item_index, item in enumerate(HEXACO_QUESTIONNAIRE_ITEMS)
                },
            }
        )
    return blocks


def _trait_slider(
    field_name: str,
    labels: dict[str, str],
    *,
    value: float | None = None,
    elem_id_prefix: str = "trait",
) -> gr.Slider:
    return gr.Slider(
        label=labels[field_name],
        info=labels[f"{field_name}_info"],
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        value=float(PERSONA_TRAIT_DEFAULTS[field_name] if value is None else value),
        elem_id=f"{elem_id_prefix}-{field_name}",
    )


def _build_agent_editor_tab(
    *,
    slot_index: int,
    labels: dict[str, str],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    suffix = "" if slot_index == 0 else f"-{slot_index + 1}"
    trait_prefix = "trait" if slot_index == 0 else f"agent-{slot_index + 1}-trait"
    questionnaire_defaults = questionnaire_default_responses()
    controls: dict[str, Any] = {
        "questionnaire_domain_panels": {},
        "questionnaire_inputs": {},
        "trait_sliders": {},
    }

    with gr.Tab(
        _agent_tab_label(slot_index, "ko"),
        elem_id=f"agent-tab-{slot_index + 1}",
        interactive=bool(defaults["enabled"]),
    ) as tab:
        unavailable_note = gr.Markdown(
            labels["agent_tab_disabled"],
            visible=not bool(defaults["enabled"]),
            elem_id=f"agent-{slot_index + 1}-disabled-note",
        )
        with gr.Column(visible=bool(defaults["enabled"])) as editor_column:
            with gr.Row():
                name = gr.Textbox(
                    label=labels["name"],
                    value=defaults["name"],
                    elem_id=f"agent-name{suffix}",
                )
                age = gr.Slider(
                    label=labels["age"],
                    minimum=12,
                    maximum=80,
                    step=1,
                    value=int(defaults["age"]),
                    elem_id=f"agent-age{suffix}",
                )

            persona_preset = gr.Dropdown(
                label=labels["persona_preset"],
                choices=_persona_choices("ko"),
                value="",
                info=labels["persona_preset_info"],
                elem_id=f"persona-preset-dropdown{suffix}",
            )

            routine_preset = gr.Dropdown(
                label=labels["routine_preset"],
                choices=_routine_preset_choices("ko"),
                value="free",
                info=labels["routine_preset_info"],
                elem_id=f"routine-preset-dropdown{suffix}",
            )
            routine_text = gr.Textbox(
                label=labels["routine_text"],
                info=labels["routine_text_info"],
                lines=6,
                value=str(defaults.get("routine_text", "")),
                placeholder=labels["routine_text_placeholder"],
                elem_id=f"agent-routine-text{suffix}",
            )
            personality_input_mode = gr.Radio(
                label=questionnaire_mode_label("ko"),
                choices=questionnaire_mode_choices("ko"),
                value=QUESTIONNAIRE_MODE_SLIDERS,
                elem_id=f"personality-input-mode{suffix}",
            )
            questionnaire_panel = gr.Accordion(
                questionnaire_panel_label("ko"),
                open=False,
                visible=False,
                elem_id=f"hexaco-questionnaire-panel{suffix}",
            )
            with questionnaire_panel:
                questionnaire_intro = gr.Markdown(
                    questionnaire_intro_markdown("ko"),
                    elem_classes=["knoema-muted"],
                    elem_id=f"hexaco-questionnaire-intro{suffix}",
                )
                for domain in HEXACO_DOMAINS:
                    domain_panel = gr.Accordion(
                        questionnaire_domain_label(domain, "ko"),
                        open=False,
                        elem_id=f"hexaco-domain-{domain}{suffix}",
                    )
                    controls["questionnaire_domain_panels"][domain] = domain_panel
                    with domain_panel:
                        for item in questionnaire_domain_items(domain):
                            controls["questionnaire_inputs"][item.item_id] = gr.Slider(
                                label=item.label,
                                info=item.prompt("ko"),
                                minimum=1,
                                maximum=5,
                                step=1,
                                value=questionnaire_defaults[item.item_id],
                                elem_id=f"hexaco-item-{item.item_id}{suffix}",
                            )
                questionnaire_apply = gr.Button(
                    questionnaire_apply_label("ko"),
                    elem_id=f"hexaco-apply{suffix}",
                )
                questionnaire_summary = gr.Markdown(
                    questionnaire_empty_summary("ko"),
                    elem_id=f"hexaco-summary{suffix}",
                )

            tier_a_panel = gr.Accordion(
                labels["tier_a_panel"],
                open=True,
                elem_id=f"tier-a-panel{suffix}",
            )
            with tier_a_panel:
                with gr.Row():
                    for field_name in BIG_FIVE_FIELDS[:3]:
                        controls["trait_sliders"][field_name] = _trait_slider(
                            field_name,
                            labels,
                            value=float(defaults["personality"][field_name]),
                            elem_id_prefix=trait_prefix,
                        )
                with gr.Row():
                    for field_name in BIG_FIVE_FIELDS[3:]:
                        controls["trait_sliders"][field_name] = _trait_slider(
                            field_name,
                            labels,
                            value=float(defaults["personality"][field_name]),
                            elem_id_prefix=trait_prefix,
                        )

            extended_panel = gr.Accordion(
                labels["extended_panel"],
                open=True,
                elem_id=f"extended-personality-panel{suffix}",
            )
            with extended_panel:
                extended_panel_note = gr.Markdown(labels["extended_panel_note"])

                tier_bd_panel = gr.Accordion(
                    labels["tier_bd_panel"],
                    open=False,
                    elem_id=f"tier-bd-panel{suffix}",
                )
                with tier_bd_panel:
                    with gr.Row():
                        for field_name in TIER_BD_FIELDS:
                            controls["trait_sliders"][field_name] = _trait_slider(
                                field_name,
                                labels,
                                value=float(defaults["personality"][field_name]),
                                elem_id_prefix=trait_prefix,
                            )
                    honesty_humility_caveat = gr.Markdown(
                        _honesty_humility_caveat_markdown(KOREAN_CHOICE),
                        visible=True,
                        elem_classes=["knoema-muted"],
                        elem_id=f"honesty-humility-caveat{suffix}",
                    )

                tier_c_panel = gr.Accordion(
                    labels["tier_c_panel"],
                    open=False,
                    visible=False,
                    elem_id=f"tier-c-panel{suffix}",
                )
                with tier_c_panel:
                    dark_tetrad_notice = gr.Markdown(labels["dark_tetrad_notice"])
                    with gr.Row():
                        for field_name in TIER_C_FIELDS:
                            controls["trait_sliders"][field_name] = _trait_slider(
                                field_name,
                                labels,
                                value=float(defaults["personality"][field_name]),
                                elem_id_prefix=trait_prefix,
                            )

                tier_e_panel = gr.Accordion(
                    labels["tier_e_panel"],
                    open=False,
                    elem_id=f"tier-e-panel{suffix}",
                )
                with tier_e_panel, gr.Row():
                    for field_name in TIER_E_FIELDS:
                        controls["trait_sliders"][field_name] = _trait_slider(
                            field_name,
                            labels,
                            value=float(defaults["personality"][field_name]),
                            elem_id_prefix=trait_prefix,
                        )

                tier_f_panel = gr.Accordion(
                    labels["tier_f_panel"],
                    open=False,
                    elem_id=f"tier-f-panel{suffix}",
                )
                with tier_f_panel, gr.Row():
                    for field_name in TIER_F_FIELDS:
                        controls["trait_sliders"][field_name] = _trait_slider(
                            field_name,
                            labels,
                            value=float(defaults["personality"][field_name]),
                            elem_id_prefix=trait_prefix,
                        )

                tier_g_panel = gr.Accordion(
                    labels["tier_g_panel"],
                    open=False,
                    elem_id=f"tier-g-panel{suffix}",
                )
                with tier_g_panel:
                    for row_fields in TIER_G_ROWS:
                        with gr.Row():
                            for field_name in row_fields:
                                controls["trait_sliders"][field_name] = _trait_slider(
                                    field_name,
                                    labels,
                                    value=float(defaults["personality"][field_name]),
                                    elem_id_prefix=trait_prefix,
                                )

    controls.update(
        {
            "tab": tab,
            "editor_column": editor_column,
            "unavailable_note": unavailable_note,
            "name": name,
            "age": age,
            "persona_preset": persona_preset,
            "routine_preset": routine_preset,
            "routine_text": routine_text,
            "personality_input_mode": personality_input_mode,
            "questionnaire_apply": questionnaire_apply,
            "questionnaire_intro": questionnaire_intro,
            "questionnaire_panel": questionnaire_panel,
            "questionnaire_summary": questionnaire_summary,
            "tier_a_panel": tier_a_panel,
            "extended_panel": extended_panel,
            "extended_panel_note": extended_panel_note,
            "tier_bd_panel": tier_bd_panel,
            "honesty_humility_caveat": honesty_humility_caveat,
            "tier_c_panel": tier_c_panel,
            "dark_tetrad_notice": dark_tetrad_notice,
            "tier_e_panel": tier_e_panel,
            "tier_f_panel": tier_f_panel,
            "tier_g_panel": tier_g_panel,
        }
    )
    return controls


def _resolve_run_request(
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
) -> dict[str, Any]:
    primary_routine_text = ""
    primary_routine_specified = False
    extra_agent_routine_specified = False
    event_injections_text = ""
    initial_relationships_text = ""
    legacy_with_language = len(PERSONA_TRAIT_FIELDS) + 5
    legacy_without_language = len(PERSONA_TRAIT_FIELDS) + 4
    routine_with_language = len(PERSONA_TRAIT_FIELDS) + 6
    routine_without_language = len(PERSONA_TRAIT_FIELDS) + 5
    legacy_batch_with_language = legacy_with_language + 3
    legacy_batch_without_language = legacy_without_language + 3
    routine_batch_with_language = routine_with_language + 3
    routine_batch_without_language = routine_without_language + 3
    extra_agent_block = (AGENT_EDITOR_SLOT_COUNT - 1) * (2 + len(PERSONA_TRAIT_FIELDS))
    routine_extra_agent_block = (AGENT_EDITOR_SLOT_COUNT - 1) * (3 + len(PERSONA_TRAIT_FIELDS))
    multi_with_language = legacy_with_language + extra_agent_block
    multi_without_language = legacy_without_language + extra_agent_block
    multi_with_language_routine = routine_with_language + routine_extra_agent_block
    multi_without_language_routine = routine_without_language + routine_extra_agent_block
    multi_batch_with_language = multi_with_language + 3
    multi_batch_without_language = multi_without_language + 3
    multi_batch_with_language_routine = multi_with_language_routine + 3
    multi_batch_without_language_routine = multi_without_language_routine + 3
    legacy_lengths = {
        multi_batch_with_language_routine,
        multi_batch_without_language_routine,
        multi_with_language_routine,
        multi_without_language_routine,
        multi_batch_with_language,
        multi_batch_without_language,
        multi_with_language,
        multi_without_language,
        routine_batch_with_language,
        routine_batch_without_language,
        legacy_batch_with_language,
        legacy_batch_without_language,
        routine_with_language,
        routine_without_language,
        legacy_with_language,
        legacy_without_language,
    }
    if (
        len(trait_and_runtime) >= 2
        and isinstance(trait_and_runtime[-2], str)
        and isinstance(trait_and_runtime[-1], str)
        and (len(trait_and_runtime) - 2) in legacy_lengths
    ):
        event_injections_text = str(trait_and_runtime[-2])
        initial_relationships_text = str(trait_and_runtime[-1])
        trait_and_runtime = trait_and_runtime[:-2]

    multi_agent_values: list[Any] = []
    batch_mode = False
    batch_runs = 10
    master_seed = 20260419
    if len(trait_and_runtime) == multi_batch_with_language_routine:
        values = list(trait_and_runtime)
        primary_routine_specified = True
        extra_agent_routine_specified = True
        primary_routine_text = str(values[0])
        trait_values = values[1 : 1 + len(PERSONA_TRAIT_FIELDS)]
        remainder = values[1 + len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-8]
        (
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
            language_choice,
        ) = remainder[-8:]
    elif len(trait_and_runtime) == multi_batch_without_language_routine:
        values = list(trait_and_runtime)
        primary_routine_specified = True
        extra_agent_routine_specified = True
        primary_routine_text = str(values[0])
        trait_values = values[1 : 1 + len(PERSONA_TRAIT_FIELDS)]
        remainder = values[1 + len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-7]
        (
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
        ) = remainder[-7:]
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == multi_with_language_routine:
        values = list(trait_and_runtime)
        primary_routine_specified = True
        extra_agent_routine_specified = True
        primary_routine_text = str(values[0])
        trait_values = values[1 : 1 + len(PERSONA_TRAIT_FIELDS)]
        remainder = values[1 + len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-5]
        htn_enabled, planning_depth, ticks, agent_count, language_choice = remainder[-5:]
    elif len(trait_and_runtime) == multi_without_language_routine:
        values = list(trait_and_runtime)
        primary_routine_specified = True
        extra_agent_routine_specified = True
        primary_routine_text = str(values[0])
        trait_values = values[1 : 1 + len(PERSONA_TRAIT_FIELDS)]
        remainder = values[1 + len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-4]
        htn_enabled, planning_depth, ticks, agent_count = remainder[-4:]
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == multi_batch_with_language:
        values = list(trait_and_runtime)
        trait_values = values[: len(PERSONA_TRAIT_FIELDS)]
        remainder = values[len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-8]
        (
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
            language_choice,
        ) = remainder[-8:]
    elif len(trait_and_runtime) == multi_batch_without_language:
        values = list(trait_and_runtime)
        trait_values = values[: len(PERSONA_TRAIT_FIELDS)]
        remainder = values[len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-7]
        (
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
        ) = remainder[-7:]
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == multi_with_language:
        values = list(trait_and_runtime)
        trait_values = values[: len(PERSONA_TRAIT_FIELDS)]
        remainder = values[len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-5]
        htn_enabled, planning_depth, ticks, agent_count, language_choice = remainder[-5:]
    elif len(trait_and_runtime) == multi_without_language:
        values = list(trait_and_runtime)
        trait_values = values[: len(PERSONA_TRAIT_FIELDS)]
        remainder = values[len(PERSONA_TRAIT_FIELDS) :]
        multi_agent_values = remainder[:-4]
        htn_enabled, planning_depth, ticks, agent_count = remainder[-4:]
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == routine_batch_with_language:
        values = list(trait_and_runtime)
        primary_routine_specified = True
        primary_routine_text = str(values[0])
        (
            *trait_values,
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
            language_choice,
        ) = values[1:]
    elif (
        len(trait_and_runtime) == routine_batch_without_language
        and str(trait_and_runtime[-1]) not in LANGUAGE_CHOICES
    ):
        values = list(trait_and_runtime)
        primary_routine_specified = True
        primary_routine_text = str(values[0])
        (
            *trait_values,
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
        ) = values[1:]
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == legacy_batch_with_language:
        (
            *trait_values,
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
            language_choice,
        ) = trait_and_runtime
    elif len(trait_and_runtime) == legacy_batch_without_language:
        (
            *trait_values,
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
        ) = trait_and_runtime
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == routine_with_language:
        values = list(trait_and_runtime)
        primary_routine_specified = True
        primary_routine_text = str(values[0])
        *trait_values, htn_enabled, planning_depth, ticks, agent_count, language_choice = values[1:]
    elif (
        len(trait_and_runtime) == routine_without_language
        and str(trait_and_runtime[-1]) not in LANGUAGE_CHOICES
    ):
        values = list(trait_and_runtime)
        primary_routine_specified = True
        primary_routine_text = str(values[0])
        *trait_values, htn_enabled, planning_depth, ticks, agent_count = values[1:]
        language_choice = KOREAN_CHOICE
    elif len(trait_and_runtime) == legacy_with_language:
        *trait_values, htn_enabled, planning_depth, ticks, agent_count, language_choice = (
            trait_and_runtime
        )
    elif len(trait_and_runtime) == legacy_without_language:
        *trait_values, htn_enabled, planning_depth, ticks, agent_count = trait_and_runtime
        language_choice = KOREAN_CHOICE
    else:  # pragma: no cover - defensive guard
        raise ValueError(
            "unexpected number of personality/runtime values: "
            f"{len(trait_and_runtime)}"
        )

    language = _language_key(str(language_choice))
    personality_overrides = {
        field_name: float(value)
        for field_name, value in zip(PERSONA_TRAIT_FIELDS, trait_values, strict=True)
    }
    agent_overrides = [
        {
            "name": primary_name,
            "age": int(primary_age),
            "personality_overrides": personality_overrides,
            "planning": bool(htn_enabled),
            **({"routine_text": primary_routine_text} if primary_routine_specified else {}),
        }
    ]
    if multi_agent_values:
        block_size = (3 if extra_agent_routine_specified else 2) + len(PERSONA_TRAIT_FIELDS)
        for slot_index in range(0, len(multi_agent_values), block_size):
            name = str(multi_agent_values[slot_index])
            age = int(multi_agent_values[slot_index + 1])
            trait_start = slot_index + 2
            routine_text = ""
            if extra_agent_routine_specified:
                routine_text = str(multi_agent_values[slot_index + 2])
                trait_start += 1
            slot_traits = multi_agent_values[
                trait_start : trait_start + len(PERSONA_TRAIT_FIELDS)
            ]
            override = {
                "name": name,
                "age": age,
                "personality_overrides": {
                    field_name: float(value)
                    for field_name, value in zip(
                        PERSONA_TRAIT_FIELDS,
                        slot_traits,
                        strict=True,
                    )
                },
            }
            if extra_agent_routine_specified:
                override["routine_text"] = routine_text
            agent_overrides.append(override)

    normalized_provider = _normalize_provider(provider)
    return {
        "scenario_name": scenario_name,
        "environment_preset_id": environment_preset_id,
        "cultural_prior_id": cultural_prior_id,
        "provider": normalized_provider,
        "provider_label": _provider_label(normalized_provider, language),
        "api_key": api_key,
        "model": model,
        "primary_name": primary_name,
        "primary_age": int(primary_age),
        "personality_overrides": personality_overrides,
        "ticks": int(ticks),
        "agent_count": int(agent_count),
        "agent_overrides": agent_overrides,
        "primary_planning_enabled": bool(htn_enabled),
        "planning_depth": int(planning_depth),
        "batch_mode": bool(batch_mode),
        "batch_runs": int(batch_runs),
        "master_seed": int(master_seed),
        "language": language,
        "event_injections_text": event_injections_text,
        "initial_relationships_text": initial_relationships_text,
    }


def _reviewer_alias_map(result: Any) -> dict[str, str]:
    agent_ids = sorted(
        set(getattr(result, "action_breakdown", {}))
        | set(getattr(result, "memory_snapshot", {}))
        | {str(row.get("source", "")) for row in getattr(result, "relationship_rows", []) if row.get("source")}
        | {str(row.get("target", "")) for row in getattr(result, "relationship_rows", []) if row.get("target")}
    )
    aliases: dict[str, str] = {}
    for index, agent_id in enumerate(agent_ids):
        aliases[agent_id] = f"Agent {chr(65 + index)}"
    return aliases


def _sanitize_text(text: str, aliases: dict[str, str]) -> str:
    sanitized = str(text)
    for original, alias in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        sanitized = sanitized.replace(original, alias)
    return sanitized


def _sanitize_value(value: Any, aliases: dict[str, str]) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value, aliases)
    if isinstance(value, dict):
        return {
            (_sanitize_text(key, aliases) if isinstance(key, str) else key): _sanitize_value(item, aliases)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitize_value(item, aliases) for item in value]
    return value


def _reviewer_jsonl_text(jsonl_text: str, aliases: dict[str, str]) -> str:
    rows = _jsonl_rows(jsonl_text)
    return "\n".join(
        json.dumps(_sanitize_value(row, aliases), ensure_ascii=False, sort_keys=True)
        for row in rows
    )


def _reviewer_download_path(jsonl_text: str) -> str:
    export_path = Path(tempfile.gettempdir()) / f"knoema_reviewer_run_{uuid.uuid4().hex}.jsonl"
    export_path.write_text(jsonl_text, encoding="utf-8")
    return str(export_path)


def _render_result_outputs(
    result: Any,
    *,
    mode_label: str,
    provider: str,
    api_key: str,
    language: str,
    reviewer_mode: bool = False,
    theme_mode: str | None = None,
) -> RunOutputs:
    host_provider = host_key_active(provider, api_key)
    batch_result = getattr(result, "batch_result", None)
    aliases: dict[str, str] = {}
    if reviewer_mode:
        aliases = _reviewer_alias_map(result)
        rendered_jsonl = _reviewer_jsonl_text(result.jsonl, aliases)
        rendered_memory_snapshot = cast(
            "dict[str, dict[str, list[dict[str, Any]]]]",
            _sanitize_value(result.memory_snapshot, aliases),
        )
        rendered_relationship_rows = cast(
            "list[dict[str, object]]",
            _sanitize_value(result.relationship_rows, aliases),
        )
        rendered_action_breakdown = cast(
            "dict[str, dict[str, int]]",
            _sanitize_value(result.action_breakdown, aliases),
        )
        rendered_timeline = _sanitize_text(result.timeline_markdown, aliases)
        rendered_monologue = _sanitize_text(result.monologue_markdown, aliases)
        rendered_plan = _sanitize_text(result.plan_markdown, aliases)
        download_path = _reviewer_download_path(rendered_jsonl)
    else:
        rendered_jsonl = result.jsonl
        rendered_memory_snapshot = result.memory_snapshot
        rendered_relationship_rows = result.relationship_rows
        rendered_action_breakdown = result.action_breakdown
        rendered_timeline = result.timeline_markdown
        rendered_monologue = result.monologue_markdown
        rendered_plan = result.plan_markdown
        download_path = result.download_path
    if language == "ko":
        summary = (
            f"모드: {mode_label} | 에이전트: {result.agent_count}명 | "
            f"틱: {result.tick_count} | 로그 항목: {result.log_count}"
        )
        if batch_result is not None:
            summary += (
                f" | 배치: {batch_result.batch_size}회"
                f" | 재현성 계수: {batch_result.reproducibility_coefficient:.3f}"
                f" | 마스터 시드: {batch_result.master_seed}"
            )
        if host_provider:
            summary += f" | (Celovin 호스트 {host_provider} 키 사용 중 - 데모 전용)"
    else:
        summary = (
            f"Mode: {mode_label} | Agents: {result.agent_count} | "
            f"Ticks: {result.tick_count} | Log entries: {result.log_count}"
        )
        if batch_result is not None:
            summary += (
                f" | Batch runs: {batch_result.batch_size}"
                f" | Reproducibility: {batch_result.reproducibility_coefficient:.3f}"
                f" | Master seed: {batch_result.master_seed}"
            )
        if host_provider:
            summary += f" | (Celovin host {host_provider} key in use - demo only)"
    summary += f" | {_relationship_accessibility_text(rendered_relationship_rows, language=language)}"
    agent_ids = sorted(
        set(rendered_action_breakdown)
        | set(rendered_memory_snapshot)
        | {str(row["source"]) for row in rendered_relationship_rows}
        | {str(row["target"]) for row in rendered_relationship_rows}
    )
    agent_colors = _agent_color_map(agent_ids)
    memory_snapshot, memory_agent, memory_markdown, emotion_trajectory = _memory_inspector_outputs(
        rendered_memory_snapshot,
        language=language,
        batch_mode=batch_result is not None,
    )
    return (
        _timeline_markdown_with_agent_colors(
            rendered_jsonl,
            rendered_timeline,
            agent_colors,
            language=language,
        ),
        _conversation_threads_markdown(
            rendered_jsonl,
            rendered_memory_snapshot,
            agent_colors,
            language=language,
        ),
        _relationship_graph_html(
            rendered_relationship_rows,
            language=language,
            agent_colors=agent_colors,
            theme_mode=theme_mode,
        ),
        rendered_monologue,
        rendered_plan,
        rendered_jsonl,
        download_path,
        _sanitize_text(summary, aliases) if reviewer_mode else summary,
        _action_chart_figure(rendered_action_breakdown, language=language),
        gr.update(minimum=-1, maximum=max(-1, int(result.tick_count) - 1), value=-1),
        _tick_focus_markdown(rendered_jsonl, -1, language=language),
        memory_snapshot,
        memory_agent,
        memory_markdown,
        emotion_trajectory,
        _spatial_heatmap_figure(rendered_jsonl, rendered_memory_snapshot, language=language),
        _action_flow_figure(rendered_jsonl, language=language),
        _mini_map_figure(rendered_jsonl, -1, language=language),
    )


def _relationship_accessibility_text(
    rows: list[dict[str, object]],
    *,
    language: str = "en",
) -> str:
    labels = LABELS[language]
    if not rows:
        if language == "ko":
            return f"{labels['graph_a11y']}: 아직 관계 간선이 없습니다."
        return f"{labels['graph_a11y']}: no relationship edges yet."

    strongest = max(
        rows,
        key=lambda row: (
            float(row.get("trust", 0.0)),
            float(row.get("weight", 0.0)),
        ),
    )
    source = str(strongest.get("source", "unknown"))
    target = str(strongest.get("target", "unknown"))
    trust = float(strongest.get("trust", 0.0))
    weight = float(strongest.get("weight", 0.0))
    edge_count = len(rows)
    if language == "ko":
        return (
            f"{labels['graph_a11y']}: 관계 간선 {edge_count}개, "
            f"가장 강한 연결 {source} -> {target}, 신뢰 {trust:.2f}, 가중치 {weight:.2f}."
        )
    return (
        f"{labels['graph_a11y']}: {edge_count} relationship edges; "
        f"strongest link {source} -> {target}, trust {trust:.2f}, weight {weight:.2f}."
    )


def _run(
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
    reviewer_mode: bool = False,
    theme_mode: str | None = None,
) -> RunOutputs:
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
    )
    if request["provider"] == "Player mode":
        _session, result, _status = start_player_session(
            scenario_name=str(request["scenario_name"]),
            primary_name=str(request["primary_name"]),
            primary_age=int(request["primary_age"]),
            personality_overrides=dict(request["personality_overrides"]),
            ticks=int(request["ticks"]),
            agent_count=int(request["agent_count"]),
            environment_preset_id=cast("str | None", request["environment_preset_id"]),
            cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
            agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
            primary_planning_enabled=bool(request["primary_planning_enabled"]),
            planning_depth=int(request["planning_depth"]),
            language=str(request["language"]),
            event_injections_text=str(request["event_injections_text"]),
            initial_relationships_text=str(request["initial_relationships_text"]),
        )
    else:
        result = run_playground_scenario(
            scenario_name=str(request["scenario_name"]),
            provider=cast("Provider", request["provider"]),
            api_key=str(request["api_key"]),
            model=str(request["model"]),
            primary_name=str(request["primary_name"]),
            primary_age=int(request["primary_age"]),
            openness=float(dict(request["personality_overrides"])["openness"]),
            conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
            extraversion=float(dict(request["personality_overrides"])["extraversion"]),
            agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
            neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
            personality_overrides=dict(request["personality_overrides"]),
            ticks=int(request["ticks"]),
            agent_count=int(request["agent_count"]),
            environment_preset_id=cast("str | None", request["environment_preset_id"]),
            cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
            agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
            primary_planning_enabled=bool(request["primary_planning_enabled"]),
            planning_depth=int(request["planning_depth"]),
            batch_mode=bool(request["batch_mode"]),
            batch_runs=int(request["batch_runs"]),
            master_seed=int(request["master_seed"]),
            language=str(request["language"]),
            event_injections_text=str(request["event_injections_text"]),
            initial_relationships_text=str(request["initial_relationships_text"]),
        )
    return _render_result_outputs(
        result,
        mode_label=str(request["provider_label"]),
        provider=str(request["provider"]),
        api_key=str(request["api_key"]),
        language=str(request["language"]),
        reviewer_mode=reviewer_mode,
        theme_mode=theme_mode,
    )


def _run_with_player_mode(
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
    reviewer_mode: bool = False,
    theme_mode: str | None = None,
) -> RunWithPlayerModeOutputs:
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
    )
    if request["provider"] == "Player mode":
        session, result, status = start_player_session(
            scenario_name=str(request["scenario_name"]),
            primary_name=str(request["primary_name"]),
            primary_age=int(request["primary_age"]),
            personality_overrides=dict(request["personality_overrides"]),
            ticks=int(request["ticks"]),
            agent_count=int(request["agent_count"]),
            environment_preset_id=cast("str | None", request["environment_preset_id"]),
            cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
            agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
            primary_planning_enabled=bool(request["primary_planning_enabled"]),
            planning_depth=int(request["planning_depth"]),
            language=str(request["language"]),
            event_injections_text=str(request["event_injections_text"]),
            initial_relationships_text=str(request["initial_relationships_text"]),
        )
        return (
            *_render_result_outputs(
                result,
                mode_label=str(request["provider_label"]),
                provider=str(request["provider"]),
                api_key="",
                language=str(request["language"]),
                reviewer_mode=reviewer_mode,
                theme_mode=theme_mode,
            ),
            gr.update(value=None),
            session,
            status,
        )

    result = run_playground_scenario(
        scenario_name=str(request["scenario_name"]),
        provider=cast("Provider", request["provider"]),
        api_key=str(request["api_key"]),
        model=str(request["model"]),
        primary_name=str(request["primary_name"]),
        primary_age=int(request["primary_age"]),
        openness=float(dict(request["personality_overrides"])["openness"]),
        conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
        extraversion=float(dict(request["personality_overrides"])["extraversion"]),
        agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
        neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
        personality_overrides=dict(request["personality_overrides"]),
        ticks=int(request["ticks"]),
        agent_count=int(request["agent_count"]),
        environment_preset_id=cast("str | None", request["environment_preset_id"]),
        cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
        agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
        primary_planning_enabled=bool(request["primary_planning_enabled"]),
        planning_depth=int(request["planning_depth"]),
        batch_mode=bool(request["batch_mode"]),
        batch_runs=int(request["batch_runs"]),
        master_seed=int(request["master_seed"]),
        language=str(request["language"]),
        event_injections_text=str(request["event_injections_text"]),
        initial_relationships_text=str(request["initial_relationships_text"]),
    )
    return (
        *_render_result_outputs(
            result,
            mode_label=str(request["provider_label"]),
            provider=str(request["provider"]),
            api_key=str(request["api_key"]),
            language=str(request["language"]),
            reviewer_mode=reviewer_mode,
            theme_mode=theme_mode,
        ),
        gr.update(value=None),
        None,
        "",
    )


def _noop_run_outputs() -> NoopRunOutputs:
    return cast(NoopRunOutputs, tuple(gr.update() for _ in range(18)))


def _coerce_plotly_figure(figure: Any) -> go.Figure:
    if isinstance(figure, go.Figure):
        return figure
    if isinstance(figure, dict):
        return go.Figure(figure)
    return go.Figure()


def _resolved_language_key(language: str) -> str:
    if language in {"ko", "en"}:
        return language
    return _language_key(language)


def _gradio_file_url(path: Path) -> str:
    return f"/gradio_api/file={quote(path.resolve().as_posix(), safe='/')}"


def _resolved_force_graph_theme(theme_mode: str | None) -> str:
    return "dark" if _normalize_theme_mode(theme_mode) == "dark" else "light"


def _force_graph_payload_token(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(serialized).decode("ascii").rstrip("=")


def _decode_force_graph_payload(token: str) -> dict[str, Any]:
    padding = "=" * (-len(token) % 4)
    decoded = base64.urlsafe_b64decode((token + padding).encode("ascii"))
    return cast("dict[str, Any]", json.loads(decoded.decode("utf-8")))


def _html_attr_value(markup: str, attribute: str) -> str | None:
    prefix = f'{attribute}="'
    if prefix not in markup:
        return None
    _, remainder = markup.split(prefix, 1)
    value, _sep, _tail = remainder.partition('"')
    return value or None


@lru_cache(maxsize=1)
def _force_graph_template() -> str:
    if FORCE_GRAPH_HTML_PATH.exists():
        return FORCE_GRAPH_HTML_PATH.read_text(encoding="utf-8")
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Relationship graph</title>
</head>
<body>
<!-- KNOEMA_FORCE_GRAPH_BOOTSTRAP -->
<p>Force graph asset missing.</p>
</body>
</html>
"""


def _relationship_graph_payload(
    rows: list[dict[str, Any]],
    *,
    language: str = "en",
    agent_colors: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not rows:
        return {"language": _resolved_language_key(language), "nodes": [], "links": []}

    agents = sorted({str(row["source"]) for row in rows} | {str(row["target"]) for row in rows})
    color_map = agent_colors or _agent_color_map(agents)
    graph = _relationship_layout_graph(agents, rows)
    node_degrees = dict(graph.degree())
    edge_weights = [_relationship_metric(row, "weight") for row in rows]
    edge_trusts = [_relationship_metric(row, "trust") for row in rows]

    nodes = [
        {
            "id": agent,
            "label": agent,
            "color": color_map.get(agent, "#0f172a"),
            "degree": int(node_degrees.get(agent, 0)),
            "size": min(30, 12 + int(node_degrees.get(agent, 0)) * 4),
            "showLabel": True,
        }
        for agent in agents
    ]
    links: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        source = str(row["source"])
        target = str(row["target"])
        normalized_weight = _normalized_metric(edge_weights[index], edge_weights)
        normalized_trust = _normalized_metric(edge_trusts[index], edge_trusts)
        links.append(
            {
                "source": source,
                "target": target,
                "weight": _relationship_metric(row, "weight"),
                "trust": _relationship_metric(row, "trust"),
                "width": round(1.0 + 5.0 * normalized_weight, 3),
                "distance": round(78.0 + 28.0 * (1.0 - normalized_weight), 3),
                "color": f"rgba(100,116,139,{0.18 + 0.62 * normalized_trust:.3f})",
                "label": (
                    f"{source} -> {target} ({row.get('relationship_type', 'unknown')})"
                    f"\ntrust={_relationship_metric(row, 'trust'):.2f}"
                    f"\nweight={_relationship_metric(row, 'weight'):.2f}"
                ),
            }
        )
    return {"language": _resolved_language_key(language), "nodes": nodes, "links": links}


def _force_graph_srcdoc(payload: dict[str, Any], *, theme_mode: str | None = None) -> str:
    bootstrap = {
        "theme": _resolved_force_graph_theme(theme_mode),
        "graphData": payload,
        "vendorUrl": _gradio_file_url(FORCE_GRAPH_VENDOR_PATH) if FORCE_GRAPH_VENDOR_PATH.exists() else "",
        "cdnUrl": FORCE_GRAPH_CDN_URL,
    }
    script = (
        "<script>window.KNOEMA_FORCE_GRAPH_BOOT = "
        + json.dumps(bootstrap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        + ";</script>"
    )
    return _force_graph_template().replace("<!-- KNOEMA_FORCE_GRAPH_BOOTSTRAP -->", script, 1)


def _force_graph_iframe_html(
    payload: dict[str, Any],
    *,
    language: str = "en",
    theme_mode: str | None = None,
) -> str:
    language_key = _resolved_language_key(language)
    title = LABELS[language_key]["graph"]
    payload_token = _force_graph_payload_token(payload)
    srcdoc = _force_graph_srcdoc(payload, theme_mode=theme_mode)
    return (
        '<div class="knoema-force-graph-shell"'
        ' data-knoema-force-graph="1"'
        f' data-knoema-language="{escape(language_key, quote=True)}"'
        f' data-knoema-payload="{escape(payload_token, quote=True)}">'
        f'<iframe class="knoema-force-graph-frame" title="{escape(title, quote=True)}"'
        ' loading="lazy" referrerpolicy="no-referrer"'
        f' srcdoc="{escape(srcdoc, quote=True)}"></iframe>'
        "</div>"
    )


def _relationship_graph_placeholder_html(language: str = "en") -> str:
    language_key = _resolved_language_key(language)
    title = "관계 그래프" if language_key == "ko" else "Relationship graph"
    empty_msg = (
        "관계 연결이 아직 없습니다. 틱을 더 실행하거나 대화형 시나리오를 사용해 보세요."
        if language_key == "ko"
        else "No relationship edges yet. Run more ticks or use a conversational scenario."
    )
    return (
        '<div class="knoema-force-graph-shell" data-knoema-force-graph="0">'
        '<div style="min-height: 620px; display: flex; align-items: center; justify-content: center;'
        ' border: 1px solid rgba(100, 116, 139, 0.25); border-radius: 8px;'
        ' background: rgba(248,250,252,1); color: #0f172a; padding: 24px; text-align: center;">'
        f'<div><strong>{escape(title)}</strong><div style="margin-top: 12px;">{escape(empty_msg)}</div></div>'
        "</div></div>"
    )


def _relationship_graph_html(
    rows: list[dict[str, Any]],
    *,
    language: str = "en",
    agent_colors: dict[str, str] | None = None,
    theme_mode: str | None = None,
) -> str:
    if not rows:
        return _relationship_graph_placeholder_html(language)
    payload = _relationship_graph_payload(
        rows,
        language=language,
        agent_colors=agent_colors,
    )
    return _force_graph_iframe_html(
        payload,
        language=language,
        theme_mode=theme_mode,
    )


def _relationship_graph_theme_update(graph_html: str, theme_mode: str) -> str:
    if 'data-knoema-force-graph="1"' not in graph_html:
        return graph_html
    payload_token = _html_attr_value(graph_html, "data-knoema-payload")
    language_key = _html_attr_value(graph_html, "data-knoema-language") or "en"
    if not payload_token:
        return graph_html
    try:
        payload = _decode_force_graph_payload(payload_token)
    except (ValueError, json.JSONDecodeError):
        return graph_html
    return _force_graph_iframe_html(payload, language=language_key, theme_mode=theme_mode)


def _report_section(title: str, body: str, *, language: str = "en") -> str:
    if not str(body).strip():
        empty_text = "데이터가 아직 없습니다." if _language_key(language) == "ko" else "No data available."
        return (
            f"<section><h2>{escape(title)}</h2>"
            f"<p class='empty'>{escape(empty_text)}</p></section>"
        )
    return (
        f"<section><h2>{escape(title)}</h2>"
        f"<pre>{escape(str(body))}</pre></section>"
    )


def _prereg_defaults(language: str) -> dict[str, str]:
    key = language if language in {"ko", "en"} else _language_key(language)
    if key == "ko":
        return {
            "title": "Knoema 사회 관계 재생 실험서",
            "hypotheses": (
                "H1. 친화성과 배려/위해 점수가 높을수록 협조적인 행동 비율이 늘어난다.\n"
                "H2. 정서 불안정성과 권력 성향이 높을수록 스트레스 상황에서 거절 / 위협 행동이 증가한다."
            ),
            "design": (
                "결정론적 시드를 기반으로 JSONL 로그를 구축하는 synthetic replay 연구. "
                "같은 시나리오를 여러 시드로 반복 실행하고 tick 예산은 분석 프로토콜에 고정합니다."
            ),
            "outcomes": (
                "1차 지표: 협조적인 action 비율\n"
                "보조 지표: 신뢰 가중치 변화, 에이전트별 행동 다양도, 감정 단계 데이터"
            ),
            "analysis": (
                "배치 결과를 비교하여 순위기반 검정과 효과크기를 산출하고, "
                "에이전트별 행동카운트와 관계 변화로 2차적 해석을 결합합니다."
            ),
            "deviations": "일탈 없음.",
        }
    return {
        "title": "Knoema social replay study",
        "hypotheses": (
            "H1. Higher agreeableness and care/harm scores increase cooperative action frequency.\n"
            "H2. Higher emotional volatility and power increase refusal or threat actions under stress."
        ),
        "design": (
            "Synthetic replay study with deterministic seeds, JSONL logging, and a fixed tick budget. "
            "The same scenario is repeated across multiple seeds before interpretation."
        ),
        "outcomes": (
            "Primary outcome: cooperative action rate.\n"
            "Secondary outcomes: trust delta, per-agent action diversity, emotion trajectory stability."
        ),
        "analysis": (
            "Compare batch runs with rank-based tests and effect sizes, then inspect per-agent counts "
            "and relationship drift before interpreting qualitative traces."
        ),
        "deviations": "No deviations recorded.",
    }


def _power_test_choices(language: str) -> list[tuple[str, str]]:
    key = language if language in {"ko", "en"} else _language_key(language)
    if key == "ko":
        return [
            ("독립표본 t 검정", "independent_t"),
            ("대응표본 t 검정", "paired_t"),
            ("두 비율 비교", "two_proportions"),
        ]
    return [
        ("Independent-samples t-test", "independent_t"),
        ("Paired-samples t-test", "paired_t"),
        ("Two-proportion z-test", "two_proportions"),
    ]


def _power_defaults() -> dict[str, float | str]:
    return {
        "test_family": "independent_t",
        "effect_size": 0.5,
        "alpha": 0.05,
        "target_power": 0.8,
        "planned_n": float(
            estimate_sample_size(
                effect_size=0.5,
                alpha=0.05,
                target_power=0.8,
                test_family="independent_t",
            ).total_sample_size
        ),
    }


def _power_analysis_plan(
    test_family: str,
    effect_size: float,
    alpha: float,
    target_power: float,
) -> PowerAnalysisPlan:
    return estimate_sample_size(
        effect_size=max(float(effect_size), 0.01),
        alpha=min(max(float(alpha), 0.001), 0.2),
        target_power=min(max(float(target_power), 0.5), 0.99),
        test_family=cast("str", test_family),
    )


def _power_analysis_markdown(
    language: str,
    test_family: str,
    effect_size: float,
    alpha: float,
    target_power: float,
) -> str:
    plan = _power_analysis_plan(test_family, effect_size, alpha, target_power)
    key = language if language in {"ko", "en"} else _language_key(language)
    if key == "ko":
        return "\n".join(
            [
                f"- 권장 총 표본수: **{plan.total_sample_size}**",
                f"- 군/조건당 표본수: **{plan.sample_size_per_group}**",
                f"- 효과크기: `{plan.effect_size:.2f}` | alpha `{plan.alpha:.3f}` | power `{plan.target_power:.2f}`",
                f"- 방법: {plan.method}",
            ]
        )
    return "\n".join(
        [
            f"- Recommended total sample size: **{plan.total_sample_size}**",
            f"- Balanced sample size per group / condition: **{plan.sample_size_per_group}**",
            f"- Effect size: `{plan.effect_size:.2f}` | alpha `{plan.alpha:.3f}` | power `{plan.target_power:.2f}`",
            f"- Method: {plan.method}",
        ]
    )


def _power_analysis_updates(
    language: str,
    test_family: str,
    effect_size: float,
    alpha: float,
    target_power: float,
) -> tuple[float, str]:
    plan = _power_analysis_plan(test_family, effect_size, alpha, target_power)
    return float(plan.total_sample_size), _power_analysis_markdown(
        language,
        test_family,
        effect_size,
        alpha,
        target_power,
    )


def _deposit_defaults(language: str) -> dict[str, str]:
    key = language if language in {"ko", "en"} else _language_key(language)
    if key == "ko":
        return {
            "creators": "Celovin",
            "description": "Knoema playground run export with JSONL log, current pre-registration draft, and upload metadata.",
            "keywords": "knoema, simulation, zenodo, arxiv",
        }
    return {
        "creators": "Celovin",
        "description": "Knoema playground run export with JSONL log, current pre-registration draft, and upload metadata.",
        "keywords": "knoema, simulation, zenodo, arxiv",
    }


def _simulation_template_defaults() -> dict[str, str]:
    return {
        "data_generation": "Freeze the scenario YAML, seed schedule, and agent overrides before interpretation.",
        "factor_design": "2 x 2 between-seed design over agreeableness profile and stressor intensity.",
        "performance_metrics": "Cooperation rate, refusal rate, trust delta, and mixed-effects coefficients.",
        "aggregation": "Aggregate over seeds first, then summarize agent-level dispersion and scenario-level uncertainty.",
    }


def _prereg_template_updates(template_id: str, language: str) -> tuple[Any, ...]:
    template = prereg_template_by_id(str(template_id))
    key = _language_key(language)
    planned_n = float(template.planned_n)
    return (
        template.title,
        template.hypotheses,
        template.design,
        template.data_generation,
        template.factor_design,
        template.outcomes,
        template.performance_metrics,
        template.aggregation,
        template.analysis,
        template.deviations if key == "en" else "일탈 없음.",
        planned_n,
        template.power_test,
        template.power_effect,
        template.power_alpha,
        template.power_target,
        _power_analysis_markdown(
            key,
            template.power_test,
            template.power_effect,
            template.power_alpha,
            template.power_target,
        ),
    )


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _attached_run_summary(summary: str, jsonl_text: str, language: str) -> str:
    rows = _jsonl_rows(jsonl_text)
    language_key = _language_key(language)
    batch_summary = next(
        (
            row
            for row in rows
            if str(row.get("record_type", "")) == "batch_summary"
        ),
        None,
    )
    tick_values = {
        int(row["tick"])
        for row in rows
        if row.get("tick") is not None
    }
    agent_ids = sorted(
        {
            str(row["agent_id"])
            for row in rows
            if row.get("agent_id")
        }
        | {
            str(row["source"])
            for row in rows
            if row.get("source")
        }
        | {
            str(row["target"])
            for row in rows
            if row.get("target")
        }
    )
    action_counts = Counter(
        str(row.get("action_type", ""))
        for row in rows
        if row.get("action_type")
    )
    top_actions = ", ".join(
        f"{action_type} x{count}"
        for action_type, count in action_counts.most_common(3)
    ) or ("없음" if language_key == "ko" else "none")
    if not rows:
        if language_key == "ko":
            return "- 아직 첨부된 실행 결과가 없습니다."
        return "- No run artifact is attached yet."

    if language_key == "ko":
        lines = [
            f"- 실행 요약: {summary or '해당 없음'}",
            f"- JSONL 해시: `{_digest_text(jsonl_text)[:16]}`",
            f"- 행 수: {len(rows)}",
            f"- 틱 범위: {min(tick_values) if tick_values else 0} ~ {max(tick_values) if tick_values else 0}",
            f"- 관측 에이전트: {', '.join(agent_ids) if agent_ids else '해당 없음'}",
            f"- 주요 행동: {top_actions}",
        ]
        if batch_summary is not None:
            lines.append(
                "- 배치 요약: "
                f"runs={int(batch_summary.get('batch_size', 0))}, "
                f"master_seed={int(batch_summary.get('master_seed', 0))}, "
                f"reproducibility={float(batch_summary.get('reproducibility_coefficient', 0.0)):.3f}"
            )
        return "\n".join(lines)

    lines = [
        f"- Summary: {summary or 'n/a'}",
        f"- JSONL digest: `{_digest_text(jsonl_text)[:16]}`",
        f"- Row count: {len(rows)}",
        f"- Tick span: {min(tick_values) if tick_values else 0} to {max(tick_values) if tick_values else 0}",
        f"- Agents observed: {', '.join(agent_ids) if agent_ids else 'n/a'}",
        f"- Top actions: {top_actions}",
    ]
    if batch_summary is not None:
        lines.append(
            "- Batch summary: "
            f"runs={int(batch_summary.get('batch_size', 0))}, "
            f"master_seed={int(batch_summary.get('master_seed', 0))}, "
            f"reproducibility={float(batch_summary.get('reproducibility_coefficient', 0.0)):.3f}"
        )
    return "\n".join(lines)


def _preregistration_markdown(
    summary: str,
    jsonl_text: str,
    language: str,
    title: str,
    hypotheses: str,
    design: str,
    outcomes: str,
    analysis_plan: str,
    freeze_after_run: bool,
    deviation_log: str,
    planned_n: float = 0.0,
    power_test_family: str = "independent_t",
    power_effect_size: float = 0.5,
    power_alpha: float = 0.05,
    power_target: float = 0.8,
    data_generation_process: str = "",
    factor_design_matrix: str = "",
    performance_metrics: str = "",
    aggregation_plan: str = "",
) -> str:
    key = _language_key(language)
    power_plan = _power_analysis_plan(
        power_test_family,
        power_effect_size,
        power_alpha,
        power_target,
    )
    planned_n_value = max(round(float(planned_n or 0.0)), power_plan.total_sample_size)
    freeze_fingerprint = _digest_text(
        json.dumps(
            {
                "title": title,
                "hypotheses": hypotheses,
                "design": design,
                "outcomes": outcomes,
                "analysis_plan": analysis_plan,
                "planned_n": planned_n_value,
                "power_test_family": power_test_family,
                "power_effect_size": round(power_effect_size, 4),
                "power_alpha": round(power_alpha, 4),
                "power_target": round(power_target, 4),
                "data_generation_process": data_generation_process,
                "factor_design_matrix": factor_design_matrix,
                "performance_metrics": performance_metrics,
                "aggregation_plan": aggregation_plan,
                "summary": summary,
                "jsonl_digest": _digest_text(jsonl_text),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )[:16]
    attached_run = _attached_run_summary(summary, jsonl_text, key)
    deviation_text = deviation_log.strip() or _prereg_defaults(key)["deviations"]
    if key == "ko":
        freeze_lines = [
            "1. 실행 후 시드, 결과 지표, 분석 계획을 논문화 전에 미리 정리합니다.",
            f"2. 고정 지문 `{freeze_fingerprint}`",
            "3. 결과 정리는 JSONL 해시와 요약 문장을 함께 보조 자료로 첨부합니다.",
        ]
        status = "적용" if freeze_after_run else "선택 사항"
        heading = "## OSF 형식 사전등록"
        sections = [
            heading,
            f"- 실행 후 고정: {status}",
            f"- 고정 지문: `{freeze_fingerprint}`",
            "",
            "### 연구 제목",
            title.strip(),
            "",
            "### 가설 / 연구 질문",
            hypotheses.strip(),
            "",
            "### 연구 설계",
            design.strip(),
            "",
            "### 데이터 생성 절차",
            data_generation_process.strip(),
            "",
            "### 요인 설계 행렬",
            factor_design_matrix.strip(),
            "",
            "### 성능 지표",
            performance_metrics.strip(),
            "",
            "### 집계 계획",
            aggregation_plan.strip(),
            "",
            "### 주요 / 보조 지표",
            outcomes.strip(),
            "",
            "### 계획 표본수",
            f"- 계획 표본수 N: {planned_n_value}",
            f"- 검정력 분석 권장 표본수: {power_plan.total_sample_size}",
            f"- 집단 / 조건별 균형 표본수: {power_plan.sample_size_per_group}",
            "",
            "### 검정력 분석",
            _power_analysis_markdown(language, power_test_family, power_effect_size, power_alpha, power_target),
            "",
            "### 분석 계획",
            analysis_plan.strip(),
            "",
            "### 실행 후 고정 절차",
            *freeze_lines,
            "",
            "### 첨부 실행 근거",
            attached_run,
            "",
            "### 일탈 로그",
            deviation_text,
        ]
        return "\n".join(sections)
    freeze_lines = [
        "1. Lock the scenario, seed strategy, outcomes, and analysis plan before interpretation.",
        f"2. Freeze fingerprint: `{freeze_fingerprint}`",
        "3. Attach the JSONL digest and summary string to the results packet before drafting claims.",
    ]
    sections = [
        "## OSF-format pre-registration",
        f"- Freeze-after-run: {'enabled' if freeze_after_run else 'optional'}",
        f"- Freeze fingerprint: `{freeze_fingerprint}`",
        "",
        "### Study title",
        title.strip(),
        "",
        "### Hypotheses / research questions",
        hypotheses.strip(),
        "",
        "### Study design",
        design.strip(),
        "",
        "### Data generation process",
        data_generation_process.strip(),
        "",
        "### Factor design matrix",
        factor_design_matrix.strip(),
        "",
        "### Performance metrics",
        performance_metrics.strip(),
        "",
        "### Aggregation plan",
        aggregation_plan.strip(),
        "",
        "### Primary / secondary outcomes",
        outcomes.strip(),
        "",
        "### Planned sample size",
        f"- Planned N: {planned_n_value}",
        f"- Recommended N from power analysis: {power_plan.total_sample_size}",
        f"- Balanced per-group / condition N: {power_plan.sample_size_per_group}",
        "",
        "### Power analysis",
        _power_analysis_markdown(language, power_test_family, power_effect_size, power_alpha, power_target),
        "",
        "### Analysis plan",
        analysis_plan.strip(),
        "",
        "### Freeze-after-run protocol",
        *freeze_lines,
        "",
        "### Attached run evidence",
        attached_run,
        "",
        "### Deviation log",
        deviation_text,
    ]
    return "\n".join(sections)


def _export_preregistration(
    summary: str,
    jsonl_text: str,
    language: str,
    title: str,
    hypotheses: str,
    design: str,
    outcomes: str,
    analysis_plan: str,
    freeze_after_run: bool,
    deviation_log: str,
    planned_n: float = 0.0,
    power_test_family: str = "independent_t",
    power_effect_size: float = 0.5,
    power_alpha: float = 0.05,
    power_target: float = 0.8,
    data_generation_process: str = "",
    factor_design_matrix: str = "",
    performance_metrics: str = "",
    aggregation_plan: str = "",
) -> tuple[str, str]:
    document = _preregistration_markdown(
        summary,
        jsonl_text,
        language,
        title,
        hypotheses,
        design,
        outcomes,
        analysis_plan,
        freeze_after_run,
        deviation_log,
        planned_n,
        power_test_family,
        power_effect_size,
        power_alpha,
        power_target,
        data_generation_process,
        factor_design_matrix,
        performance_metrics,
        aggregation_plan,
    )
    export_path = Path(tempfile.gettempdir()) / f"knoema_preregistration_{uuid.uuid4().hex}.md"
    export_path.write_text(document, encoding="utf-8")
    return document, str(export_path)


def _deposit_status_markdown(result: ZenodoDepositResult, language: str) -> str:
    key = language if language in {"ko", "en"} else _language_key(language)
    if key == "ko":
        lines = [
            f"- 모드: `{result.mode}`",
            f"- 번들: `{result.bundle_path.name}`",
            f"- API 기본 주소: `{result.api_base}`",
        ]
        if result.deposition_id is not None:
            lines.append(f"- 등록 ID: `{result.deposition_id}`")
        if result.doi:
            lines.append(f"- DOI: `{result.doi}`")
        if result.html_url:
            lines.append(f"- 링크: {result.html_url}")
        lines.append(f"- 메모: {result.message}")
        return "\n".join(lines)
    lines = [
        f"- Mode: `{result.mode}`",
        f"- Bundle: `{result.bundle_path.name}`",
        f"- API base: `{result.api_base}`",
    ]
    if result.deposition_id is not None:
        lines.append(f"- Deposition id: `{result.deposition_id}`")
    if result.doi:
        lines.append(f"- DOI: `{result.doi}`")
    if result.html_url:
        lines.append(f"- Link: {result.html_url}")
    lines.append(f"- Note: {result.message}")
    return "\n".join(lines)


def _export_deposit_bundle(
    summary: str,
    jsonl_text: str,
    preregistration_markdown: str,
    language: str,
    title: str,
    creators: str,
    description: str,
    keywords: str,
    access_token: str,
    sandbox: bool,
    publish: bool,
) -> tuple[str, str]:
    resolved_title = title.strip() or "Knoema playground run dataset"
    try:
        result = submit_zenodo_bundle(
            title=resolved_title,
            creators_text=creators,
            description=description,
            keywords_text=keywords,
            summary=summary,
            jsonl_text=jsonl_text,
            preregistration_markdown=preregistration_markdown,
            access_token=access_token,
            sandbox=sandbox,
            publish=publish,
        )
        return _deposit_status_markdown(result, language), str(result.bundle_path)
    except Exception as exc:
        fallback = submit_zenodo_bundle(
            title=resolved_title,
            creators_text=creators,
            description=description,
            keywords_text=keywords,
            summary=summary,
            jsonl_text=jsonl_text,
            preregistration_markdown=preregistration_markdown,
            access_token="",
            sandbox=sandbox,
            publish=False,
        )
        status = _deposit_status_markdown(fallback, language)
        if _language_key(language) == "ko":
            return f"{status}\n- 오류: `{escape(str(exc))}`", str(fallback.bundle_path)
        return f"{status}\n- Error: `{escape(str(exc))}`", str(fallback.bundle_path)


def _environment_freeze() -> str:
    packages: list[tuple[str, str]] = []
    for distribution in importlib_metadata.distributions():
        name = str(distribution.metadata.get("Name", "")).strip()
        version = str(getattr(distribution, "version", "")).strip()
        if name and version:
            packages.append((name, version))
    return "\n".join(
        f"{name}=={version}"
        for name, version in sorted(packages, key=lambda item: item[0].lower())
    )


def _replication_notebook(summary: str, language: str) -> str:
    title = "Knoema replication notebook" if _language_key(language) == "en" else "Knoema 재현 노트북"
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# {title}\n\n",
                    f"Summary: `{summary or 'n/a'}`\n\n",
                    "This notebook reads the bundled JSONL log and computes basic replay diagnostics.\n",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": [
                    "import json\n",
                    "from collections import Counter\n",
                    "from pathlib import Path\n\n",
                    "rows = [\n",
                    "    json.loads(line)\n",
                    "    for line in Path('../data/run.jsonl').read_text(encoding='utf-8').splitlines()\n",
                    "    if line.strip()\n",
                    "]\n",
                    "print('rows', len(rows))\n",
                    "print('record types', Counter(row.get('record_type', 'action') for row in rows))\n",
                ],
            },
            {
                "cell_type": "code",
                "metadata": {},
                "execution_count": None,
                "outputs": [],
                "source": [
                    "action_counts = Counter(\n",
                    "    row.get('action_type') or row.get('action', {}).get('action_type')\n",
                    "    for row in rows\n",
                    ")\n",
                    "action_counts.pop(None, None)\n",
                    "action_counts.most_common(10)\n",
                ],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(notebook, ensure_ascii=False, indent=2)


def _replication_source_paths() -> tuple[Path, ...]:
    root = Path(__file__).resolve().parents[1]
    candidate_paths = (
        root / "README.md",
        root / "pyproject.toml",
        root / "playground" / "app.py",
        root / "playground" / "simulation.py",
        root / "src" / "knoema" / "simulator.py",
        root / "src" / "knoema" / "memory" / "long_term.py",
        root / "src" / "knoema" / "research" / "statistics.py",
    )
    return tuple(path for path in candidate_paths if path.exists())


def _export_replication_package(
    jsonl_text: str,
    memory_snapshot: dict[str, Any],
    summary: str,
    language: str,
) -> str:
    root = Path(__file__).resolve().parents[1]
    rows = _jsonl_rows(jsonl_text)
    manifest = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "language": _language_key(language),
        "summary": summary,
        "jsonl_sha256": _digest_text(jsonl_text),
        "row_count": len(rows),
        "source_files": [
            str(path.relative_to(root)).replace("\\", "/")
            for path in _replication_source_paths()
        ],
    }
    archive_path = Path(tempfile.gettempdir()) / f"knoema_replication_package_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README.md", "# Knoema replication package\n\nUse the notebook in `notebooks/` to inspect the bundled run.\n")
        archive.writestr("data/run.jsonl", jsonl_text)
        archive.writestr("data/summary.txt", summary or "n/a")
        archive.writestr(
            "data/memory_snapshot.json",
            json.dumps(memory_snapshot, ensure_ascii=False, indent=2, sort_keys=True),
        )
        archive.writestr(
            "config/reproduction_manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        )
        archive.writestr("config/environment-freeze.txt", _environment_freeze())
        archive.writestr("notebooks/reproduce_run.ipynb", _replication_notebook(summary, language))
        for source_path in _replication_source_paths():
            archive.write(source_path, arcname=f"source/{source_path.relative_to(root)}")
    return str(archive_path)


def _export_reproducibility_certificate(
    jsonl_text: str,
    summary: str,
    language: str,
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
) -> str:
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
    )
    run_config = {
        "source": "knoema-playground",
        "scenario_name": request["scenario_name"],
        "environment_preset_id": request["environment_preset_id"],
        "cultural_prior_id": request["cultural_prior_id"],
        "provider": request["provider"],
        "provider_config": {
            "model": request["model"],
            "api_key_present": bool(str(api_key).strip()),
        },
        "seed": request["master_seed"],
        "ticks": request["ticks"],
        "agent_count": request["agent_count"],
        "batch_mode": request["batch_mode"],
        "batch_runs": request["batch_runs"],
        "language": request["language"],
        "primary_agent": {
            "name": request["primary_name"],
            "age": request["primary_age"],
        },
        "trait_vector": request["personality_overrides"],
        "agent_overrides": request["agent_overrides"],
        "primary_planning_enabled": request["primary_planning_enabled"],
        "planning_depth": request["planning_depth"],
        "event_injections_sha256": _digest_text(str(request["event_injections_text"])),
        "initial_relationships_sha256": _digest_text(str(request["initial_relationships_text"])),
    }
    certificate = generate_run_fingerprint(
        run_config=run_config,
        result=jsonl_text,
        metadata={
            "summary_sha256": _digest_text(summary),
            "language": _language_key(language),
        },
    )
    guide = verification_guide_markdown(certificate)
    archive_path = Path(tempfile.gettempdir()) / f"knoema_reproducibility_certificate_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "run_fingerprint.json",
            json.dumps(certificate, ensure_ascii=False, indent=2, sort_keys=True),
        )
        archive.writestr("VERIFY.md", guide)
        archive.writestr(
            "verification_guide.pdf",
            _simple_pdf_bytes(
                [
                    "Knoema reproducibility certificate",
                    f"Fingerprint: {certificate['fingerprint']}",
                    f"Input hash: {certificate['input_hash']}",
                    f"Output Merkle root: {certificate['output_merkle_root']}",
                    "Verify with: python scripts/knoema_verify.py run_fingerprint.json --result-jsonl run.jsonl",
                ]
            ),
        )
    return str(archive_path)


def _simple_pdf_bytes(lines: list[str]) -> bytes:
    escaped_lines = [
        line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        for line in lines
    ]
    text_commands = ["BT", "/F1 12 Tf", "72 760 Td"]
    for index, line in enumerate(escaped_lines):
        if index:
            text_commands.append("0 -18 Td")
        text_commands.append(f"({line}) Tj")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets: list[int] = []
    for index, pdf_object in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{index} 0 obj\n".encode("ascii") + pdf_object + b"\nendobj\n")
    xref_offset = sum(len(chunk) for chunk in chunks)
    xref = [b"xref\n0 6\n", b"0000000000 65535 f \n"]
    xref.extend(f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets)
    chunks.extend(
        [
            *xref,
            b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n",
            str(xref_offset).encode("ascii"),
            b"\n%%EOF\n",
        ]
    )
    return b"".join(chunks)


def _export_html_report(
    timeline_markdown: str,
    graph_figure: Any,
    jsonl_text: str,
    summary: str,
    language: str,
) -> str:
    language_key = _language_key(language)
    labels = LABELS[language_key]
    if isinstance(graph_figure, str) and graph_figure.strip().startswith("<"):
        graph_html = graph_figure
    else:
        figure = _coerce_plotly_figure(graph_figure)
        graph_html = figure.to_html(
            full_html=False,
            include_plotlyjs=True,
            config={"displayModeBar": False, "responsive": True},
        )
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    document = f"""<!DOCTYPE html>
<html lang="{language_key}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(labels["html_report_title"])}</title>
  <style>
    :root {{
      color-scheme: light dark;
      font-family: Inter, Segoe UI, Arial, sans-serif;
    }}
    body {{
      margin: 0;
      background: #0f172a;
      color: #e2e8f0;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px;
    }}
    h1, h2 {{
      margin: 0 0 12px;
    }}
    .summary {{
      margin: 0 0 20px;
      padding: 16px;
      border: 1px solid rgba(148, 163, 184, 0.35);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.72);
    }}
    .meta {{
      margin: 0 0 24px;
      color: #cbd5e1;
      font-size: 14px;
    }}
    section {{
      margin: 0 0 20px;
      padding: 16px;
      border: 1px solid rgba(148, 163, 184, 0.35);
      border-radius: 8px;
      background: rgba(15, 23, 42, 0.72);
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      font-size: 13px;
      line-height: 1.5;
    }}
    .empty {{
      margin: 0;
      color: #cbd5e1;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{escape(labels["html_report_title"])}</h1>
    <p class="meta">{escape(labels["generated_at"])}: {escape(generated_at)}</p>
    <div class="summary">{escape(summary)}</div>
    <section>
      <h2>{escape(labels["graph"])}</h2>
      {graph_html}
    </section>
    {_report_section(labels["timeline"], timeline_markdown, language=language_key)}
    {_report_section(labels["jsonl"], jsonl_text, language=language_key)}
  </main>
</body>
</html>
"""
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".html",
        prefix="knoema_playground_report_",
        delete=False,
    ) as handle:
        handle.write(document)
        return handle.name


def _write_csv_table(
    destination: Path,
    *,
    fieldnames: list[str],
    rows: list[dict[str, object]],
) -> None:
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _single_run_export_tables(
    jsonl_text: str,
    memory_snapshot: dict[str, Any],
) -> dict[str, tuple[list[str], list[dict[str, object]]]]:
    rows = [
        row
        for row in _jsonl_rows(jsonl_text)
        if "tick" in row and isinstance(row.get("action"), dict)
    ]
    agent_buckets: dict[str, list[dict[str, Any]]] = {}
    action_count_rows: list[dict[str, object]] = []
    edge_buckets: dict[tuple[str, str], dict[str, object]] = {}
    action_counts: Counter[tuple[str, str]] = Counter()

    for row in rows:
        agent_id = str(row.get("agent_id", "agent"))
        action = cast("dict[str, Any]", row.get("action", {}))
        action_type = str(action.get("action_type", "observe")).strip() or "observe"
        tick = int(row.get("tick", 0))
        agent_buckets.setdefault(agent_id, []).append(row)
        action_counts[(agent_id, action_type)] += 1
        target = str(action.get("target") or "").strip()
        if target:
            bucket = edge_buckets.setdefault(
                (agent_id, target),
                {
                    "source": agent_id,
                    "target": target,
                    "edge_weight": 0,
                    "first_tick": tick,
                    "last_tick": tick,
                    "action_counts": Counter(),
                },
            )
            bucket["edge_weight"] = int(bucket["edge_weight"]) + 1
            bucket["first_tick"] = min(int(bucket["first_tick"]), tick)
            bucket["last_tick"] = max(int(bucket["last_tick"]), tick)
            cast("Counter[str]", bucket["action_counts"])[action_type] += 1

    for (agent_id, action_type), count in sorted(action_counts.items()):
        action_count_rows.append(
            {
                "agent_id": agent_id,
                "action_type": action_type,
                "count": count,
            }
        )

    per_agent_rows: list[dict[str, object]] = []
    for agent_id in sorted(agent_buckets):
        agent_rows = agent_buckets[agent_id]
        per_agent_counter = Counter(
            str(cast("dict[str, Any]", row.get("action", {})).get("action_type", "observe"))
            for row in agent_rows
        )
        unique_targets = {
            str(cast("dict[str, Any]", row.get("action", {})).get("target") or "").strip()
            for row in agent_rows
            if str(cast("dict[str, Any]", row.get("action", {})).get("target") or "").strip()
        }
        emotion_rows = list(dict(memory_snapshot.get(agent_id, {})).get("emotion", []))
        valences = [float(entry.get("valence", 0.0)) for entry in emotion_rows]
        per_agent_rows.append(
            {
                "agent_id": agent_id,
                "total_actions": len(agent_rows),
                "unique_targets": len(unique_targets),
                "top_action_type": per_agent_counter.most_common(1)[0][0] if per_agent_counter else "n/a",
                "first_tick": min(int(row.get("tick", 0)) for row in agent_rows),
                "last_tick": max(int(row.get("tick", 0)) for row in agent_rows),
                "mean_valence": round(_mean(valences), 4) if valences else 0.0,
                "last_valence": round(valences[-1], 4) if valences else 0.0,
            }
        )

    edge_rows: list[dict[str, object]] = []
    for (source, target), bucket in sorted(edge_buckets.items()):
        counter = cast("Counter[str]", bucket["action_counts"])
        edge_rows.append(
            {
                "source": source,
                "target": target,
                "edge_weight": int(bucket["edge_weight"]),
                "top_action_type": counter.most_common(1)[0][0] if counter else "n/a",
                "first_tick": int(bucket["first_tick"]),
                "last_tick": int(bucket["last_tick"]),
            }
        )

    emotion_rows: list[dict[str, object]] = []
    for agent_id in sorted(memory_snapshot):
        for entry in list(dict(memory_snapshot.get(agent_id, {})).get("emotion", [])):
            emotion_rows.append(
                {
                    "agent_id": agent_id,
                    "tick": int(entry.get("tick", -1)),
                    "valence": float(entry.get("valence", 0.0)),
                    "arousal": float(entry.get("arousal", 0.0)),
                    "dominance": float(entry.get("dominance", 0.0)),
                    "timestamp": str(entry.get("timestamp", "")),
                }
            )

    return {
        "per_agent_stats.csv": (
            [
                "agent_id",
                "total_actions",
                "unique_targets",
                "top_action_type",
                "first_tick",
                "last_tick",
                "mean_valence",
                "last_valence",
            ],
            per_agent_rows,
        ),
        "edge_weights.csv": (
            ["source", "target", "edge_weight", "top_action_type", "first_tick", "last_tick"],
            edge_rows,
        ),
        "action_counts.csv": (
            ["agent_id", "action_type", "count"],
            action_count_rows,
        ),
        "emotion_trajectories.csv": (
            ["agent_id", "tick", "valence", "arousal", "dominance", "timestamp"],
            emotion_rows,
        ),
    }


def _batch_export_tables(
    jsonl_text: str,
) -> dict[str, tuple[list[str], list[dict[str, object]]]]:
    rows = _jsonl_rows(jsonl_text)
    tick_rows = [
        row
        for row in rows
        if str(row.get("record_type", "")) == "tick_stat"
    ]
    agent_rows = [
        row
        for row in rows
        if str(row.get("record_type", "")) == "agent_stat"
    ]
    per_agent_rows = [
        {
            "agent_id": str(row.get("agent_id", "agent")),
            "mean_actions": float(row.get("mean_actions", 0.0)),
            "top_action_type": str(row.get("top_action_type", "n/a")),
        }
        for row in agent_rows
    ]
    action_count_rows: list[dict[str, object]] = []
    tick_stat_rows: list[dict[str, object]] = []
    for row in tick_rows:
        tick = int(row.get("tick", -1))
        tick_stat_rows.append(
            {
                "tick": tick,
                "mean_actions": float(row.get("mean_actions", 0.0)),
                "top_action_type": str(row.get("top_action_type", "n/a")),
            }
        )
        action_counts = row.get("action_type_counts", {})
        if not isinstance(action_counts, dict):
            continue
        for action_type, count in sorted(action_counts.items()):
            action_count_rows.append(
                {
                    "tick": tick,
                    "action_type": str(action_type),
                    "count": int(count),
                }
            )

    return {
        "per_agent_stats.csv": (
            ["agent_id", "mean_actions", "top_action_type"],
            per_agent_rows,
        ),
        "edge_weights.csv": (
            ["source", "target", "edge_weight", "top_action_type", "first_tick", "last_tick"],
            [],
        ),
        "action_counts.csv": (
            ["tick", "action_type", "count"],
            action_count_rows,
        ),
        "emotion_trajectories.csv": (
            ["agent_id", "tick", "valence", "arousal", "dominance", "timestamp"],
            [],
        ),
        "tick_stats.csv": (
            ["tick", "mean_actions", "top_action_type"],
            tick_stat_rows,
        ),
    }


def _export_csv_bundle(
    jsonl_text: str,
    memory_snapshot: dict[str, Any],
    summary: str,
    language: str,
) -> str:
    del language
    rows = _jsonl_rows(jsonl_text)
    tables = (
        _batch_export_tables(jsonl_text)
        if any("record_type" in row for row in rows)
        else _single_run_export_tables(jsonl_text, memory_snapshot)
    )
    with tempfile.TemporaryDirectory(prefix="knoema_playground_csv_") as directory:
        directory_path = Path(directory)
        (directory_path / "run_summary.txt").write_text(str(summary), encoding="utf-8")
        for filename, (fieldnames, table_rows) in tables.items():
            _write_csv_table(
                directory_path / filename,
                fieldnames=fieldnames,
                rows=table_rows,
            )
        with tempfile.NamedTemporaryFile(
            suffix=".zip",
            prefix="knoema_playground_csv_bundle_",
            delete=False,
        ) as handle:
            archive_path = Path(handle.name)
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(directory_path.iterdir()):
                archive.write(file_path, arcname=file_path.name)
        return str(archive_path)


def _finetuning_format_choices(language: str) -> list[tuple[str, str]]:
    key = _language_key(language)
    if key == "ko":
        return [
            ("OpenAI 채팅 JSONL", "openai"),
            ("Anthropic 채팅 JSONL", "anthropic"),
            ("DPO 선호쌍 JSONL", "dpo"),
        ]
    return [
        ("OpenAI chat JSONL", "openai"),
        ("Anthropic chat JSONL", "anthropic"),
        ("DPO preference pairs JSONL", "dpo"),
    ]


def _export_finetuning_dataset(
    jsonl_text: str,
    export_format: str,
    language: str,
) -> str:
    del language
    raw_format = str(export_format or "openai").strip()
    dataset_text = export_finetuning_jsonl(jsonl_text, raw_format)
    format_slug = raw_format.lower().replace(" ", "_").replace("-", "_")
    export_path = Path(tempfile.gettempdir()) / f"knoema_finetuning_{format_slug}_{uuid.uuid4().hex}.jsonl"
    export_path.write_text(dataset_text, encoding="utf-8")
    return str(export_path)


def _latex_escape(text: object) -> str:
    escaped = str(text)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    for source, target in replacements.items():
        escaped = escaped.replace(source, target)
    return escaped


def _export_latex_table(
    jsonl_text: str,
    memory_snapshot: dict[str, Any],
    summary: str,
    language: str,
) -> str:
    key = _language_key(language)
    rows = _jsonl_rows(jsonl_text)
    batch_mode = any("record_type" in row for row in rows)
    tables = (
        _batch_export_tables(jsonl_text)
        if batch_mode
        else _single_run_export_tables(jsonl_text, memory_snapshot)
    )
    per_agent_fieldnames, per_agent_rows = tables["per_agent_stats.csv"]
    if batch_mode:
        headers = ["Agent", "Mean Actions", "Top Action"]
        column_spec = "lrl"
        body_rows = [
            (
                _latex_escape(row["agent_id"]),
                _latex_escape(row["mean_actions"]),
                _latex_escape(row["top_action_type"]),
            )
            for row in per_agent_rows[:8]
        ]
        caption = (
            "배치 실행 에이전트 요약"
            if key == "ko"
            else "Batch per-agent summary"
        )
    else:
        del per_agent_fieldnames
        headers = ["Agent", "Total Actions", "Unique Targets", "Top Action"]
        column_spec = "lrrl"
        body_rows = [
            (
                _latex_escape(row["agent_id"]),
                _latex_escape(row["total_actions"]),
                _latex_escape(row["unique_targets"]),
                _latex_escape(row["top_action_type"]),
            )
            for row in per_agent_rows[:8]
        ]
        caption = (
            "단일 실행 에이전트 요약"
            if key == "ko"
            else "Single-run per-agent summary"
        )

    if not body_rows:
        body_rows = [(r"\multicolumn{4}{c}{No data available.}",)] if not batch_mode else [(r"\multicolumn{3}{c}{No data available.}",)]

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        rf"\caption{{{_latex_escape(caption)}}}",
        rf"\begin{{tabular}}{{{column_spec}}}",
        r"\hline",
        " & ".join(headers) + r" \\",
        r"\hline",
    ]
    for row in body_rows:
        lines.append(" & ".join(row) + r" \\")
    lines.extend(
        [
            r"\hline",
            r"\end{tabular}",
            r"\label{tab:knoema_playground_export}",
            r"\end{table}",
            "",
            "% Run summary",
            f"% {_latex_escape(summary)}",
        ]
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".tex",
        prefix="knoema_playground_table_",
        delete=False,
    ) as handle:
        handle.write("\n".join(lines))
        return handle.name


def _seed_relationship_draft(suggestions: tuple[dict[str, Any], ...]) -> str:
    lines: list[str] = []
    for left_index in range(len(suggestions)):
        for right_index in range(left_index + 1, len(suggestions)):
            left = suggestions[left_index]
            right = suggestions[right_index]
            left_personality = dict(left.get("personality", {}))
            right_personality = dict(right.get("personality", {}))
            trust = round(
                (
                    float(left_personality.get("agreeableness", 0.5))
                    + float(right_personality.get("agreeableness", 0.5))
                    + float(left_personality.get("honesty_humility", 0.5))
                    + float(right_personality.get("honesty_humility", 0.5))
                )
                / 4.0,
                2,
            )
            weight = round(
                (
                    float(left_personality.get("extraversion", 0.5))
                    + float(right_personality.get("extraversion", 0.5))
                )
                / 2.0,
                2,
            )
            familiarity = round(0.2 + ((left_index + right_index) * 0.08), 2)
            relationship_type = "friend" if trust >= 0.65 else "colleague"
            source_id = f"agent_{left_index + 1}"
            target_id = f"agent_{right_index + 1}"
            lines.append(
                f"{source_id} | {target_id} | {relationship_type} | {weight:.2f} | {trust:.2f} | {familiarity:.2f}"
            )
            lines.append(
                f"{target_id} | {source_id} | {relationship_type} | {weight:.2f} | {trust:.2f} | {familiarity:.2f}"
            )
    return "\n".join(lines)


def _seed_prompt_summary(seed_prompt: str, suggestions: tuple[dict[str, Any], ...], language: str) -> str:
    if not suggestions:
        return LABELS[_language_key(language)]["seed_prompt_empty"]
    if _language_key(language) == "ko":
        lines = ["### 시드 결과", f"- 프롬프트: {seed_prompt.strip()}"]
        for index, suggestion in enumerate(suggestions, start=1):
            lines.append(
                f"- agent_{index}: {suggestion['name']} ({suggestion['age']}) / {suggestion['preset_label']}"
            )
        return "\n".join(lines)
    lines = ["### Seed output", f"- Prompt: {seed_prompt.strip()}"]
    for index, suggestion in enumerate(suggestions, start=1):
        lines.append(
            f"- agent_{index}: {suggestion['name']} ({suggestion['age']}) / {suggestion['preset_label']}"
        )
    return "\n".join(lines)


def _seed_prompt_updates(seed_prompt: str, language: str) -> tuple[Any, ...]:
    suggestions = seed_persona_suggestions(seed_prompt, language=_language_key(language))
    outputs: list[Any] = []
    if not suggestions:
        empty_updates = (3 + len(PERSONA_TRAIT_FIELDS)) * AGENT_EDITOR_SLOT_COUNT
        outputs.extend(gr.update() for _ in range(empty_updates))
        outputs.append(gr.update())
        outputs.append(LABELS[_language_key(language)]["seed_prompt_empty"])
        return tuple(outputs)
    for suggestion in suggestions:
        outputs.extend(
            [
                gr.update(value=suggestion["name"]),
                gr.update(value=int(suggestion["age"])),
                gr.update(value=suggestion["preset_id"]),
            ]
        )
        outputs.extend(
            gr.update(value=float(suggestion["personality"][field_name]))
            for field_name in PERSONA_TRAIT_FIELDS
        )
    outputs.append(gr.update(value=_seed_relationship_draft(suggestions)))
    outputs.append(_seed_prompt_summary(seed_prompt, suggestions, language))
    return tuple(outputs)


def _scenario_synthesis_updates(description: str, language: str) -> tuple[Any, ...]:
    output_count = 1 + ((3 + len(PERSONA_TRAIT_FIELDS)) * AGENT_EDITOR_SLOT_COUNT) + 3
    key = _language_key(language)
    if not str(description).strip():
        return tuple(
            [gr.update() for _ in range(output_count - 1)]
            + [gr.update(value=LABELS[key]["scenario_synthesis_empty"])]
        )
    try:
        config = synthesize_scenario(str(description), key)
    except ScenarioSynthesisError as exc:
        message = (
            f"생성 실패: {exc}"
            if key == "ko"
            else f"Generation failed: {exc}"
        )
        return tuple([gr.update() for _ in range(output_count - 1)] + [gr.update(value=message)])

    agents = list(config.get("agents", []))
    outputs: list[Any] = [gr.update(value=len(agents))]
    for slot_index in range(AGENT_EDITOR_SLOT_COUNT):
        if slot_index < len(agents):
            agent = cast("dict[str, Any]", agents[slot_index])
            personality = cast("dict[str, Any]", agent.get("personality", {}))
            outputs.extend(
                [
                    gr.update(value=str(agent.get("name", f"Agent {slot_index + 1}"))),
                    gr.update(value=int(agent.get("age", 30))),
                    gr.update(value=""),
                ]
            )
            outputs.extend(
                gr.update(value=float(personality.get(field_name, PERSONA_TRAIT_DEFAULTS[field_name])))
                for field_name in PERSONA_TRAIT_FIELDS
            )
        else:
            outputs.extend(gr.update() for _ in range(3 + len(PERSONA_TRAIT_FIELDS)))
    outputs.append(gr.update(value=_scenario_synthesis_event_lines(config)))
    outputs.append(gr.update(value=_scenario_synthesis_relationship_lines(agents[:3])))
    outputs.append(gr.update(value=_scenario_synthesis_preview(config, key)))
    return tuple(outputs)


def _community_scenario_updates(scenario_id: str, language: str) -> tuple[Any, ...]:
    output_count = 1 + ((3 + len(PERSONA_TRAIT_FIELDS)) * AGENT_EDITOR_SLOT_COUNT) + 3
    key = _language_key(language)
    try:
        scenario = community_scenario_by_id(str(scenario_id))
        payload = yaml.safe_load(scenario.yaml_text)
    except Exception as exc:
        message = (
            f"불러오기 실패: {exc}"
            if key == "ko"
            else f"Load failed: {exc}"
        )
        return tuple([gr.update() for _ in range(output_count - 1)] + [gr.update(value=message)])
    if not isinstance(payload, dict):
        return tuple(
            [gr.update() for _ in range(output_count - 1)]
            + [gr.update(value=LABELS[key]["community_gallery_empty"])]
        )
    agents = list(cast("list[dict[str, Any]]", payload.get("agents", [])))
    outputs: list[Any] = [gr.update(value=len(agents))]
    for slot_index in range(AGENT_EDITOR_SLOT_COUNT):
        if slot_index < len(agents):
            agent = agents[slot_index]
            personality = cast("dict[str, Any]", agent.get("personality", {}))
            outputs.extend(
                [
                    gr.update(value=str(agent.get("name", f"Agent {slot_index + 1}"))),
                    gr.update(value=int(agent.get("age", 30))),
                    gr.update(value=""),
                ]
            )
            outputs.extend(
                gr.update(value=float(personality.get(field_name, PERSONA_TRAIT_DEFAULTS[field_name])))
                for field_name in PERSONA_TRAIT_FIELDS
            )
        else:
            outputs.extend(gr.update() for _ in range(3 + len(PERSONA_TRAIT_FIELDS)))
    outputs.append(gr.update(value=_scenario_synthesis_event_lines(payload)))
    outputs.append(gr.update(value=_scenario_synthesis_relationship_lines(agents[:3])))
    outputs.append(gr.update(value=community_gallery_markdown(scenario.scenario_id, key)))
    return tuple(outputs)


def _scenario_synthesis_event_lines(config: dict[str, Any]) -> str:
    lines: list[str] = []
    for event in cast("list[dict[str, Any]]", config.get("events", [])):
        participants = ",".join(str(participant) for participant in event.get("participants", []))
        lines.append(
            " | ".join(
                [
                    "0",
                    str(event.get("location", "Generated Location")),
                    str(event.get("description", "")),
                    participants,
                    str(event.get("event_type", "scenario.trigger")),
                ]
            )
        )
    return "\n".join(lines)


def _scenario_synthesis_relationship_lines(agents: list[Any]) -> str:
    agent_ids = [str(cast("dict[str, Any]", agent).get("agent_id", f"agent_{index + 1}")) for index, agent in enumerate(agents)]
    lines: list[str] = []
    for left_index, left_id in enumerate(agent_ids):
        for right_id in agent_ids[left_index + 1 :]:
            lines.append(f"{left_id} | {right_id} | generated_peer | 0.50 | 0.55 | 0.20")
            lines.append(f"{right_id} | {left_id} | generated_peer | 0.50 | 0.55 | 0.20")
    return "\n".join(lines)


def _scenario_synthesis_preview(config: dict[str, Any], language: str) -> str:
    title = "생성된 시나리오 YAML" if language == "ko" else "Synthesized scenario YAML"
    yaml_text = scenario_to_yaml(config)
    return f"### {title}\n\n```yaml\n{yaml_text}```"


def _jsonl_rows(jsonl_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _flatten_action_counts(action_breakdown: dict[str, dict[str, int]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for actions in action_breakdown.values():
        for action_type, count in actions.items():
            counts[str(action_type)] += int(count)
    return counts


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _sample_variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_value = _mean(values)
    return sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)


def _format_stat(value: float, *, digits: int = 3) -> str:
    if math.isnan(value):
        return "n/a"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    return f"{value:.{digits}f}"


def _format_p_value(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def _cohens_d(left: list[float], right: list[float]) -> float:
    if len(left) < 2 or len(right) < 2:
        return math.nan
    left_variance = _sample_variance(left)
    right_variance = _sample_variance(right)
    pooled_numerator = ((len(left) - 1) * left_variance) + ((len(right) - 1) * right_variance)
    pooled_denominator = len(left) + len(right) - 2
    if pooled_denominator <= 0:
        return math.nan
    pooled_variance = pooled_numerator / pooled_denominator
    if pooled_variance <= 0:
        return 0.0
    return (_mean(right) - _mean(left)) / math.sqrt(pooled_variance)


def _cliffs_delta(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return math.nan
    greater = 0
    lower = 0
    for left_value in left:
        for right_value in right:
            if right_value > left_value:
                greater += 1
            elif right_value < left_value:
                lower += 1
    return (greater - lower) / (len(left) * len(right))


def _mean_difference_ci(left: list[float], right: list[float]) -> tuple[float, float, float]:
    mean_diff = _mean(right) - _mean(left)
    if len(left) < 2 or len(right) < 2:
        return mean_diff, math.nan, math.nan
    left_variance = _sample_variance(left)
    right_variance = _sample_variance(right)
    left_term = left_variance / len(left)
    right_term = right_variance / len(right)
    standard_error = math.sqrt(left_term + right_term)
    if standard_error == 0:
        return mean_diff, mean_diff, mean_diff
    denominator = 0.0
    if len(left) > 1 and left_term > 0:
        denominator += (left_term * left_term) / (len(left) - 1)
    if len(right) > 1 and right_term > 0:
        denominator += (right_term * right_term) / (len(right) - 1)
    if denominator == 0:
        return mean_diff, math.nan, math.nan
    degrees_of_freedom = ((left_term + right_term) ** 2) / denominator
    critical = float(student_t.ppf(0.975, degrees_of_freedom))
    margin = critical * standard_error
    return mean_diff, mean_diff - margin, mean_diff + margin


def _holm_correct(p_values: dict[str, float]) -> dict[str, float]:
    adjusted = dict.fromkeys(p_values, math.nan)
    ordered = sorted(
        ((name, value) for name, value in p_values.items() if not math.isnan(value)),
        key=lambda item: item[1],
    )
    running_max = 0.0
    total = len(ordered)
    for index, (name, value) in enumerate(ordered):
        candidate = min(1.0, (total - index) * value)
        running_max = max(running_max, candidate)
        adjusted[name] = running_max
    return adjusted


def _aggregate_batch_action_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        action_counts = row.get("action_type_counts", {})
        if not isinstance(action_counts, dict):
            continue
        for action_type, count in action_counts.items():
            counts[str(action_type)] += int(count)
    return counts


def _dominant_action_label(counts: Counter[str]) -> str:
    if not counts:
        return "n/a"
    action_type, count = counts.most_common(1)[0]
    return f"{action_type} ({count})"


def _advanced_statistics_lines(rows: list[dict[str, Any]], language: str) -> list[str]:
    advanced_summary = summarize_seed_tick_effect(rows)
    if advanced_summary is None:
        return []
    if language == "ko":
        return [
            (
                f"- Mixed effects (seed random intercept, late-phase fixed effect): "
                f"beta={_format_stat(advanced_summary.fixed_effect)} | "
                f"intercept={_format_stat(advanced_summary.intercept)} | "
                f"random SD={_format_stat(advanced_summary.random_intercept_sd)} | "
                f"p={_format_p_value(advanced_summary.p_value)} | "
                f"backend={advanced_summary.backend}"
            ),
            (
                f"- Bayesian posterior (late-early cooperative rate): "
                f"mean={_format_stat(advanced_summary.posterior_mean)} | "
                f"95% CrI [{_format_stat(advanced_summary.credible_interval_low)}, "
                f"{_format_stat(advanced_summary.credible_interval_high)}] | "
                f"P(delta>0)={_format_stat(advanced_summary.probability_positive)}"
            ),
        ]
    return [
        (
            f"- Mixed effects (seed random intercept, late-phase fixed effect): "
            f"beta={_format_stat(advanced_summary.fixed_effect)} | "
            f"intercept={_format_stat(advanced_summary.intercept)} | "
            f"random SD={_format_stat(advanced_summary.random_intercept_sd)} | "
            f"p={_format_p_value(advanced_summary.p_value)} | "
            f"backend={advanced_summary.backend}"
        ),
        (
            f"- Bayesian posterior (late-early cooperative rate): "
            f"mean={_format_stat(advanced_summary.posterior_mean)} | "
            f"95% CrI [{_format_stat(advanced_summary.credible_interval_low)}, "
            f"{_format_stat(advanced_summary.credible_interval_high)}] | "
            f"P(delta > 0)={_format_stat(advanced_summary.probability_positive)}"
        ),
    ]


def _statistical_analysis_markdown(jsonl_text: str, language: str) -> str:
    key = _language_key(language)
    rows = _jsonl_rows(jsonl_text)
    batch_summary = next(
        (
            row
            for row in rows
            if str(row.get("record_type", "")) == "batch_summary"
        ),
        None,
    )
    tick_rows = sorted(
        (
            row
            for row in rows
            if str(row.get("record_type", "")) == "tick_stat"
        ),
        key=lambda row: int(row.get("tick", 0)),
    )
    if batch_summary is None or not tick_rows:
        return LABELS[key]["statistics_batch_only"]
    if len(tick_rows) < 4:
        return LABELS[key]["statistics_insufficient"]

    split_index = len(tick_rows) // 2
    early_rows = tick_rows[:split_index]
    late_rows = tick_rows[split_index:]
    if not early_rows or not late_rows:
        return LABELS[key]["statistics_insufficient"]

    early_actions = [float(row.get("mean_actions", 0.0)) for row in early_rows]
    late_actions = [float(row.get("mean_actions", 0.0)) for row in late_rows]
    early_counts = _aggregate_batch_action_counts(early_rows)
    late_counts = _aggregate_batch_action_counts(late_rows)
    action_types = sorted(set(early_counts) | set(late_counts))
    chi_square = math.nan
    chi_square_p = math.nan
    cramers_v = math.nan
    degrees_of_freedom = 0
    if len(action_types) >= 2:
        contingency = [
            [int(early_counts.get(action_type, 0)) for action_type in action_types],
            [int(late_counts.get(action_type, 0)) for action_type in action_types],
        ]
        if sum(contingency[0]) > 0 and sum(contingency[1]) > 0:
            chi_square_result = chi2_contingency(contingency, correction=False)
            chi_square = float(chi_square_result[0])
            chi_square_p = float(chi_square_result[1])
            degrees_of_freedom = int(chi_square_result[2])
            total = float(sum(contingency[0]) + sum(contingency[1]))
            if total > 0:
                cramers_v = math.sqrt(chi_square / total)

    mann_whitney = mannwhitneyu(early_actions, late_actions, alternative="two-sided")
    mann_whitney_u = float(mann_whitney.statistic)
    mann_whitney_p = float(mann_whitney.pvalue)
    cohen_d = _cohens_d(early_actions, late_actions)
    cliffs_delta = _cliffs_delta(early_actions, late_actions)
    mean_diff, ci_low, ci_high = _mean_difference_ci(early_actions, late_actions)
    corrected = _holm_correct(
        {
            "mann_whitney": mann_whitney_p,
            "chi_square": chi_square_p,
        }
    )
    agent_rows = [
        row
        for row in rows
        if str(row.get("record_type", "")) == "agent_stat"
    ]
    advanced_lines = _advanced_statistics_lines(rows, key)
    busiest_agent = max(
        agent_rows,
        key=lambda row: float(row.get("mean_actions", 0.0)),
        default=None,
    )
    early_tick_range = f"{int(early_rows[0]['tick'])}-{int(early_rows[-1]['tick'])}"
    late_tick_range = f"{int(late_rows[0]['tick'])}-{int(late_rows[-1]['tick'])}"
    batch_size = int(batch_summary.get("batch_size", 0))
    master_seed = int(batch_summary.get("master_seed", 0))
    reproducibility = float(batch_summary.get("reproducibility_coefficient", 0.0))

    if key == "ko":
        busiest_line = "없음"
        if busiest_agent is not None:
            busiest_line = (
                f"{busiest_agent.get('agent_id', 'agent_1')!s} "
                f"(평균 행동 {float(busiest_agent.get('mean_actions', 0.0)):.2f})"
            )
        return "\n".join(
            [
                "### 통계 분석",
                (
                    f"- 배치 반복 {batch_size}회 | master seed {master_seed} | "
                    f"재현성 {reproducibility:.3f}"
                ),
                f"- 비교 구간: 초기 tick {early_tick_range} vs 후기 tick {late_tick_range}",
                (
                    f"- Mann-Whitney U (tick당 평균 행동): U={_format_stat(mann_whitney_u)} | "
                    f"p={_format_p_value(mann_whitney_p)} | Holm p={_format_p_value(corrected['mann_whitney'])}"
                ),
                f"- Cohen's d={_format_stat(cohen_d)} | Cliff's delta={_format_stat(cliffs_delta)}",
                (
                    f"- 평균 차이 (후기-초기)={_format_stat(mean_diff)} | "
                    f"95% CI [{_format_stat(ci_low)}, {_format_stat(ci_high)}]"
                ),
                (
                    f"- chi-square (행동 분포 이동): chi2={_format_stat(chi_square)} | "
                    f"dof={degrees_of_freedom} | p={_format_p_value(chi_square_p)} | "
                    f"Holm p={_format_p_value(corrected['chi_square'])}"
                ),
                f"- Cramer's V={_format_stat(cramers_v)}",
                (
                    f"- 주요 행동 변화: {_dominant_action_label(early_counts)} -> "
                    f"{_dominant_action_label(late_counts)}"
                ),
                f"- 최고 활동 에이전트: {busiest_line}",
                "- 다중비교 보정: Holm step-down (2 tests)",
            ]
        )

    busiest_line = "n/a"
    if busiest_agent is not None:
        busiest_line = (
            f"{busiest_agent.get('agent_id', 'agent_1')!s} "
            f"(mean actions {float(busiest_agent.get('mean_actions', 0.0)):.2f})"
        )
    return "\n".join(
        [
            "### Statistical analysis",
            (
                f"- Batch runs: {batch_size} | Master seed: {master_seed} | "
                f"Reproducibility: {reproducibility:.3f}"
            ),
            f"- Comparison window: early ticks {early_tick_range} vs late ticks {late_tick_range}",
            (
                f"- Mann-Whitney U (mean actions per tick): U={_format_stat(mann_whitney_u)} | "
                f"p={_format_p_value(mann_whitney_p)} | Holm p={_format_p_value(corrected['mann_whitney'])}"
            ),
            f"- Cohen's d={_format_stat(cohen_d)} | Cliff's delta={_format_stat(cliffs_delta)}",
            (
                f"- Mean difference (late-early)={_format_stat(mean_diff)} | "
                f"95% CI [{_format_stat(ci_low)}, {_format_stat(ci_high)}]"
            ),
            (
                f"- chi-square (action-type shift): chi2={_format_stat(chi_square)} | "
                f"dof={degrees_of_freedom} | p={_format_p_value(chi_square_p)} | "
                f"Holm p={_format_p_value(corrected['chi_square'])}"
            ),
            f"- Cramer's V={_format_stat(cramers_v)}",
            (
                f"- Dominant action shift: {_dominant_action_label(early_counts)} -> "
                f"{_dominant_action_label(late_counts)}"
            ),
            f"- Highest-activity agent: {busiest_line}",
            "- Multiple-comparison correction: Holm step-down (2 tests)",
            *advanced_lines,
        ]
    )


def _report_agent_answer(question: str, jsonl_text: str, summary: str, language: str) -> str:
    rows = _jsonl_rows(jsonl_text)
    key = _language_key(language)
    if not rows:
        return LABELS[key]["report_agent_empty"]
    question_text = question.strip() or ("이번 런에서 핵심은 무엇인가?" if key == "ko" else "What mattered most in this run?")
    agent_counts = Counter(str(row.get("agent_id", "")) for row in rows)
    action_counts = Counter(
        str(dict(row.get("action", {})).get("action_type", ""))
        for row in rows
        if dict(row.get("action", {})).get("action_type")
    )
    directed_count = sum(1 for row in rows if dict(row.get("action", {})).get("target"))
    top_agent, top_agent_count = agent_counts.most_common(1)[0]
    top_action, top_action_count = action_counts.most_common(1)[0]
    latest_tick = max(int(row.get("tick", 0)) for row in rows)
    if key == "ko":
        return "\n".join(
            [
                "### ReportAgent 응답",
                f"- 질문: {question_text}",
                f"- 실행 요약: {summary}",
                f"- 가장 많이 움직인 에이전트: {top_agent} ({top_agent_count}회)",
                f"- 지배적 액션: {top_action} ({top_action_count}회)",
                f"- 지시형 상호작용 수: {directed_count}",
                f"- 마지막 틱: {latest_tick}",
            ]
        )
    return "\n".join(
        [
            "### ReportAgent answer",
            f"- Question: {question_text}",
            f"- Run summary: {summary}",
            f"- Most active agent: {top_agent} ({top_agent_count} actions)",
            f"- Dominant action: {top_action} ({top_action_count})",
            f"- Directed interactions: {directed_count}",
            f"- Final tick observed: {latest_tick}",
        ]
    )


def _memory_items(memory_snapshot: dict[str, Any], agent_id: str, key: str) -> list[str]:
    bucket = dict(memory_snapshot.get(agent_id, {}))
    values = bucket.get(key, [])
    if not isinstance(values, list):
        return []
    items: list[str] = []
    for entry in values:
        if isinstance(entry, dict):
            content = str(entry.get("content", "")).strip()
            if content:
                items.append(content)
    return items


def _interview_agent_answer(
    agent_id: str,
    question: str,
    jsonl_text: str,
    memory_snapshot: dict[str, Any],
    language: str,
) -> str:
    key = _language_key(language)
    resolved_agent_id = agent_id.strip()
    if not resolved_agent_id:
        return LABELS[key]["interview_empty"]
    rows = [row for row in _jsonl_rows(jsonl_text) if str(row.get("agent_id", "")) == resolved_agent_id]
    if not rows and resolved_agent_id not in memory_snapshot:
        return LABELS[key]["interview_empty"]
    question_text = question.strip() or ("지금 무엇을 우선시하고 있나?" if key == "ko" else "What are you prioritizing right now?")
    recent_actions = [
        f"{dict(row.get('action', {})).get('action_type', 'act')}: {dict(row.get('action', {})).get('content', '')}"
        for row in rows[-3:]
    ]
    short_term = _memory_items(memory_snapshot, resolved_agent_id, "short_term")[:2]
    long_term = _memory_items(memory_snapshot, resolved_agent_id, "long_term")[:2]
    monologues = _memory_items(memory_snapshot, resolved_agent_id, "monologue")[:1]
    if key == "ko":
        return "\n".join(
            [
                f"### 인터뷰: {resolved_agent_id}",
                f"- 질문: {question_text}",
                f"- 최근 행동: {' / '.join(recent_actions) if recent_actions else '없음'}",
                f"- 단기 기억: {' / '.join(short_term) if short_term else '없음'}",
                f"- 회수 기억: {' / '.join(long_term) if long_term else '없음'}",
                f"- 내적 독백: {' / '.join(monologues) if monologues else '없음'}",
            ]
        )
    return "\n".join(
        [
            f"### Interview: {resolved_agent_id}",
            f"- Question: {question_text}",
            f"- Recent actions: {' / '.join(recent_actions) if recent_actions else 'none'}",
            f"- Short-term memory: {' / '.join(short_term) if short_term else 'none'}",
            f"- Retrieved memory: {' / '.join(long_term) if long_term else 'none'}",
            f"- Inner monologue: {' / '.join(monologues) if monologues else 'none'}",
        ]
    )


def _comparison_markdown(left: Any, right: Any, seed_a: int, seed_b: int, language: str) -> str:
    key = _language_key(language)
    left_actions = _flatten_action_counts(dict(getattr(left, "action_breakdown", {})))
    right_actions = _flatten_action_counts(dict(getattr(right, "action_breakdown", {})))
    left_top_action, left_top_action_count = left_actions.most_common(1)[0]
    right_top_action, right_top_action_count = right_actions.most_common(1)[0]
    left_top_agent = max(
        dict(getattr(left, "action_breakdown", {})).items(),
        key=lambda item: sum(int(value) for value in item[1].values()),
    )[0]
    right_top_agent = max(
        dict(getattr(right, "action_breakdown", {})).items(),
        key=lambda item: sum(int(value) for value in item[1].values()),
    )[0]
    if key == "ko":
        return "\n".join(
            [
                "### A/B 비교",
                "| 지표 | 시드 A | 시드 B |",
                "| --- | --- | --- |",
                f"| seed | {seed_a} | {seed_b} |",
                f"| 로그 수 | {left.log_count} | {right.log_count} |",
                f"| 지배적 액션 | {left_top_action} ({left_top_action_count}) | {right_top_action} ({right_top_action_count}) |",
                f"| 최다 행동 에이전트 | {left_top_agent} | {right_top_agent} |",
                f"| 관계 엣지 수 | {len(left.relationship_rows)} | {len(right.relationship_rows)} |",
            ]
        )
    return "\n".join(
        [
            "### A/B compare",
            "| Metric | Seed A | Seed B |",
            "| --- | --- | --- |",
            f"| seed | {seed_a} | {seed_b} |",
            f"| log entries | {left.log_count} | {right.log_count} |",
            f"| dominant action | {left_top_action} ({left_top_action_count}) | {right_top_action} ({right_top_action_count}) |",
            f"| busiest agent | {left_top_agent} | {right_top_agent} |",
            f"| relationship edges | {len(left.relationship_rows)} | {len(right.relationship_rows)} |",
        ]
    )


def _compare_runs(
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_runtime_and_compare: Any,
) -> str:
    compare_seed_a = int(trait_runtime_and_compare[-2])
    compare_seed_b = int(trait_runtime_and_compare[-1])
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_runtime_and_compare[:-2],
    )
    left = run_playground_scenario(
        scenario_name=str(request["scenario_name"]),
        provider="Replay only",
        api_key="",
        model="",
        primary_name=str(request["primary_name"]),
        primary_age=int(request["primary_age"]),
        openness=float(dict(request["personality_overrides"])["openness"]),
        conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
        extraversion=float(dict(request["personality_overrides"])["extraversion"]),
        agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
        neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
        personality_overrides=dict(request["personality_overrides"]),
        ticks=int(request["ticks"]),
        agent_count=int(request["agent_count"]),
        environment_preset_id=cast("str | None", request["environment_preset_id"]),
        cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
        agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
        primary_planning_enabled=bool(request["primary_planning_enabled"]),
        planning_depth=int(request["planning_depth"]),
        batch_mode=False,
        batch_runs=1,
        master_seed=compare_seed_a,
        language=str(request["language"]),
        event_injections_text=str(request["event_injections_text"]),
        initial_relationships_text=str(request["initial_relationships_text"]),
    )
    right = run_playground_scenario(
        scenario_name=str(request["scenario_name"]),
        provider="Replay only",
        api_key="",
        model="",
        primary_name=str(request["primary_name"]),
        primary_age=int(request["primary_age"]),
        openness=float(dict(request["personality_overrides"])["openness"]),
        conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
        extraversion=float(dict(request["personality_overrides"])["extraversion"]),
        agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
        neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
        personality_overrides=dict(request["personality_overrides"]),
        ticks=int(request["ticks"]),
        agent_count=int(request["agent_count"]),
        environment_preset_id=cast("str | None", request["environment_preset_id"]),
        cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
        agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
        primary_planning_enabled=bool(request["primary_planning_enabled"]),
        planning_depth=int(request["planning_depth"]),
        batch_mode=False,
        batch_runs=1,
        master_seed=compare_seed_b,
        language=str(request["language"]),
        event_injections_text=str(request["event_injections_text"]),
        initial_relationships_text=str(request["initial_relationships_text"]),
    )
    return _comparison_markdown(left, right, compare_seed_a, compare_seed_b, str(request["language"]))


def _cross_model_card(model_name: str, result: Any, language: str) -> str:
    key = _language_key(language)
    action_counts = _flatten_action_counts(dict(getattr(result, "action_breakdown", {})))
    top_actions = ", ".join(
        f"{action_type}={count}"
        for action_type, count in action_counts.most_common(5)
    ) or "none"
    tick_sequence = _cross_model_tick_sequence(str(getattr(result, "jsonl", "")))
    if key == "ko":
        return "\n".join(
            [
                f"### {model_name}",
                f"- 로그 수: {getattr(result, 'log_count', 0)}",
                f"- 틱 수: {getattr(result, 'tick_count', 0)}",
                f"- 액션 분포: {top_actions}",
                f"- 관계 엣지: {len(getattr(result, 'relationship_rows', []))}",
                "",
                tick_sequence,
            ]
        )
    return "\n".join(
        [
            f"### {model_name}",
            f"- Log entries: {getattr(result, 'log_count', 0)}",
            f"- Ticks: {getattr(result, 'tick_count', 0)}",
            f"- Action mix: {top_actions}",
            f"- Relationship edges: {len(getattr(result, 'relationship_rows', []))}",
            "",
            tick_sequence,
        ]
    )


def _cross_model_tick_sequence(jsonl_text: str) -> str:
    tick_actions: dict[int, list[str]] = {}
    for row in _jsonl_rows(jsonl_text):
        action = row.get("action")
        if not isinstance(action, dict) or "tick" not in row:
            continue
        tick = int(row.get("tick", 0))
        tick_actions.setdefault(tick, []).append(str(action.get("action_type", "observe")))
    lines = ["| Tick | Actions |", "| --- | --- |"]
    for tick in sorted(tick_actions)[:8]:
        counts = Counter(tick_actions[tick])
        action_text = ", ".join(
            f"{action_type} x{count}"
            for action_type, count in counts.most_common(4)
        )
        lines.append(f"| {tick} | {action_text} |")
    return "\n".join(lines)


def _cross_model_diff_markdown(results: dict[str, Any], language: str) -> str:
    key = _language_key(language)
    labels = LABELS[key]
    typed_results = cast("dict[str, PlaygroundResult]", results)
    overlap = cross_model_overlap_ratio(typed_results)
    correlations = cross_model_action_correlations(typed_results)
    if key == "ko":
        lines = [
            f"### {labels['cross_model_diff']}",
            f"- 같은 tick/agent 액션 overlap ratio: {overlap:.3f}",
        ]
        if correlations:
            lines.append("- 모델 간 action-distribution Pearson r:")
            lines.extend(
                f"  - {stat.left} vs {stat.right}: {stat.pearson_r:.3f}"
                for stat in correlations
            )
        lines.extend(_cross_model_divergence_lines(results, language=key))
        return "\n".join(lines)
    lines = [
        f"### {labels['cross_model_diff']}",
        f"- Same tick/agent action overlap ratio: {overlap:.3f}",
    ]
    if correlations:
        lines.append("- Cross-model action-distribution Pearson r:")
        lines.extend(
            f"  - {stat.left} vs {stat.right}: {stat.pearson_r:.3f}"
            for stat in correlations
        )
    lines.extend(_cross_model_divergence_lines(results, language=key))
    return "\n".join(lines)


def _cross_model_divergence_lines(results: dict[str, Any], *, language: str) -> list[str]:
    signatures: dict[str, dict[tuple[int, str], str]] = {}
    for model_name, result in results.items():
        signatures[model_name] = {}
        for row in _jsonl_rows(str(getattr(result, "jsonl", ""))):
            action = row.get("action")
            if not isinstance(action, dict) or "tick" not in row:
                continue
            signatures[model_name][(int(row.get("tick", 0)), str(row.get("agent_id", "agent")))] = str(
                action.get("action_type", "observe")
            )
    if not signatures:
        return []
    common_keys = set(next(iter(signatures.values())))
    for signature in list(signatures.values())[1:]:
        common_keys &= set(signature)
    divergent: list[str] = []
    for key in sorted(common_keys)[:48]:
        actions = {model_name: signature[key] for model_name, signature in signatures.items()}
        if len(set(actions.values())) <= 1:
            continue
        tick, agent_id = key
        detail = ", ".join(f"{model_name}: {action}" for model_name, action in actions.items())
        if language == "ko":
            divergent.append(f"- [DIFF] tick {tick}, {agent_id}: {detail}")
        else:
            divergent.append(f"- [DIFF] tick {tick}, {agent_id}: {detail}")
        if len(divergent) >= 10:
            break
    if not divergent:
        return ["- No divergent tick/agent decisions in the common action window."]
    return divergent


def _compare_models(
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_runtime_and_models: Any,
) -> tuple[str, str, str, str]:
    selected_models = trait_runtime_and_models[-1]
    selected = [str(value) for value in selected_models] if isinstance(selected_models, list) else []
    if not selected:
        selected = ["GPT", "Claude", "Replay"]
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_runtime_and_models[:-1],
    )
    try:
        results = run_cross_model_comparison(
            scenario_name=str(request["scenario_name"]),
            models=selected,
            api_key=str(request["api_key"]),
            model=str(request["model"]),
            primary_name=str(request["primary_name"]),
            primary_age=int(request["primary_age"]),
            openness=float(dict(request["personality_overrides"])["openness"]),
            conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
            extraversion=float(dict(request["personality_overrides"])["extraversion"]),
            agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
            neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
            personality_overrides=dict(request["personality_overrides"]),
            ticks=int(request["ticks"]),
            agent_count=int(request["agent_count"]),
            environment_preset_id=cast("str | None", request["environment_preset_id"]),
            cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
            agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
            primary_planning_enabled=bool(request["primary_planning_enabled"]),
            planning_depth=int(request["planning_depth"]),
            master_seed=int(request["master_seed"]),
            language=str(request["language"]),
            event_injections_text=str(request["event_injections_text"]),
            initial_relationships_text=str(request["initial_relationships_text"]),
        )
    except Exception as exc:
        message = f"Cross-model comparison failed: {exc}"
        return message, message, message, message

    cards = {
        model_name: _cross_model_card(model_name, result, str(request["language"]))
        for model_name, result in results.items()
    }
    placeholder = LABELS[_language_key(str(request["language"]))]["cross_model_empty"]
    return (
        cards.get("GPT", placeholder),
        cards.get("Claude", placeholder),
        cards.get("Replay", placeholder),
        _cross_model_diff_markdown(results, str(request["language"])),
    )


def _run_with_optional_streaming(
    live_streaming: bool,
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
    reviewer_mode: bool = False,
    theme_mode: str | None = None,
) -> Generator[RunWithPlayerModeOutputs, None, None]:
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
    )
    if (
        not bool(live_streaming)
        or bool(request["batch_mode"])
        or str(request["provider"]) != "Replay only"
    ):
        if reviewer_mode:
            if theme_mode is None:
                yield _run_with_player_mode(
                    scenario_name,
                    environment_preset_id,
                    cultural_prior_id,
                    provider,
                    api_key,
                    model,
                    primary_name,
                    primary_age,
                    *trait_and_runtime,
                    reviewer_mode=True,
                )
            else:
                yield _run_with_player_mode(
                    scenario_name,
                    environment_preset_id,
                    cultural_prior_id,
                    provider,
                    api_key,
                    model,
                    primary_name,
                    primary_age,
                    *trait_and_runtime,
                    reviewer_mode=True,
                    theme_mode=theme_mode,
                )
        else:
            if theme_mode is None:
                yield _run_with_player_mode(
                    scenario_name,
                    environment_preset_id,
                    cultural_prior_id,
                    provider,
                    api_key,
                    model,
                    primary_name,
                    primary_age,
                    *trait_and_runtime,
                )
            else:
                yield _run_with_player_mode(
                    scenario_name,
                    environment_preset_id,
                    cultural_prior_id,
                    provider,
                    api_key,
                    model,
                    primary_name,
                    primary_age,
                    *trait_and_runtime,
                    theme_mode=theme_mode,
                )
        return

    from fastapi.testclient import TestClient

    from knoema.api.server import create_app
    from knoema.api.service import SimulationRecord, SimulationService

    artifacts = _prepare_playground_run(
        scenario_name=str(request["scenario_name"]),
        provider="Replay only",
        api_key="",
        model="",
        primary_name=str(request["primary_name"]),
        primary_age=int(request["primary_age"]),
        openness=float(dict(request["personality_overrides"])["openness"]),
        conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
        extraversion=float(dict(request["personality_overrides"])["extraversion"]),
        agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
        neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
        personality_overrides=dict(request["personality_overrides"]),
        agent_count=int(request["agent_count"]),
        environment_preset_id=cast("str | None", request["environment_preset_id"]),
        cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
        agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
        primary_planning_enabled=bool(request["primary_planning_enabled"]),
        planning_depth=int(request["planning_depth"]),
        language=str(request["language"]),
        seed=int(request["master_seed"]),
        event_injections_text=str(request["event_injections_text"]),
        initial_relationships_text=str(request["initial_relationships_text"]),
    )
    service = SimulationService()
    now = datetime.now(UTC)
    simulation_id = uuid.uuid4().hex
    record = SimulationRecord(
        simulation_id=simulation_id,
        simulator=artifacts.simulator,
        duration_days=1,
        total_ticks=int(request["ticks"]),
        started_at=now,
        updated_at=now,
        stream_delay_seconds=0.0,
    )
    record.worker = threading.Thread(
        target=service._run_record,
        args=(record, None),
        daemon=True,
        name=f"knoema-stream-{simulation_id}",
    )
    service._records[simulation_id] = record
    record.worker.start()

    try:
        with (
            TestClient(create_app(simulation_service=service)) as client,
            client.websocket_connect(f"/simulations/{simulation_id}/stream") as websocket,
        ):
            while True:
                message = websocket.receive_json()
                result = playground_result_from_artifacts(
                    scenario_name=str(request["scenario_name"]),
                    mode="Replay only",
                    artifacts=artifacts,
                    language=str(request["language"]),
                )
                yield (
                    *_render_result_outputs(
                        result,
                        mode_label=_provider_label("Replay only", str(request["language"])),
                        provider="Replay only",
                        api_key="",
                        language=str(request["language"]),
                        reviewer_mode=reviewer_mode,
                        theme_mode=theme_mode,
                    ),
                    gr.update(value=None),
                    None,
                    "",
                )
                if message["type"] == "simulation.status":
                    break
    finally:
        service.shutdown()


def _run_with_optional_streaming_ui(
    live_streaming: bool,
    reviewer_mode: bool,
    advanced_research_mode: bool,
    advanced_research_ack: bool,
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
    theme_mode: str | None = None,
) -> Generator[RunWithPlayerModeOutputs, None, None]:
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
    )
    violation = _research_gate_violation(
        str(request["scenario_name"]),
        str(request["language"]),
        advanced_research_mode,
        advanced_research_ack,
    )
    if violation:
        yield (
            *_noop_run_outputs(),
            gr.update(value=None),
            None,
            violation,
        )
        return
    yield from _run_with_optional_streaming(
        live_streaming,
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
        reviewer_mode=reviewer_mode,
        theme_mode=theme_mode,
    )


def _run_with_optional_streaming_ui_theme(
    live_streaming: bool,
    reviewer_mode: bool,
    theme_mode: str,
    advanced_research_mode: bool,
    advanced_research_ack: bool,
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
) -> Generator[RunWithPlayerModeOutputs, None, None]:
    yield from _run_with_optional_streaming_ui(
        live_streaming,
        reviewer_mode,
        advanced_research_mode,
        advanced_research_ack,
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
        theme_mode=theme_mode,
    )


def _status_with_voice_notes(status: str, voice_notes: list[str]) -> str:
    filtered = [note.strip() for note in voice_notes if note and note.strip()]
    if not filtered:
        return status
    if status.strip():
        return status.strip() + "\n\n" + "\n".join(f"- {note}" for note in filtered)
    return "\n".join(f"- {note}" for note in filtered)


def _latest_npc_response_text(
    result: Any,
    session: dict[str, Any] | None,
) -> str:
    player_agent_id = str((session or {}).get("player_agent_id", "")).strip()
    if not player_agent_id:
        return ""
    for line in reversed(str(getattr(result, "jsonl", "")).splitlines()):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(payload.get("agent_id", "")) == player_agent_id:
            continue
        action = payload.get("action", {})
        if isinstance(action, dict):
            content = str(action.get("content", "")).strip()
            if content:
                return content
    return ""


def _advance_player_mode(
    session: dict[str, Any] | None,
    player_text: str,
    player_audio_path: str | None,
    stt_engine: str,
    tts_engine: str,
    reviewer_mode: bool = False,
    theme_mode: str | None = None,
) -> PlayerAdvanceOutputs:
    language = str((session or {}).get("language", "en"))
    voice_notes: list[str] = []
    resolved_text = str(player_text or "").strip()
    if not resolved_text and player_audio_path:
        transcript, stt_status = transcribe_player_audio(
            player_audio_path,
            engine=str(stt_engine or "off"),
            language=language,
        )
        if stt_status:
            voice_notes.append(stt_status)
        resolved_text = transcript.strip()
    if not resolved_text:
        empty_input_status = (
            "먼저 텍스트를 입력하거나 음성 입력을 제공하세요."
            if language == "ko"
            else "Provide text or voice input first."
        )
        return (
            *_noop_run_outputs(),
            gr.update(value=None),
            session,
            _status_with_voice_notes(empty_input_status, voice_notes),
            gr.update(value=""),
        )

    updated_session, result, status = advance_player_session(session, resolved_text)
    if result is None:
        return (
            *_noop_run_outputs(),
            gr.update(value=None),
            updated_session,
            _status_with_voice_notes(status, voice_notes),
            gr.update(value=""),
        )

    response_audio, tts_status = synthesize_text_to_audio(
        _latest_npc_response_text(result, updated_session or session),
        engine=str(tts_engine or "off"),
        language=language,
    )
    if tts_status:
        voice_notes.append(tts_status)
    return (
        *_render_result_outputs(
            result,
            mode_label=_provider_label("Player mode", language),
            provider="Player mode",
            api_key="",
            language=language,
            reviewer_mode=reviewer_mode,
            theme_mode=theme_mode,
        ),
        gr.update(value=response_audio),
        updated_session,
        _status_with_voice_notes(status, voice_notes),
        gr.update(value=""),
    )


def _advance_player_mode_theme(
    session: dict[str, Any] | None,
    player_text: str,
    player_audio_path: str | None,
    stt_engine: str,
    tts_engine: str,
    theme_mode: str,
    reviewer_mode: bool = False,
) -> PlayerAdvanceOutputs:
    return _advance_player_mode(
        session,
        player_text,
        player_audio_path,
        stt_engine,
        tts_engine,
        reviewer_mode=reviewer_mode,
        theme_mode=theme_mode,
    )


def _player_mode_language_updates(provider: str, language_choice: str) -> list[Any]:
    language = _language_key(language_choice)
    labels = LABELS[language]
    is_player_mode = _normalize_provider(provider) == "Player mode"
    return [
        gr.update(visible=is_player_mode),
        gr.update(
            label=labels["player_input"],
            placeholder=labels["player_input_placeholder"],
        ),
        gr.update(value=labels["player_submit"]),
        gr.update(
            label=labels["player_voice_input"],
        ),
        gr.update(
            label=labels["player_voice_output"],
        ),
        gr.update(
            label=labels["player_stt_engine"],
            choices=stt_engine_choices(language),
        ),
        gr.update(
            label=labels["player_tts_engine"],
            choices=tts_engine_choices(language),
        ),
    ]


def _player_mode_provider_updates(provider: str, language_choice: str) -> list[Any]:
    (
        panel_update,
        input_update,
        submit_update,
        voice_input_update,
        voice_output_update,
        stt_update,
        tts_update,
    ) = _player_mode_language_updates(
        provider,
        language_choice,
    )
    return [
        panel_update,
        gr.update(value=""),
        input_update,
        submit_update,
        voice_input_update,
        voice_output_update,
        stt_update,
        tts_update,
        None,
    ]


def _scenario_agent_count_update(scenario_name: str) -> dict[str, Any]:
    return gr.update(value=scenario_default_agent_count(scenario_name))


def _apply_persona_preset(preset_id: str | None) -> list[dict[str, Any]]:
    values = persona_trait_values(preset_id, PERSONA_TRAIT_FIELDS)
    if values is None:
        return [gr.update() for _ in PERSONA_TRAIT_FIELDS]
    return [gr.update(value=value) for value in values]


def _apply_routine_preset(preset_id: str | None, language: str) -> dict[str, Any]:
    language_key = _language_key(language)
    return gr.update(
        value=routine_preset_text(preset_id),
        placeholder=LABELS[language_key]["routine_text_placeholder"],
    )


def _apply_cultural_prior(prior_id: str | None) -> list[dict[str, Any]]:
    values = cultural_prior_trait_values(prior_id, PERSONA_TRAIT_FIELDS)
    return [gr.update(value=value) for value in values]


def _apply_cultural_prior_to_all_tabs(prior_id: str | None) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for _ in range(AGENT_EDITOR_SLOT_COUNT):
        updates.extend(_apply_cultural_prior(prior_id))
    return updates


def _agent_tab_label(slot_index: int, language: str) -> str:
    labels = LABELS[language]
    return f"{labels['agent_tab_prefix']} {slot_index + 1}"


def _agent_editor_updates(
    scenario_name: str,
    agent_count: int,
    cultural_prior_id: str | None,
    language_choice: str,
    *,
    current_slot_states: list[dict[str, Any]] | None = None,
) -> list[Any]:
    language = _language_key(language_choice)
    labels = LABELS[language]
    questionnaire_defaults = questionnaire_default_responses()
    defaults = agent_editor_defaults(
        scenario_name,
        agent_count=agent_count,
        slot_count=AGENT_EDITOR_SLOT_COUNT,
        cultural_prior_id=cultural_prior_id,
        language=language,
    )
    updates: list[Any] = []
    for slot_index, default in enumerate(defaults):
        current_state = (
            current_slot_states[slot_index]
            if current_slot_states is not None and slot_index < len(current_slot_states)
            else None
        )
        personality_values = (
            dict(default["personality"])
            if current_state is None
            else {
                field_name: float(current_state["personality"].get(field_name, default["personality"][field_name]))
                for field_name in PERSONA_TRAIT_FIELDS
            }
        )
        questionnaire_values = dict(questionnaire_defaults)
        if current_state is not None:
            questionnaire_values.update(
                {
                    item.item_id: _questionnaire_response_value(
                        current_state["questionnaire_responses"].get(item.item_id)
                    )
                    for item in HEXACO_QUESTIONNAIRE_ITEMS
                }
            )
        mode_value = _questionnaire_mode_value(
            QUESTIONNAIRE_MODE_SLIDERS
            if current_state is None
            else current_state.get("personality_input_mode")
        )
        questionnaire_summary_value = (
            questionnaire_empty_summary(language)
            if mode_value != QUESTIONNAIRE_MODE_HEXACO
            else questionnaire_summary_markdown(
                score_hexaco_questionnaire(questionnaire_values),
                language,
            )
        )
        updates.extend(
            [
                gr.update(
                    label=_agent_tab_label(slot_index, language),
                    interactive=bool(default["enabled"]),
                ),
                gr.update(visible=bool(default["enabled"])),
                gr.update(
                    value=labels["agent_tab_disabled"],
                    visible=not bool(default["enabled"]),
                ),
                gr.update(
                    label=labels["name"],
                    value=default["name"] if current_state is None else str(current_state["name"]),
                ),
                gr.update(
                    label=labels["age"],
                    value=int(default["age"] if current_state is None else current_state["age"]),
                ),
                gr.update(
                    label=labels["persona_preset"],
                    choices=_persona_choices(language),
                    value="" if current_state is None else str(current_state["persona_preset"]),
                    info=labels["persona_preset_info"],
                ),
                gr.update(
                    label=labels["routine_preset"],
                    choices=_routine_preset_choices(language),
                    value="free" if current_state is None else str(current_state["routine_preset"]),
                    info=labels["routine_preset_info"],
                ),
                gr.update(
                    label=labels["routine_text"],
                    value=(
                        str(default.get("routine_text", ""))
                        if current_state is None
                        else str(current_state["routine_text"])
                    ),
                    info=labels["routine_text_info"],
                    placeholder=labels["routine_text_placeholder"],
                ),
                gr.update(
                    label=questionnaire_mode_label(language),
                    choices=questionnaire_mode_choices(language),
                    value=mode_value,
                ),
                gr.update(
                    label=questionnaire_panel_label(language),
                    visible=bool(default["enabled"]) and mode_value == QUESTIONNAIRE_MODE_HEXACO,
                    open=bool(default["enabled"]) and mode_value == QUESTIONNAIRE_MODE_HEXACO,
                ),
                questionnaire_intro_markdown(language),
                *[
                    gr.update(label=questionnaire_domain_label(domain, language))
                    for domain in HEXACO_DOMAINS
                ],
                gr.update(value=questionnaire_apply_label(language)),
                questionnaire_summary_value,
                gr.update(label=labels["tier_a_panel"]),
                gr.update(label=labels["extended_panel"]),
                labels["extended_panel_note"],
                gr.update(label=labels["tier_bd_panel"]),
                _honesty_humility_caveat_update(language_choice),
                gr.update(label=labels["tier_c_panel"]),
                labels["dark_tetrad_notice"],
                gr.update(label=labels["tier_e_panel"]),
                gr.update(label=labels["tier_f_panel"]),
                gr.update(label=labels["tier_g_panel"]),
            ]
        )
        updates.extend(
            [
                gr.update(
                    label=labels[field_name],
                    info=labels[f"{field_name}_info"],
                    value=float(personality_values[field_name]),
                )
                for field_name in PERSONA_TRAIT_FIELDS
            ]
        )
        updates.extend(
            [
                gr.update(
                    label=item.label,
                    info=item.prompt(language),
                    value=questionnaire_values[item.item_id],
                )
                for item in HEXACO_QUESTIONNAIRE_ITEMS
            ]
        )
    return updates


def _scenario_agent_editor_updates(
    scenario_name: str,
    cultural_prior_id: str | None,
    language_choice: str,
) -> list[Any]:
    return _agent_editor_updates(
        scenario_name,
        scenario_default_agent_count(scenario_name),
        cultural_prior_id,
        language_choice,
    )


def _hint_markdown_update(
    scenario_name: str | None,
    language_choice: str,
    environment_preset_id: str | None = None,
) -> str:
    language = _language_key(language_choice)
    return build_playground_hint(
        scenario_name=scenario_name,
        language=language,
        environment_note=environment_note(environment_preset_id, language),
    )


SENSITIVE_SCENARIO_NAMES = frozenset(
    {
        "Hospital waiting room",
        "ER triage",
        "Refugee shelter arrival",
        "Prison yard (fictional)",
    }
)
DARK_TETRAD_FIELDS = ("machiavellianism", "narcissism", "psychopathy", "sadism")


def _advanced_research_unlocked(enabled: bool, acknowledged: bool) -> bool:
    return bool(enabled and acknowledged)


def _scenario_choices_with_gate(unlocked: bool, language: str = "en") -> list[tuple[str, str]]:
    return [
        (scenario_label(scenario_name, language), scenario_name)
        for scenario_name in scenario_choices()
        if unlocked or scenario_name not in SENSITIVE_SCENARIO_NAMES
    ]


def _default_scenario_name() -> str:
    choices = scenario_choices()
    if PLAYGROUND_DEFAULT_SCENARIO in choices:
        return PLAYGROUND_DEFAULT_SCENARIO
    return choices[0]


def _advanced_research_status_text(
    language_choice: str,
    enabled: bool,
    acknowledged: bool,
) -> str:
    key = language_choice if language_choice in {"ko", "en"} else _language_key(language_choice)
    labels = LABELS[key]
    if _advanced_research_unlocked(enabled, acknowledged):
        if key == "ko":
            return (
                "- 고급 연구 모드가 잠금 해제되었습니다.\n"
                "- Dark Tetrad 컨트롤과 민감한 가상 시나리오가 활성화됩니다."
            )
        return (
            "- Advanced research mode unlocked.\n"
            "- Dark Tetrad controls and sensitive fictional scenarios are available."
        )
    if enabled and not acknowledged:
        if key == "ko":
            return (
                f"- {labels['advanced_research_notice']}\n"
                "- 추가 컨트롤을 해제하려면 안내 사항에 동의 체크해 주세요."
            )
        return (
            f"- {labels['advanced_research_notice']}\n"
            "- Acknowledge the notice to unlock the additional controls."
        )
    return f"- {labels['advanced_research_locked']}"


def _advanced_research_ui_updates(
    current_scenario: str | None,
    language_choice: str,
    enabled: bool,
    acknowledged: bool,
) -> list[Any]:
    unlocked = _advanced_research_unlocked(enabled, acknowledged)
    language_key = language_choice if language_choice in {"ko", "en"} else _language_key(language_choice)
    choices = _scenario_choices_with_gate(unlocked, language_key)
    canonical_choices = [pair[1] for pair in choices]
    default_scenario = _default_scenario_name()
    fallback_scenario = (
        default_scenario
        if default_scenario in canonical_choices
        else (canonical_choices[0] if canonical_choices else default_scenario)
    )
    scenario_value = current_scenario if current_scenario in canonical_choices else fallback_scenario
    panel_update = gr.update(visible=unlocked, open=False)
    notice_value = (
        LABELS["ko"]["dark_tetrad_notice"]
        if (language_choice if language_choice in {"ko", "en"} else _language_key(language_choice)) == "ko"
        else LABELS["en"]["dark_tetrad_notice"]
    )
    if not unlocked:
        notice_value = _advanced_research_status_text(language_choice, enabled, acknowledged)
    updates: list[Any] = [
        gr.update(choices=choices, value=scenario_value),
        _advanced_research_status_text(language_choice, enabled, acknowledged),
    ]
    for _ in range(AGENT_EDITOR_SLOT_COUNT):
        updates.extend([panel_update, notice_value])
        updates.extend(
            [
                gr.update()
                if unlocked
                else gr.update(value=PERSONA_TRAIT_DEFAULTS[field_name])
                for field_name in DARK_TETRAD_FIELDS
            ]
        )
    return updates


def _research_gate_violation(
    scenario_name: str,
    language_choice: str,
    enabled: bool,
    acknowledged: bool,
) -> str | None:
    if _advanced_research_unlocked(enabled, acknowledged):
        return None
    if scenario_name not in SENSITIVE_SCENARIO_NAMES:
        return None
    key = language_choice if language_choice in {"ko", "en"} else _language_key(language_choice)
    if key == "ko":
        return "Advanced research mode와 IRB-style notice 확인 후에만 민감한 fictional scenario를 실행할 수 있습니다."
    return "Sensitive fictional scenarios require Advanced research mode and IRB-style notice acknowledgement."


def _batch_control_updates(enabled: bool) -> list[dict[str, Any]]:
    return [
        gr.update(interactive=bool(enabled)),
        gr.update(interactive=bool(enabled)),
    ]


def _trait_update(field_name: str, labels: dict[str, str]) -> dict[str, Any]:
    return gr.update(label=labels[field_name], info=labels[f"{field_name}_info"])


def _competitive_comparison_markdown(language: str) -> str:
    key = _language_key(language)
    labels = LABELS[key]
    if key == "ko":
        header = (
            "| System | 초점 | 기억/세계 모델 | 재현 가능 표면 | 게임 어댑터 | License | Reference |\n"
            "| --- | --- | --- | --- | --- | --- | --- |"
        )
        rows = [
            (
                f"| {row['system']} | {row['focus_ko']} | {row['memory_ko']} | "
                f"{row['repro_ko']} | {row['game_ko']} | {row['license']} | "
                f"[public]({row['reference']}) |"
            )
            for row in COMPETITIVE_COMPARISON_ROWS
        ]
    else:
        header = (
            "| System | Focus | Memory / world model | Reproducible surface | "
            "Game adapters | License | Reference |\n"
            "| --- | --- | --- | --- | --- | --- | --- |"
        )
        rows = [
            (
                f"| {row['system']} | {row['focus_en']} | {row['memory_en']} | "
                f"{row['repro_en']} | {row['game_en']} | {row['license']} | "
                f"[public]({row['reference']}) |"
            )
            for row in COMPETITIVE_COMPARISON_ROWS
        ]
    return "\n".join(
        [
            f"### {labels['competitive_panel']}",
            labels["competitive_intro"],
            "",
            header,
            *rows,
            "",
            _benchmark_evidence_markdown(key),
        ]
    )


def _benchmark_evidence_markdown(language: str) -> str:
    key = _language_key(language)
    title = "### 벤치마크 근거와 caveat" if key == "ko" else "### Benchmark Evidence and Caveats"
    intro = (
        "아래 수치는 발표나 평가에서 caveat와 함께 읽어야 합니다."
        if key == "ko"
        else "Read each benchmark row together with its caveat before making claims."
    )
    lines = [title, intro, ""]
    for row in BENCHMARK_EVIDENCE_ROWS:
        label = row["label_ko"] if key == "ko" else row["label_en"]
        metric = row["metric_ko"] if key == "ko" else row["metric_en"]
        lines.append(
            f"- **{label}**: {metric} | caveat: `{row['caveat']}` | source: `{row['source']}`"
        )
    return "\n".join(lines)


def _language_updates(
    lang_choice: str,
    current_provider: str | None,
    current_scenario: str | None = None,
    current_environment: str | None = None,
    current_cultural_prior: str | None = None,
    current_persona: str | None = None,
    current_agent_count: int | None = None,
    current_htn_enabled: bool = False,
    current_planning_depth: int | None = None,
    current_batch_mode: bool = False,
    current_batch_runs: int | None = None,
    current_master_seed: int | None = None,
    current_live_streaming: bool = False,
    current_theme_mode: str | None = None,
    current_advanced_research_mode: bool = False,
    current_advanced_research_ack: bool = False,
    current_power_test: str = "independent_t",
    current_power_effect: float = 0.5,
    current_power_alpha: float = 0.05,
    current_power_target: float = 0.8,
    current_planned_n: float | None = None,
    *agent_editor_state: Any,
) -> list[Any]:
    key = _language_key(lang_choice)
    labels = LABELS[key]
    current_slot_states = _agent_editor_state_blocks(*agent_editor_state)
    advanced_unlocked = _advanced_research_unlocked(
        current_advanced_research_mode,
        current_advanced_research_ack,
    )
    allowed_scenarios = _scenario_choices_with_gate(advanced_unlocked, key)
    canonical_scenarios = [pair[1] for pair in allowed_scenarios]
    provider_value = _normalize_provider(current_provider or "Replay only")
    theme_value = _normalize_theme_mode(current_theme_mode)
    default_scenario = _default_scenario_name()
    scenario_value = current_scenario or default_scenario
    if scenario_value not in canonical_scenarios:
        scenario_value = (
            default_scenario if default_scenario in canonical_scenarios else canonical_scenarios[0]
        )
    environment_value = current_environment or _default_environment_id()
    agent_count_value = int(current_agent_count or scenario_default_agent_count(scenario_value))
    planning_depth_value = int(current_planning_depth or 3)
    batch_runs_value = int(current_batch_runs or 10)
    master_seed_value = int(current_master_seed or 20260419)
    agent_editor_updates = _agent_editor_updates(
        scenario_value,
        agent_count_value,
        current_cultural_prior,
        lang_choice,
        current_slot_states=current_slot_states,
    )
    trait_matrix_figure, trait_matrix_summary = _trait_correlation_outputs(key)
    return [
        labels["header"],
        gr.update(label=labels["scenario"], choices=allowed_scenarios, value=scenario_value),
        gr.update(
            label=labels["environment"],
            choices=_preset_choices(key),
            value=environment_value,
            info=labels["environment_info"],
        ),
        gr.update(
            label=labels["mode"],
            choices=_provider_choices(key),
            value=provider_value,
        ),
        gr.update(
            label=labels["theme"],
            choices=_theme_choices(key),
            value=theme_value,
            info=labels["theme_info"],
        ),
        gr.update(label=labels["reviewer_mode"]),
        gr.update(label=labels["api_key"], placeholder=labels["api_key_ph"]),
        gr.update(label=labels["model"]),
        gr.update(label=labels["agent_panel"]),
        gr.update(
            label=labels["cultural_prior"],
            choices=_cultural_prior_choices(key),
            value=current_cultural_prior or "",
            info=labels["cultural_prior_info"],
        ),
        gr.update(
            label=labels["advanced_research_mode"],
            value=current_advanced_research_mode,
        ),
        gr.update(
            label=labels["advanced_research_ack"],
            value=current_advanced_research_ack,
        ),
        labels["advanced_research_notice"],
        _advanced_research_status_text(
            key,
            current_advanced_research_mode,
            current_advanced_research_ack,
        ),
        *agent_editor_updates,
        gr.update(label=labels["agents"], info=labels["agents_info"], value=agent_count_value),
        gr.update(
            label=labels["htn_enabled"],
            info=labels["htn_info"],
            value=current_htn_enabled,
        ),
        gr.update(
            label=labels["planning_depth"],
            info=labels["planning_depth_info"],
            value=planning_depth_value,
        ),
        gr.update(label=labels["ticks"]),
        gr.update(
            label=labels["batch_mode"],
            info=labels["batch_mode_info"],
            value=current_batch_mode,
        ),
        gr.update(
            label=labels["batch_runs"],
            info=labels["batch_runs_info"],
            value=batch_runs_value,
            interactive=bool(current_batch_mode),
        ),
        gr.update(
            label=labels["master_seed"],
            info=labels["master_seed_info"],
            value=master_seed_value,
            interactive=bool(current_batch_mode),
        ),
        gr.update(
            label=labels["live_streaming"],
            info=labels["live_streaming_info"],
            value=bool(current_live_streaming),
        ),
        gr.update(label=labels["mirofish_panel"]),
        gr.update(
            label=labels["seed_prompt"],
            placeholder=labels["seed_prompt_placeholder"],
        ),
        gr.update(value=labels["seed_prompt_apply"]),
        gr.update(
            label=labels["event_injections"],
            placeholder=labels["event_injections_placeholder"],
        ),
        gr.update(
            label=labels["initial_relationships"],
            placeholder=labels["initial_relationships_placeholder"],
        ),
        gr.update(label=labels["report_agent_panel"]),
        gr.update(label=labels["report_agent_question"]),
        gr.update(value=labels["report_agent_run"]),
        gr.update(label=labels["competitive_panel"]),
        _competitive_comparison_markdown(key),
        gr.update(label=labels["cross_model_panel"]),
        gr.update(
            label=labels["cross_model_models"],
            choices=list(CROSS_MODEL_CHOICES),
            value=["GPT", "Claude", "Replay"],
        ),
        gr.update(value=labels["cross_model_button"]),
        gr.update(label=labels["prereg_panel"]),
        gr.update(
            label=labels["prereg_template"],
            choices=prereg_template_choices(key),
        ),
        gr.update(label=labels["prereg_title"]),
        gr.update(label=labels["prereg_hypotheses"]),
        gr.update(label=labels["prereg_design"]),
        gr.update(label=labels["prereg_data_generation"]),
        gr.update(label=labels["prereg_factor_design"]),
        gr.update(label=labels["prereg_outcomes"]),
        gr.update(label=labels["prereg_performance_metrics"]),
        gr.update(label=labels["prereg_aggregation"]),
        gr.update(label=labels["prereg_analysis"]),
        gr.update(label=labels["prereg_freeze"]),
        gr.update(label=labels["prereg_deviations"]),
        gr.update(label=labels["prereg_planned_n"], value=current_planned_n or _power_defaults()["planned_n"]),
        gr.update(
            label=labels["prereg_power_test"],
            choices=_power_test_choices(key),
            value=current_power_test,
        ),
        gr.update(label=labels["prereg_power_effect"], value=current_power_effect),
        gr.update(label=labels["prereg_power_alpha"], value=current_power_alpha),
        gr.update(label=labels["prereg_power_target"], value=current_power_target),
        _power_analysis_markdown(
            key,
            current_power_test,
            current_power_effect,
            current_power_alpha,
            current_power_target,
        ),
        gr.update(value=labels["prereg_button"]),
        gr.update(label=labels["prereg_download"]),
        gr.update(label=labels["compare_panel"]),
        gr.update(label=labels["compare_seed_a"]),
        gr.update(label=labels["compare_seed_b"]),
        gr.update(value=labels["compare_button"]),
        gr.update(label=labels["interview_panel"]),
        gr.update(
            label=labels["interview_agent"],
            choices=[],
            value="agent_1",
        ),
        gr.update(label=labels["interview_question"]),
        gr.update(value=labels["interview_button"]),
        _hint_markdown_update(current_scenario, lang_choice, environment_value),
        gr.update(value=labels["run"]),
        gr.update(value=f"#### {labels['export_panel']}"),
        gr.update(label=labels["summary"]),
        gr.update(
            label=labels["action_chart"],
            value=_action_chart_figure({}, language=key),
        ),
        gr.update(label=labels["graph"]),
        gr.update(label=labels["tick_scrubber"]),
        gr.update(label=labels["tick_focus"]),
        gr.update(label=labels["timeline"]),
        gr.update(label=labels["timeline"]),
        gr.update(label=labels["threads_tab"]),
        labels["threads_empty"],
        gr.update(label=labels["memory_inspector"]),
        gr.update(
            label=labels["memory_agent"],
            choices=[],
            value=[],
            interactive=False,
        ),
        labels["memory_empty"],
        gr.update(
            label=labels["memory_emotion"],
            value=_emotion_trajectory_figure({}, [], language=key),
        ),
        gr.update(label=labels["spatial_heatmap_panel"]),
        gr.update(
            label=labels["spatial_heatmap"],
            value=_spatial_heatmap_figure("", {}, language=key),
        ),
        gr.update(label=labels["action_flow_panel"]),
        gr.update(
            label=labels["action_flow"],
            value=_action_flow_figure("", language=key),
        ),
        gr.update(label=labels["mini_map_panel"]),
        gr.update(
            label=labels["mini_map"],
            value=_mini_map_figure("", -1, language=key),
        ),
        gr.update(label=labels["monologue_panel"]),
        labels["monologue_empty"],
        gr.update(label=labels["current_plan_panel"]),
        labels["current_plan_empty"],
        gr.update(label=labels["trait_matrix_panel"]),
        trait_matrix_figure,
        trait_matrix_summary,
        gr.update(label=labels["statistics_panel"]),
        gr.update(label=labels["fairness_panel"]),
        gr.update(
            label=labels["fairness_plot"],
            value=_fairness_empty_figure(labels["fairness_plot"], labels["fairness_empty"]),
        ),
        labels["fairness_empty"],
        gr.update(label=labels["jsonl"]),
        gr.update(label=labels["download"]),
        gr.update(value=labels["html_report_button"]),
        gr.update(label=labels["html_report_download"]),
        gr.update(value=labels["csv_bundle_button"]),
        gr.update(label=labels["csv_bundle_download"]),
        gr.update(
            label=labels["finetuning_format"],
            choices=_finetuning_format_choices(key),
            value="openai",
        ),
        gr.update(value=labels["finetuning_button"]),
        gr.update(label=labels["finetuning_download"]),
        gr.update(value=labels["latex_table_button"]),
        gr.update(label=labels["latex_table_download"]),
        gr.update(value=labels["replication_button"]),
        gr.update(label=labels["replication_download"]),
        gr.update(value=labels["repro_certificate_button"]),
        gr.update(label=labels["repro_certificate_download"]),
        gr.update(label=labels["deposit_panel"]),
        gr.update(label=labels["deposit_creators"]),
        gr.update(label=labels["deposit_description"]),
        gr.update(label=labels["deposit_keywords"]),
        gr.update(label=labels["deposit_token"]),
        gr.update(label=labels["deposit_sandbox"]),
        gr.update(label=labels["deposit_publish"]),
        gr.update(value=labels["deposit_button"]),
        labels["deposit_status"],
        gr.update(label=labels["deposit_download"]),
        labels["report_agent_empty"],
        labels["cross_model_empty"],
        labels["cross_model_empty"],
        labels["cross_model_empty"],
        labels["cross_model_empty"],
        labels["compare_empty"],
        labels["interview_empty"],
        gr.update(label=labels["lang"]),
    ]


def _trait_axis_label(field_name: str, language: str) -> str:
    label = LABELS[language].get(field_name, field_name.replace("_", " ").title())
    return label.replace(" / ", "<br>")


def _trait_text_label(field_name: str, language: str) -> str:
    return LABELS[language].get(field_name, field_name.replace("_", " ").title())


def _trait_correlation_outputs(language: str) -> tuple[go.Figure, str]:
    return (
        _trait_correlation_figure(language),
        trait_correlation_summary(language=language),
    )


def _trait_correlation_figure(language: str) -> go.Figure:
    study = compute_trait_correlation_study()
    axis_labels = [_trait_axis_label(field_name, language) for field_name in study.trait_names]
    title = "Trait correlation matrix" if language == "en" else "Trait 상관 행렬"
    figure = go.Figure(
        data=[
            go.Heatmap(
                z=study.correlation_matrix,
                x=axis_labels,
                y=axis_labels,
                zmin=-1.0,
                zmax=1.0,
                colorscale="RdBu",
                reversescale=True,
                hovertemplate="%{y} ↔ %{x}<br>r=%{z:.2f}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title=title,
        height=620,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        xaxis={"tickangle": -45},
        yaxis={"autorange": "reversed"},
    )
    return figure


def _agent_color_map(agent_ids: list[str]) -> dict[str, str]:
    ordered_agent_ids = sorted(dict.fromkeys(agent_ids))
    if not ordered_agent_ids:
        return {}
    return {
        agent_id: AGENT_COLOR_SEQUENCE[index % len(AGENT_COLOR_SEQUENCE)]
        for index, agent_id in enumerate(ordered_agent_ids)
    }


def _action_chart_figure(
    breakdown: dict[str, dict[str, int]],
    *,
    language: str = "en",
) -> go.Figure:
    title = "액션 타입 분해도" if language == "ko" else "Action type breakdown"
    empty_text = "데이터가 충분하지 않습니다." if language == "ko" else "Not enough data yet"
    xaxis_title = "에이전트" if language == "ko" else "Agent"
    yaxis_title = "행동 수" if language == "ko" else "Action count"
    legend_title = "행동 타입" if language == "ko" else "Action type"
    ordered_agents = sorted(breakdown)
    action_types = sorted(
        {
            action_type
            for action_counts in breakdown.values()
            for action_type, count in action_counts.items()
            if int(count) > 0
        }
    )
    if not ordered_agents or not action_types:
        figure = go.Figure()
        figure.update_layout(
            title=title,
            height=ACTION_CHART_HEIGHT_PX,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
            annotations=[{"text": empty_text, "showarrow": False}],
        )
        return figure

    color_map = _agent_color_map(ordered_agents)
    figure = go.Figure()
    for index, action_type in enumerate(action_types):
        y_values = [
            int(breakdown.get(agent_id, {}).get(action_type, 0))
            for agent_id in ordered_agents
        ]
        if not any(y_values):
            continue
        figure.add_bar(
            name=action_type,
            x=ordered_agents,
            y=y_values,
            marker={
                "color": [color_map[agent_id] for agent_id in ordered_agents],
                "line": {"color": "#0f172a", "width": 0.6},
                "pattern": {
                    "shape": ACTION_PATTERN_SEQUENCE[index % len(ACTION_PATTERN_SEQUENCE)]
                },
            },
            hovertemplate="%{x}<br>%{fullData.name}: %{y}<extra></extra>",
        )

    figure.update_layout(
        title=title,
        barmode="stack",
        height=ACTION_CHART_HEIGHT_PX,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
        xaxis={"title": xaxis_title},
        yaxis={"title": yaxis_title},
        legend={"title": {"text": legend_title}},
        plot_bgcolor="rgba(248,250,252,1)",
        paper_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _tick_focus_markdown(jsonl_text: str, tick: int, language: str = "en") -> str:
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    if not rows:
        return LABELS[language]["tick_focus_empty"]
    if any("record_type" in row for row in rows):
        return _batch_tick_focus_markdown(rows, tick, language=language)
    return _single_run_tick_focus_markdown(rows, tick, language=language)


def _memory_inspector_outputs(
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    language: str = "en",
    batch_mode: bool = False,
) -> tuple[dict[str, dict[str, list[dict[str, Any]]]], dict[str, Any], str, go.Figure]:
    if batch_mode:
        return (
            {},
            gr.update(choices=[], value=[], interactive=False),
            LABELS[language]["memory_batch"],
            _emotion_trajectory_figure({}, [], language=language),
        )

    agent_ids = sorted(snapshot)
    if not agent_ids:
        return (
            snapshot,
            gr.update(choices=[], value=[], interactive=False),
            LABELS[language]["memory_empty"],
            _emotion_trajectory_figure(snapshot, [], language=language),
        )

    selected_agents = [agent_ids[0]]
    return (
        snapshot,
        gr.update(choices=agent_ids, value=selected_agents, interactive=True),
        _memory_inspector_markdown(snapshot, selected_agents, language=language),
        _emotion_trajectory_figure(snapshot, selected_agents, language=language),
    )


def _memory_inspector_markdown(
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    agent_id: str | list[str] | None,
    language: str = "en",
) -> str:
    language_key = language if language in {"ko", "en"} else _language_key(language)
    selected_agents = _selected_memory_agents(snapshot, agent_id)
    if not snapshot or not selected_agents:
        return LABELS[language_key]["memory_empty"]

    agent_id = selected_agents[0]
    memory = snapshot[agent_id]
    color_map = _agent_color_map(sorted(snapshot))
    agent_color = color_map.get(agent_id, "#0f172a")
    lines = [
        (
            "<div style="
            f"background:{agent_color}22;border-left:4px solid {agent_color};"
            "padding:8px 12px;margin:0 0 12px 0;border-radius:6px;"
            f'"><strong>{escape(agent_id)}</strong></div>'
        )
    ]
    if len(selected_agents) > 1:
        lines.append(f"> {LABELS[language_key]['memory_multi_hint']}")
    lines.extend(
        _memory_section_lines(
            LABELS[language_key]["memory_short_term"],
            list(memory.get("short_term", [])),
            language=language_key,
            section="short_term",
        )
    )
    lines.extend(
        _memory_section_lines(
            LABELS[language_key]["memory_long_term"],
            list(memory.get("long_term", [])),
            language=language_key,
            section="long_term",
        )
    )
    lines.extend(
        _memory_section_lines(
            LABELS[language_key]["memory_monologue"],
            list(memory.get("monologue", [])),
            language=language_key,
            section="monologue",
        )
    )
    return "\n".join(lines)


def _selected_memory_agents(
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    agent_id: str | list[str] | None,
) -> list[str]:
    if isinstance(agent_id, list):
        requested = [str(value) for value in agent_id]
    elif agent_id:
        requested = [str(agent_id)]
    else:
        requested = []

    selected = [
        value
        for value in requested
        if value in snapshot
    ]
    if not selected and snapshot:
        return [sorted(snapshot)[0]]
    return selected


def _memory_inspector_views(
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    agent_id: str | list[str] | None,
    language: str = "en",
) -> tuple[str, go.Figure]:
    language_key = language if language in {"ko", "en"} else _language_key(language)
    selected_agents = _selected_memory_agents(snapshot, agent_id)
    return (
        _memory_inspector_markdown(snapshot, selected_agents, language=language_key),
        _emotion_trajectory_figure(snapshot, selected_agents, language=language_key),
    )


def _emotion_trajectory_figure(
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    agent_id: str | list[str] | None,
    *,
    language: str = "en",
) -> go.Figure:
    language_key = language if language in {"ko", "en"} else _language_key(language)
    selected_agents = _selected_memory_agents(snapshot, agent_id)[:EMOTION_TRAJECTORY_MAX_AGENTS]
    title = LABELS[language_key]["memory_emotion"]
    tick_label = "Tick"
    valence_label = "Valence"
    arousal_label = "Arousal / Dominance"
    empty_text = LABELS[language_key]["memory_emotion_empty"]
    if language_key == "ko":
        tick_label = "틱"
        valence_label = "Valence"
        arousal_label = "Arousal / Dominance"

    if not selected_agents:
        figure = go.Figure()
        figure.update_layout(
            title=title,
            height=160,
            margin={"l": 0, "r": 0, "t": 48, "b": 0},
            annotations=[{"text": empty_text, "showarrow": False}],
            paper_bgcolor="rgba(248,250,252,1)",
            plot_bgcolor="rgba(248,250,252,1)",
        )
        return figure

    figure = make_subplots(
        rows=len(selected_agents),
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=selected_agents,
        specs=[[{"secondary_y": True}] for _ in selected_agents],
    )
    trace_colors = {
        "valence": "#16a34a",
        "arousal": "#f97316",
        "dominance": "#2563eb",
    }
    for row_index, selected_agent in enumerate(selected_agents, start=1):
        emotion_series = list(snapshot.get(selected_agent, {}).get("emotion", []))
        ticks = [int(entry.get("tick", -1)) for entry in emotion_series]
        figure.add_trace(
            go.Scatter(
                x=ticks,
                y=[float(entry.get("valence", 0.0)) for entry in emotion_series],
                mode="lines+markers",
                name="Valence",
                legendgroup="valence",
                showlegend=row_index == 1,
                line={"color": trace_colors["valence"], "width": 2},
            ),
            row=row_index,
            col=1,
            secondary_y=False,
        )
        figure.add_trace(
            go.Scatter(
                x=ticks,
                y=[float(entry.get("arousal", 0.0)) for entry in emotion_series],
                mode="lines+markers",
                name="Arousal",
                legendgroup="arousal",
                showlegend=row_index == 1,
                line={"color": trace_colors["arousal"], "width": 2},
            ),
            row=row_index,
            col=1,
            secondary_y=True,
        )
        figure.add_trace(
            go.Scatter(
                x=ticks,
                y=[float(entry.get("dominance", 0.0)) for entry in emotion_series],
                mode="lines+markers",
                name="Dominance",
                legendgroup="dominance",
                showlegend=row_index == 1,
                line={"color": trace_colors["dominance"], "width": 2, "dash": "dot"},
            ),
            row=row_index,
            col=1,
            secondary_y=True,
        )
        figure.update_yaxes(
            range=[-1, 1],
            title_text=valence_label,
            row=row_index,
            col=1,
            secondary_y=False,
        )
        figure.update_yaxes(
            range=[0, 1],
            title_text=arousal_label,
            row=row_index,
            col=1,
            secondary_y=True,
        )
        figure.update_xaxes(
            title_text=tick_label if row_index == len(selected_agents) else None,
            row=row_index,
            col=1,
        )

    figure.update_layout(
        title=title,
        height=max(180, 120 * len(selected_agents)),
        margin={"l": 0, "r": 0, "t": 64, "b": 0},
        legend={"orientation": "h", "y": 1.08},
        paper_bgcolor="rgba(248,250,252,1)",
        plot_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _spatial_heatmap_figure(
    jsonl_text: str,
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    language: str = "en",
) -> go.Figure:
    title = LABELS[language]["spatial_heatmap"]
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    if not rows:
        return _spatial_heatmap_empty_figure(title, LABELS[language]["spatial_heatmap_empty"])
    if any("record_type" in row for row in rows):
        return _spatial_heatmap_empty_figure(title, LABELS[language]["spatial_heatmap_batch"])

    valence_by_tick: dict[tuple[str, int], float] = {}
    for agent_id, memory in snapshot.items():
        for entry in list(memory.get("emotion", [])):
            valence_by_tick[(agent_id, int(entry.get("tick", -1)))] = float(
                entry.get("valence", 0.0)
            )

    root_label = "Simulation world" if language == "en" else "시뮬레이션 세계"
    dominant_labels = {
        "positive": "Positive" if language == "en" else "긍정",
        "neutral": "Neutral" if language == "en" else "중립",
        "negative": "Negative" if language == "en" else "부정",
    }
    aggregate: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        action = row.get("action")
        if not isinstance(action, dict):
            continue
        raw_location = str(action.get("location") or "").strip()
        segments = [segment.strip() for segment in raw_location.split(" > ") if segment.strip()]
        if not segments:
            segments = ["Unknown" if language == "en" else "미상 위치"]
        path = [root_label, *segments]
        agent_id = str(row.get("agent_id", "agent"))
        tick = int(row.get("tick", -1))
        valence = valence_by_tick.get((agent_id, tick), 0.0)
        emotion_key = "positive" if valence > 0.2 else "negative" if valence < -0.2 else "neutral"
        for depth in range(1, len(path) + 1):
            key = tuple(path[:depth])
            bucket = aggregate.setdefault(
                key,
                {
                    "count": 0,
                    "valence_total": 0.0,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0,
                },
            )
            bucket["count"] = int(bucket["count"]) + 1
            bucket["valence_total"] = float(bucket["valence_total"]) + valence
            bucket[emotion_key] = int(bucket[emotion_key]) + 1

    if not aggregate:
        return _spatial_heatmap_empty_figure(title, LABELS[language]["spatial_heatmap_empty"])

    ids: list[str] = []
    labels: list[str] = []
    parents: list[str] = []
    values: list[int] = []
    colors: list[float] = []
    customdata: list[list[Any]] = []
    for path in sorted(aggregate, key=lambda value: (len(value), value)):
        bucket = aggregate[path]
        dominant_emotion = max(
            ("positive", "neutral", "negative"),
            key=lambda key: (int(bucket[key]), key),
        )
        ids.append(" / ".join(path))
        labels.append(path[-1])
        parents.append("" if len(path) == 1 else " / ".join(path[:-1]))
        values.append(int(bucket["count"]))
        colors.append(float(bucket["valence_total"]) / max(1, int(bucket["count"])))
        customdata.append([int(bucket["count"]), dominant_labels[dominant_emotion]])

    tick_label = "Total tick count" if language == "en" else "총 틱 수"
    emotion_label = "Dominant emotion" if language == "en" else "우세 정서"
    figure = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            customdata=customdata,
            marker={
                "colors": colors,
                "colorscale": "RdYlGn",
                "cmin": -1,
                "cmax": 1,
                "showscale": True,
                "colorbar": {"title": "Valence"},
            },
            hovertemplate=(
                "%{label}<br>"
                + f"{tick_label}: "
                + "%{customdata[0]}<br>"
                + f"{emotion_label}: "
                + "%{customdata[1]}<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title=title,
        height=380,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        paper_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _spatial_heatmap_empty_figure(title: str, message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title,
        height=220,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        annotations=[{"text": message, "showarrow": False}],
        paper_bgcolor="rgba(248,250,252,1)",
        plot_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _fairness_empty_figure(title: str, message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title,
        height=360,
        margin={"l": 0, "r": 0, "t": 52, "b": 0},
        annotations=[{"text": message, "showarrow": False}],
        paper_bgcolor="rgba(248,250,252,1)",
        plot_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _fairness_heatmap_figure(report: FairnessAuditReport, *, language: str = "en") -> go.Figure:
    title = LABELS[language]["fairness_plot"]
    if not report.cells:
        return _fairness_empty_figure(title, LABELS[language]["fairness_empty"])

    cell_map = {
        (cell.trait, cell.action_type): cell
        for cell in report.cells
    }
    x_labels = [action_type.replace("_", "<br>") for action_type in report.action_types]
    y_labels = [_trait_axis_label(trait_name, language) for trait_name in report.trait_names]
    z_values: list[list[float]] = []
    hover_text: list[list[str]] = []
    annotations: list[dict[str, Any]] = []
    max_abs = max((abs(cell.signed_effect_size) for cell in report.cells), default=0.0)
    z_limit = max(0.25, round(max_abs + 0.05, 3))

    for row_index, trait_name in enumerate(report.trait_names):
        z_row: list[float] = []
        hover_row: list[str] = []
        for column_index, action_type in enumerate(report.action_types):
            cell = cell_map[(trait_name, action_type)]
            z_row.append(cell.signed_effect_size)
            q_value = _format_p_value(cell.p_adjusted)
            hover_row.append(
                "<br>".join(
                    [
                        f"Trait: {_trait_text_label(trait_name, language)}",
                        f"Action: {action_type}",
                        f"Signed Cohen's w: {_format_stat(cell.signed_effect_size)}",
                        f"High P(action): {_format_stat(cell.high_probability)}",
                        f"Low P(action): {_format_stat(cell.low_probability)}",
                        f"BH q-value: {q_value}",
                    ]
                )
            )
            if not math.isnan(cell.p_adjusted) and cell.p_adjusted < 0.001:
                annotations.append(
                    {
                        "x": x_labels[column_index],
                        "y": y_labels[row_index],
                        "text": "*",
                        "showarrow": False,
                        "font": {"size": 15, "color": "#111827"},
                    }
                )
        z_values.append(z_row)
        hover_text.append(hover_row)

    figure = go.Figure(
        data=[
            go.Heatmap(
                z=z_values,
                x=x_labels,
                y=y_labels,
                colorscale="RdBu",
                zmid=0.0,
                zmin=-z_limit,
                zmax=z_limit,
                hovertext=hover_text,
                hovertemplate="%{hovertext}<extra></extra>",
                colorbar={"title": "signed w"},
            )
        ]
    )
    figure.update_layout(
        title=title,
        height=420,
        margin={"l": 0, "r": 0, "t": 52, "b": 0},
        annotations=annotations,
        paper_bgcolor="rgba(255,255,255,1)",
        plot_bgcolor="rgba(255,255,255,1)",
    )
    figure.update_xaxes(title_text="Action type")
    figure.update_yaxes(title_text="Trait")
    return figure


def _fairness_summary_markdown(report: FairnessAuditReport, *, language: str = "en") -> str:
    if not report.cells or report.included_events <= 0:
        return LABELS[language]["fairness_empty"]

    source_label = "action log" if report.event_source == "action_log" else "batch agent summary"
    top_cells = report.top_cells(limit=10)
    if language == "ko":
        lines = [
            "### 공정성 / 편향 감사",
            (
                f"- 분석 액션 이벤트: {report.included_events}/{report.total_events}"
                f" | source: {source_label}"
            ),
            "- trait split: 각 trait에서 에이전트를 상/하위 절반으로 나눠 조건부 행동 확률을 비교했습니다.",
            "- 다중비교 보정: Benjamini-Hochberg FDR",
            "- 히트맵 별표: q < 0.001",
            "- 상위 편향 신호 10개:",
        ]
        if not top_cells:
            lines.append("- 검토할 trait-action 신호가 아직 없습니다.")
            return "\n".join(lines)
        for cell in top_cells:
            lines.append(
                f"- {_trait_text_label(cell.trait, language)} -> {cell.action_type}: "
                f"high {cell.high_probability:.3f} vs low {cell.low_probability:.3f} | "
                f"Δ={cell.high_probability - cell.low_probability:+.3f} | "
                f"w={cell.effect_size:.3f} | q={_format_p_value(cell.p_adjusted)}"
            )
        return "\n".join(lines)

    lines = [
        "### Bias audit",
        (
            f"- Audited action events: {report.included_events}/{report.total_events}"
            f" | source: {source_label}"
        ),
        "- Trait split: agents are divided into lower and upper halves per trait before comparing conditional action probabilities.",
        "- Multiple-testing correction: Benjamini-Hochberg FDR",
        "- Heatmap star threshold: q < 0.001",
        "- Top 10 bias signals:",
    ]
    if not top_cells:
        lines.append("- No trait-action signals are available yet.")
        return "\n".join(lines)
    for cell in top_cells:
        lines.append(
            f"- {_trait_text_label(cell.trait, language)} -> {cell.action_type}: "
            f"high {cell.high_probability:.3f} vs low {cell.low_probability:.3f} | "
            f"delta={cell.high_probability - cell.low_probability:+.3f} | "
            f"w={cell.effect_size:.3f} | q={_format_p_value(cell.p_adjusted)}"
        )
    return "\n".join(lines)


def _fairness_agent_trait_map(request: dict[str, Any]) -> dict[str, dict[str, float]]:
    artifacts = _prepare_playground_run(
        scenario_name=str(request["scenario_name"]),
        provider="Replay only",
        api_key="",
        model="",
        primary_name=str(request["primary_name"]),
        primary_age=int(request["primary_age"]),
        openness=float(dict(request["personality_overrides"])["openness"]),
        conscientiousness=float(dict(request["personality_overrides"])["conscientiousness"]),
        extraversion=float(dict(request["personality_overrides"])["extraversion"]),
        agreeableness=float(dict(request["personality_overrides"])["agreeableness"]),
        neuroticism=float(dict(request["personality_overrides"])["neuroticism"]),
        personality_overrides=dict(request["personality_overrides"]),
        agent_count=int(request["agent_count"]),
        environment_preset_id=cast("str | None", request["environment_preset_id"]),
        cultural_prior_id=cast("str | None", request["cultural_prior_id"]),
        agent_overrides=cast("list[dict[str, Any]]", request["agent_overrides"]),
        primary_planning_enabled=bool(request["primary_planning_enabled"]),
        planning_depth=int(request["planning_depth"]),
        language=str(request["language"]),
        seed=int(request["master_seed"]) if bool(request["batch_mode"]) else None,
        event_injections_text=str(request["event_injections_text"]),
        initial_relationships_text=str(request["initial_relationships_text"]),
    )
    try:
        return {
            agent.agent_id: {
                field_name: float(agent.personality.to_dict().get(field_name, 0.0))
                for field_name in PERSONA_TRAIT_FIELDS
            }
            for agent in artifacts.agents
        }
    finally:
        artifacts.simulator.close()


def _fairness_audit_outputs(
    jsonl_text: str,
    scenario_name: str,
    environment_preset_id: str | None,
    cultural_prior_id: str | None,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    *trait_and_runtime: Any,
) -> tuple[go.Figure, str]:
    request = _resolve_run_request(
        scenario_name,
        environment_preset_id,
        cultural_prior_id,
        provider,
        api_key,
        model,
        primary_name,
        primary_age,
        *trait_and_runtime,
    )
    language = _language_key(str(request["language"]))
    if not _jsonl_rows(jsonl_text):
        return (
            _fairness_empty_figure(LABELS[language]["fairness_plot"], LABELS[language]["fairness_empty"]),
            LABELS[language]["fairness_empty"],
        )
    try:
        report = audit_trait_action_fairness(jsonl_text, _fairness_agent_trait_map(request))
    except Exception as exc:
        message = (
            f"공정성 감사 생성 실패: {exc}"
            if language == "ko"
            else f"Bias audit failed: {exc}"
        )
        return _fairness_empty_figure(LABELS[language]["fairness_plot"], message), message
    return (
        _fairness_heatmap_figure(report, language=language),
        _fairness_summary_markdown(report, language=language),
    )


def _action_flow_figure(jsonl_text: str, *, language: str = "en") -> go.Figure:
    title = LABELS[language]["action_flow"]
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    if not rows:
        return _action_flow_empty_figure(title, LABELS[language]["action_flow_empty"])
    if any("record_type" in row for row in rows):
        return _action_flow_empty_figure(title, LABELS[language]["action_flow_batch"])

    pair_counts: dict[tuple[str, str], dict[str, int]] = {}
    source_agents: set[str] = set()
    target_nodes: set[str] = set()
    for row in rows:
        action = row.get("action")
        if not isinstance(action, dict):
            continue
        source = str(row.get("agent_id", "agent"))
        action_type = str(action.get("action_type", "")).strip() or "observe"
        raw_target = str(action.get("target") or "").strip()
        if raw_target:
            target = raw_target
        elif action_type in ACTION_FLOW_SELF_TYPES:
            suffix = "(self)" if language == "en" else "(자기)"
            target = f"{source} {suffix}"
        else:
            suffix = "(context)" if language == "en" else "(맥락)"
            target = f"{source} {suffix}"
        source_agents.add(source)
        target_nodes.add(target)
        bucket = pair_counts.setdefault((source, target), {})
        bucket[action_type] = bucket.get(action_type, 0) + 1

    if not pair_counts:
        return _action_flow_empty_figure(title, LABELS[language]["action_flow_empty"])

    ordered_sources = sorted(source_agents)
    ordered_targets = sorted(target_nodes)
    agent_colors = _agent_color_map(ordered_sources)
    action_palette = _action_type_palette(
        action_type
        for counts in pair_counts.values()
        for action_type in counts
    )
    node_labels = ordered_sources + ordered_targets
    node_colors = [agent_colors[source] for source in ordered_sources]
    for target in ordered_targets:
        base_agent = target.replace(" (self)", "").replace(" (context)", "").replace(" (자기)", "").replace(" (맥락)", "")
        node_colors.append(agent_colors.get(base_agent, "#94a3b8"))

    source_index = {agent_id: index for index, agent_id in enumerate(ordered_sources)}
    target_index = {
        target: len(ordered_sources) + index for index, target in enumerate(ordered_targets)
    }
    link_sources: list[int] = []
    link_targets: list[int] = []
    link_values: list[int] = []
    link_colors: list[str] = []
    link_customdata: list[str] = []
    count_label = "Count" if language == "en" else "횟수"
    for source, target in sorted(pair_counts):
        counts = pair_counts[(source, target)]
        dominant_action = max(counts.items(), key=lambda item: (int(item[1]), item[0]))[0]
        link_sources.append(source_index[source])
        link_targets.append(target_index[target])
        link_values.append(sum(int(count) for count in counts.values()))
        link_colors.append(action_palette[dominant_action])
        breakdown = ", ".join(
            f"{action_type} x{count}"
            for action_type, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )
        link_customdata.append(f"{count_label}: {sum(int(count) for count in counts.values())}<br>{breakdown}")

    figure = go.Figure(
        go.Sankey(
            arrangement="snap",
            node={
                "label": node_labels,
                "color": node_colors,
                "pad": 16,
                "thickness": 16,
            },
            link={
                "source": link_sources,
                "target": link_targets,
                "value": link_values,
                "color": link_colors,
                "customdata": link_customdata,
                "hovertemplate": "%{source.label} → %{target.label}<br>%{customdata}<extra></extra>",
            },
        )
    )
    figure.update_layout(
        title=title,
        height=420,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        paper_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _action_type_palette(action_types: Any) -> dict[str, str]:
    ordered_action_types = sorted({str(action_type) for action_type in action_types})
    return {
        action_type: ACTION_FLOW_COLOR_SEQUENCE[index % len(ACTION_FLOW_COLOR_SEQUENCE)]
        for index, action_type in enumerate(ordered_action_types)
    }


def _action_flow_empty_figure(title: str, message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title,
        height=220,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        annotations=[{"text": message, "showarrow": False}],
        paper_bgcolor="rgba(248,250,252,1)",
        plot_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _mini_map_figure(jsonl_text: str, tick: int, language: str = "en") -> go.Figure:
    title = LABELS[language]["mini_map"]
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    if not rows:
        return _mini_map_empty_figure(title, LABELS[language]["mini_map_empty"])
    if any("record_type" in row for row in rows):
        return _mini_map_empty_figure(title, LABELS[language]["mini_map_batch"])

    log_rows = [
        row
        for row in rows
        if "tick" in row and isinstance(row.get("action"), dict)
    ]
    if not log_rows:
        return _mini_map_empty_figure(title, LABELS[language]["mini_map_empty"])

    unique_locations = sorted(
        {
            str(row["action"].get("location") or "").strip()
            for row in log_rows
            if str(row["action"].get("location") or "").strip()
        }
    )
    if not unique_locations:
        return _mini_map_empty_figure(title, LABELS[language]["mini_map_empty"])

    column_count = max(1, int(len(unique_locations) ** 0.5))
    if column_count * column_count < len(unique_locations):
        column_count += 1
    location_positions = {
        location: (index % column_count, -(index // column_count))
        for index, location in enumerate(unique_locations)
    }
    selected_tick = max(int(row["tick"]) for row in log_rows) if tick < 0 else int(tick)
    latest_by_agent: dict[str, dict[str, Any]] = {}
    for row in log_rows:
        row_tick = int(row["tick"])
        if row_tick > selected_tick:
            continue
        latest_by_agent[str(row.get("agent_id", "agent"))] = row

    if not latest_by_agent:
        return _mini_map_empty_figure(title, LABELS[language]["mini_map_empty"])

    agent_colors = _agent_color_map(sorted(latest_by_agent))
    occupant_slots: dict[str, list[str]] = {}
    for agent_id, row in latest_by_agent.items():
        location = str(row["action"].get("location") or "").strip()
        occupant_slots.setdefault(location, []).append(agent_id)

    x_values: list[float] = []
    y_values: list[float] = []
    marker_colors: list[str] = []
    labels: list[str] = []
    hover_text: list[str] = []
    for agent_id in sorted(latest_by_agent):
        row = latest_by_agent[agent_id]
        location = str(row["action"].get("location") or "").strip()
        base_x, base_y = location_positions.get(location, (0, 0))
        occupants = sorted(occupant_slots.get(location, [agent_id]))
        slot_index = occupants.index(agent_id)
        offset_x = ((slot_index % 3) - 1) * 0.18
        offset_y = ((slot_index // 3) * -0.18) + 0.18
        x_values.append(base_x + offset_x)
        y_values.append(base_y + offset_y)
        marker_colors.append(agent_colors[agent_id])
        labels.append(agent_id)
        hover_text.append(f"{agent_id}<br>{location}")

    figure = go.Figure()
    figure.add_scatter(
        x=x_values,
        y=y_values,
        mode="markers+text",
        text=labels,
        textposition="top center",
        hovertext=hover_text,
        hoverinfo="text",
        marker={"size": 16, "color": marker_colors, "line": {"width": 1, "color": "#0f172a"}},
        name="agents",
    )
    for location, (base_x, base_y) in location_positions.items():
        figure.add_shape(
            type="rect",
            x0=base_x - 0.45,
            x1=base_x + 0.45,
            y0=base_y - 0.45,
            y1=base_y + 0.45,
            line={"color": "#94a3b8", "width": 1},
            fillcolor="rgba(241,245,249,0.9)",
        )
        figure.add_annotation(
            x=base_x,
            y=base_y - 0.5,
            text=escape(location.split(" > ")[-1]),
            showarrow=False,
            font={"size": 10, "color": "#475569"},
        )

    figure.update_layout(
        title=title,
        height=320,
        margin={"l": 0, "r": 0, "t": 48, "b": 8},
        xaxis={"visible": False},
        yaxis={"visible": False, "scaleanchor": "x", "scaleratio": 1},
        plot_bgcolor="rgba(248,250,252,1)",
        paper_bgcolor="rgba(248,250,252,1)",
        showlegend=False,
    )
    return figure


def _mini_map_empty_figure(title: str, message: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title,
        height=220,
        margin={"l": 0, "r": 0, "t": 48, "b": 0},
        annotations=[{"text": message, "showarrow": False}],
        paper_bgcolor="rgba(248,250,252,1)",
        plot_bgcolor="rgba(248,250,252,1)",
    )
    return figure


def _memory_section_lines(
    title: str,
    entries: list[dict[str, Any]],
    *,
    language: str,
    section: str,
) -> list[str]:
    empty_key = {
        "short_term": "memory_short_term_empty",
        "long_term": "memory_long_term_empty",
        "monologue": "memory_monologue_empty",
    }[section]
    lines = [f"#### {title}"]
    if not entries:
        lines.append(f"- {LABELS[language][empty_key]}")
        return lines

    for entry in entries:
        timestamp = escape(str(entry.get("timestamp", "")))
        if section == "short_term":
            memory_type = escape(str(entry.get("memory_type", "episodic")))
            content = escape(str(entry.get("content", "")).strip())
            lines.append(f"- `{timestamp}` [{memory_type}] {content}")
            continue
        if section == "long_term":
            score = float(entry.get("score", 0.0))
            content = escape(str(entry.get("content", "")).strip())
            lines.append(f"- `{timestamp}` (score {score:.3f}) {content}")
            continue
        tick = int(entry.get("tick", -1))
        valence = float(entry.get("valence", 0.0))
        color = "#15803d" if valence > 0.2 else "#b91c1c" if valence < -0.2 else "#64748b"
        text = escape(str(entry.get("text", "")).strip())
        lines.append(
            f"- <span style=\"color:{color}\"><strong>{escape(f't{tick}')}</strong> `{timestamp}` {text}</span>"
        )
    return lines


def _single_run_tick_focus_markdown(
    rows: list[dict[str, Any]],
    tick: int,
    *,
    language: str = "en",
) -> str:
    log_rows = [
        row
        for row in rows
        if "tick" in row and isinstance(row.get("action"), dict)
    ]
    if not log_rows:
        return LABELS[language]["tick_focus_empty"]

    if tick < 0:
        action_counts: dict[str, int] = {}
        for row in log_rows:
            action_type = str(row["action"].get("action_type", "")).strip()
            if not action_type:
                continue
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        tick_count = len({int(row["tick"]) for row in log_rows})
        title = "### 전체 틱 요약" if language == "ko" else "### All ticks summary"
        tick_label = "틱 수" if language == "ko" else "Ticks"
        event_label = "이벤트 수" if language == "ko" else "Events"
        action_label = "주요 행동" if language == "ko" else "Top actions"
        return "\n".join(
            [
                title,
                f"- **{tick_label}:** {tick_count}",
                f"- **{event_label}:** {len(log_rows)}",
                f"- **{action_label}:** {_top_action_counts_text(action_counts)}",
            ]
        )

    tick_rows = [row for row in log_rows if int(row["tick"]) == int(tick)]
    if not tick_rows:
        return (
            f"### 틱 {tick}\n- 아직 기록된 이벤트가 없습니다."
            if language == "ko"
            else f"### Tick {tick}\n- No events recorded."
        )
    title = f"### 틱 {tick}" if language == "ko" else f"### Tick {tick}"
    lines = [title]
    for row in tick_rows:
        action = row["action"]
        agent_id = str(row.get("agent_id", "agent"))
        action_type = str(action.get("action_type", "act"))
        target = str(action.get("target") or ("전체" if language == "ko" else "group"))
        content = str(action.get("content", "")).strip()
        lines.append(f"- **{agent_id}** `{action_type}` -> {target}: {content}")
    return "\n".join(lines)


def _batch_tick_focus_markdown(
    rows: list[dict[str, Any]],
    tick: int,
    *,
    language: str = "en",
) -> str:
    tick_rows = [row for row in rows if row.get("record_type") == "tick_stat"]
    if not tick_rows:
        return LABELS[language]["tick_focus_empty"]
    if tick < 0:
        title = "### 전체 틱 요약" if language == "ko" else "### All ticks summary"
        tick_label = "집계 틱" if language == "ko" else "Aggregated ticks"
        action_label = "주요 행동" if language == "ko" else "Top actions"
        aggregate_counts: dict[str, int] = {}
        for row in tick_rows:
            for action_type, count in dict(row.get("action_type_counts", {})).items():
                aggregate_counts[str(action_type)] = aggregate_counts.get(str(action_type), 0) + int(
                    count
                )
        return "\n".join(
            [
                title,
                f"- **{tick_label}:** {len(tick_rows)}",
                f"- **{action_label}:** {_top_action_counts_text(aggregate_counts)}",
            ]
        )

    selected = next((row for row in tick_rows if int(row.get("tick", -999)) == int(tick)), None)
    if selected is None:
        return (
            f"### 틱 {tick}\n- 아직 집계된 결과가 없습니다."
            if language == "ko"
            else f"### Tick {tick}\n- No aggregate data recorded."
        )
    title = f"### 틱 {tick}" if language == "ko" else f"### Tick {tick}"
    mean_label = "평균 행동 수" if language == "ko" else "Mean actions"
    action_label = "주요 행동" if language == "ko" else "Top actions"
    return "\n".join(
        [
            title,
            f"- **{mean_label}:** {float(selected.get('mean_actions', 0.0)):.1f}",
            f"- **{action_label}:** {_top_action_counts_text(dict(selected.get('action_type_counts', {})))}",
        ]
    )


def _timeline_markdown_with_agent_colors(
    jsonl_text: str,
    fallback_markdown: str,
    agent_colors: dict[str, str],
    *,
    language: str = "en",
) -> str:
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    if not rows or any("record_type" in row for row in rows):
        return fallback_markdown

    header = "### 타임라인" if language == "ko" else "### Timeline"
    tick_label = "틱" if language == "ko" else "Tick"
    lines = [header]
    for row in rows[:80]:
        if "tick" not in row or not isinstance(row.get("action"), dict):
            continue
        action = row["action"]
        agent_id = str(row.get("agent_id", "agent"))
        target = str(action.get("target") or "").strip()
        target_text = f" -> {escape(target)}" if target else ""
        color = agent_colors.get(agent_id, "#0f172a")
        timestamp = escape(str(row.get("timestamp", "")))
        content = escape(str(action.get("content", "")).strip())
        lines.append(
            f"- **{tick_label} {int(row['tick']):02d}** `{timestamp}` "
            f"<span style=\"color:{color}\">●</span> "
            f"**{escape(agent_id)}{target_text}**: {content}"
        )
    return "\n".join(lines)


def _conversation_threads_markdown(
    jsonl_text: str,
    memory_snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    agent_colors: dict[str, str],
    *,
    language: str = "en",
) -> str:
    rows: list[dict[str, Any]] = []
    for line in str(jsonl_text).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    if not rows:
        return LABELS[language]["threads_empty"]
    if any("record_type" in row for row in rows):
        return LABELS[language]["threads_batch"]

    speak_rows = [
        row
        for row in rows
        if isinstance(row.get("action"), dict)
        and str(row["action"].get("action_type", "")).strip() == "speak"
        and str(row["action"].get("target") or "").strip()
    ]
    if not speak_rows:
        return LABELS[language]["threads_empty"]

    valence_by_tick: dict[tuple[str, int], float] = {}
    for agent_id, memory in memory_snapshot.items():
        for monologue in list(memory.get("monologue", [])):
            valence_by_tick[(agent_id, int(monologue.get("tick", -1)))] = float(
                monologue.get("valence", 0.0)
            )

    threads: list[dict[str, Any]] = []
    for row in speak_rows:
        tick = int(row["tick"])
        agent_id = str(row.get("agent_id", "agent"))
        action = row["action"]
        target = str(action.get("target") or "").strip()
        content = str(action.get("content", "")).strip()
        timestamp = str(row.get("timestamp", ""))
        message = {
            "tick": tick,
            "agent_id": agent_id,
            "target": target,
            "content": content,
            "timestamp": timestamp,
            "depth": 0,
        }

        thread: dict[str, Any] | None = None
        for candidate in reversed(threads):
            participants = set(candidate["participants"])
            last_message = candidate["messages"][-1]
            if tick - int(last_message["tick"]) > 5:
                continue
            if {agent_id, target}.issubset(participants):
                thread = candidate
                break

        if thread is None:
            threads.append(
                {
                    "participants": [agent_id, target],
                    "topic": _thread_topic(content),
                    "messages": [message],
                }
            )
            continue

        last_message = thread["messages"][-1]
        if (
            agent_id == str(last_message["target"])
            and target == str(last_message["agent_id"])
            and tick - int(last_message["tick"]) <= 3
        ):
            message["depth"] = int(last_message["depth"]) + 1
        thread["participants"] = sorted(set(thread["participants"]) | {agent_id, target})
        thread["messages"].append(message)

    if not threads:
        return LABELS[language]["threads_empty"]

    cards: list[str] = []
    for index, thread in enumerate(threads, start=1):
        participants = list(thread["participants"])
        header = " ↔ ".join(escape(participant) for participant in participants)
        topic = escape(str(thread["topic"]))
        body_lines: list[str] = []
        ticks_in_thread = {int(message["tick"]) for message in thread["messages"]}
        for message in thread["messages"]:
            color = agent_colors.get(str(message["agent_id"]), "#0f172a")
            indent_px = 16 * int(message["depth"])
            body_lines.append(
                "<div style="
                f"margin-left:{indent_px}px;padding:8px 10px;border-left:2px solid {color};"
                "margin-bottom:8px;background:#ffffff;border-radius:6px;"
                '">'
                f'<div><span style="color:{color};font-weight:600">{escape(str(message["agent_id"]))}</span> '
                f'→ {escape(str(message["target"]))}</div>'
                f'<div style="color:#475569;font-size:12px">{escape(str(message["timestamp"]))}</div>'
                f"<div>{escape(str(message['content']))}</div>"
                "</div>"
            )

        reactions: list[str] = []
        for observer in sorted(agent_colors):
            if observer in participants:
                continue
            observer_valence = max(
                (valence_by_tick.get((observer, tick), 0.0) for tick in ticks_in_thread),
                default=0.0,
            )
            emoji = "🙂" if observer_valence > 0.2 else "😐" if observer_valence >= -0.2 else "🙁"
            reactions.append(f"{emoji} {escape(observer)}")
        footer = " ".join(reactions[:4]) if reactions else "😐"

        cards.append(
            "<div style="
            "border:1px solid rgba(148,163,184,0.55);border-radius:8px;padding:12px;"
            "background:#f8fafc;margin-bottom:12px;"
            '">'
            f"<div style=\"font-weight:600\">Thread {index}: {header}</div>"
            f"<div style=\"color:#475569;margin:4px 0 10px 0\">{topic}</div>"
            + "".join(body_lines)
            + f"<div style=\"color:#64748b;font-size:12px;margin-top:8px\">{footer}</div>"
            + "</div>"
        )
    return "\n".join(cards)


def _thread_topic(content: str) -> str:
    words = content.split()
    if not words:
        return "Untitled thread"
    snippet = " ".join(words[:6])
    return snippet if len(words) <= 6 else f"{snippet}..."


def _top_action_counts_text(action_counts: dict[str, int]) -> str:
    if not action_counts:
        return "none"
    ordered = sorted(action_counts.items(), key=lambda item: (-int(item[1]), item[0]))
    return ", ".join(f"{action_type} ({count})" for action_type, count in ordered[:3])


def _relationship_figure(
    rows: list[dict[str, Any]],
    *,
    language: str = "en",
    agent_colors: dict[str, str] | None = None,
) -> go.Figure:
    title = "관계 그래프" if language == "ko" else "Relationship graph"
    empty_msg = (
        "관계 엣지가 아직 없습니다. 틱을 더 늘리거나 대화형 시나리오를 사용해 보세요."
        if language == "ko"
        else "No relationship edges yet. Run more ticks or use a conversational scenario."
    )
    scene_layout = {
        "xaxis": {"visible": False, "showbackground": False},
        "yaxis": {"visible": False, "showbackground": False},
        "zaxis": {"visible": False, "showbackground": False},
        "bgcolor": "rgba(248,250,252,1)",
        "camera": {
            "eye": {"x": 1.25, "y": 1.25, "z": 0.85},
            "projection": {"type": "perspective"},
        },
        "aspectmode": "cube",
    }
    if not rows:
        figure = go.Figure()
        figure.update_layout(
            title=title,
            scene=scene_layout,
            annotations=[{"text": empty_msg, "showarrow": False}],
            height=GRAPH_HEIGHT_PX,
            margin={"l": 0, "r": 0, "t": 40, "b": 0},
        )
        return figure

    agents = sorted({str(row["source"]) for row in rows} | {str(row["target"]) for row in rows})
    color_map = agent_colors or _agent_color_map(agents)
    graph = _relationship_layout_graph(agents, rows)
    positions = _force_directed_positions(agents, rows)
    edge_weights = [_relationship_metric(row, "weight") for row in rows]
    edge_trusts = [_relationship_metric(row, "trust") for row in rows]
    node_degrees = dict(graph.degree())
    edge_traces: list[go.Scatter3d] = []
    for index, row in enumerate(rows):
        source = str(row["source"])
        target = str(row["target"])
        sx, sy, sz = positions[source]
        tx, ty, tz = positions[target]
        normalized_weight = _normalized_metric(edge_weights[index], edge_weights)
        normalized_trust = _normalized_metric(edge_trusts[index], edge_trusts)
        edge_alpha = 0.18 + 0.62 * normalized_trust
        edge_traces.append(
            go.Scatter3d(
                x=[sx, tx],
                y=[sy, ty],
                z=[sz, tz],
                mode="lines",
                line={
                    "width": 1.0 + 5.0 * normalized_weight,
                    "color": f"rgba(100,116,139,{edge_alpha:.3f})",
                },
                text=f"{source} -> {target} ({row.get('relationship_type', 'unknown')})",
                hovertemplate=(
                    "%{text}<br>trust="
                    + f"{_relationship_metric(row, 'trust'):.2f}"
                    + "<br>weight="
                    + f"{_relationship_metric(row, 'weight'):.2f}"
                    + "<extra></extra>"
                ),
                showlegend=False,
            )
        )

    node_x = [positions[agent][0] for agent in agents]
    node_y = [positions[agent][1] for agent in agents]
    node_z = [positions[agent][2] for agent in agents]
    node_text = list(agents)
    node_color = [color_map.get(agent, "#0f172a") for agent in agents]
    node_size = [min(30, 12 + int(node_degrees.get(agent, 0)) * 4) for agent in agents]

    figure = go.Figure(
        data=[
            *edge_traces,
            go.Scatter3d(
                x=node_x,
                y=node_y,
                z=node_z,
                mode="markers+text",
                text=node_text,
                textposition="bottom center",
                textfont={"color": "#0f172a", "size": 13, "family": "Inter, sans-serif"},
                marker={
                    "size": node_size,
                    "symbol": "circle",
                    "color": node_color,
                    "opacity": 0.95,
                    "line": {"width": 1.6, "color": "#0f172a"},
                },
                hovertext=_node_hover_text(agents, rows, language=language),
                hoverinfo="text",
                showlegend=False,
            ),
        ]
    )
    figure.update_layout(
        title=title,
        showlegend=False,
        scene=scene_layout,
        dragmode="orbit",
        height=GRAPH_HEIGHT_PX,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
    )
    return figure


def _relationship_metric(row: dict[str, Any], key: str) -> float:
    try:
        return float(row.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _normalized_metric(value: float, all_values: list[float]) -> float:
    if not all_values:
        return 0.5
    minimum = min(all_values)
    maximum = max(all_values)
    if math.isclose(minimum, maximum):
        return 0.5
    return max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))


def _relationship_layout_graph(agents: list[str], rows: list[dict[str, Any]]) -> Any:
    import networkx as nx

    graph = nx.Graph()
    graph.add_nodes_from(agents)
    for row in rows:
        source = str(row["source"])
        target = str(row["target"])
        weight = max(abs(_relationship_metric(row, "weight")), 0.05)
        if graph.has_edge(source, target):
            graph[source][target]["weight"] += weight
        else:
            graph.add_edge(source, target, weight=weight)
    return graph


def _force_directed_positions(
    agents: list[str],
    rows: list[dict[str, Any]],
) -> dict[str, tuple[float, float, float]]:
    import networkx as nx

    n = len(agents)
    if n == 0:
        return {}
    if n == 1:
        return {agents[0]: (0.0, 0.0, 0.0)}
    if n == 2:
        return {agents[0]: (0.0, 1.0, 0.0), agents[1]: (0.0, -1.0, 0.0)}

    graph = _relationship_layout_graph(agents, rows)
    optimal_distance = 1.35 / math.sqrt(n)
    raw_positions = nx.spring_layout(
        graph,
        dim=3,
        seed=42,
        k=optimal_distance,
        iterations=100,
        weight="weight",
    )
    centered_positions: dict[str, tuple[float, float, float]] = {
        agent: tuple(float(coord) for coord in raw_positions[agent])
        for agent in agents
    }
    center_x = sum(position[0] for position in centered_positions.values()) / n
    center_y = sum(position[1] for position in centered_positions.values()) / n
    center_z = sum(position[2] for position in centered_positions.values()) / n
    normalized_positions = {
        agent: (
            position[0] - center_x,
            position[1] - center_y,
            position[2] - center_z,
        )
        for agent, position in centered_positions.items()
    }
    scale = max(
        max(abs(axis_value) for axis_value in position)
        for position in normalized_positions.values()
    )
    if scale <= 1e-9:
        return _sphere_positions(agents)
    return {
        agent: (
            position[0] / scale,
            position[1] / scale,
            position[2] / scale,
        )
        for agent, position in normalized_positions.items()
    }


def _sphere_positions(agents: list[str]) -> dict[str, tuple[float, float, float]]:

    n = len(agents)
    if n == 0:
        return {}
    if n == 1:
        return {agents[0]: (0.0, 0.0, 0.0)}
    if n == 2:
        return {agents[0]: (0.0, 1.0, 0.0), agents[1]: (0.0, -1.0, 0.0)}
    positions: dict[str, tuple[float, float, float]] = {}
    phi = math.pi * (3.0 - math.sqrt(5.0))
    for index, agent in enumerate(agents):
        y = 1.0 - (index / (n - 1)) * 2.0
        radius = math.sqrt(max(0.0, 1.0 - y * y))
        theta = phi * index
        x = math.cos(theta) * radius
        z = math.sin(theta) * radius
        positions[agent] = (x, y, z)
    return positions


def _node_hover_text(
    agents: list[str],
    rows: list[dict[str, Any]],
    *,
    language: str = "en",
) -> list[str]:
    hover: list[str] = []
    no_edges_text = "나가는 관계 없음" if language == "ko" else "No outgoing relationships"
    for agent in agents:
        outgoing = [row for row in rows if row["source"] == agent]
        if not outgoing:
            hover.append(f"{agent}<br>{no_edges_text}")
            continue
        lines = [agent]
        for row in outgoing:
            lines.append(
                f"{row['target']}: trust={row['trust']}, weight={row['weight']}, type={row['relationship_type']}"
            )
        hover.append("<br>".join(lines))
    return hover


def build_app() -> gr.Blocks:
    labels = LABELS["ko"]
    default_scenario = _default_scenario_name()
    initial_agent_defaults = agent_editor_defaults(
        default_scenario,
        agent_count=scenario_default_agent_count(default_scenario),
        cultural_prior_id=None,
        language="ko",
    )
    initial_action_chart_figure = _action_chart_figure({}, language="ko")
    initial_relationship_graph_html = _relationship_graph_html([], language="ko")
    initial_trait_matrix_figure, initial_trait_matrix_summary = _trait_correlation_outputs("ko")
    prereg_defaults = _prereg_defaults("ko")
    power_defaults = _power_defaults()
    deposit_defaults = _deposit_defaults("ko")
    simulation_defaults = _simulation_template_defaults()

    with gr.Blocks(
        title="Knoema Playground",
        css=FOOTER_CSS,
        head=APP_HEAD,
        analytics_enabled=False,
    ) as demo:
        with gr.Row(elem_id="topbar-row"):
            language = gr.Radio(
                label=labels["lang"],
                choices=LANGUAGE_CHOICES,
                value=LANGUAGE_CHOICES[0],
                scale=0,
            )
            theme_mode = gr.Radio(
                label=labels["theme"],
                choices=_theme_choices("ko"),
                value="auto",
                info=labels["theme_info"],
                scale=0,
                elem_id="theme-mode-radio",
            )
            with gr.Column(scale=1, min_width=0):
                gr.HTML("<div></div>", padding=False)
            tutorial_button = gr.Button("?", elem_id="tutorial-button", scale=0, min_width=52)
            reviewer_mode = gr.Checkbox(
                label=labels["reviewer_mode"],
                value=False,
                visible=False,
                elem_id="reviewer-mode-toggle",
            )

        header = gr.Markdown(labels["header"])

        with gr.Row():
            scenario = gr.Dropdown(
                label=labels["scenario"],
                choices=_scenario_choices_with_gate(False, "ko"),
                value=default_scenario,
                elem_id="scenario-dropdown",
            )
            environment_preset = gr.Dropdown(
                label=labels["environment"],
                choices=_preset_choices("ko"),
                value=_default_environment_id(),
                info=labels["environment_info"],
                elem_id="environment-preset",
            )
            provider = gr.Radio(
                label=labels["mode"],
                choices=_provider_choices("ko"),
                value="Replay only",
                elem_id="mode-radio",
            )

        with gr.Row():
            api_key = gr.Textbox(
                label=labels["api_key"],
                type="password",
                placeholder=labels["api_key_ph"],
            )
            model = gr.Dropdown(
                label=labels["model"],
                choices=[
                    "gpt-5.4",
                    "gpt-5.4-mini",
                    "gpt-5",
                    "gpt-5-mini",
                    "gpt-4.1",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "o3-mini",
                    "claude-opus-4-7",
                    "claude-sonnet-4-6",
                    "claude-haiku-4-5-20251001",
                ],
                value="gpt-5.4-mini",
                allow_custom_value=True,
            )

        agent_panel = gr.Accordion(
            labels["agent_panel"],
            open=True,
            elem_id="personality-panel",
        )
        with agent_panel:
            cultural_prior = gr.Dropdown(
                label=labels["cultural_prior"],
                choices=_cultural_prior_choices("ko"),
                value="",
                info=labels["cultural_prior_info"],
                elem_id="cultural-prior-dropdown",
            )
            advanced_research_mode = gr.Checkbox(
                label=labels["advanced_research_mode"],
                value=False,
                elem_id="advanced-research-mode",
            )
            advanced_research_ack = gr.Checkbox(
                label=labels["advanced_research_ack"],
                value=False,
                elem_id="advanced-research-ack",
            )
            advanced_research_notice = gr.Markdown(
                labels["advanced_research_notice"],
                elem_id="advanced-research-notice",
            )
            advanced_research_status = gr.Markdown(
                labels["advanced_research_locked"],
                elem_id="advanced-research-status",
            )

            agent_tabs: list[dict[str, Any]] = []
            with gr.Tabs(elem_id="agent-editor-tabs"):
                for slot_index, defaults in enumerate(initial_agent_defaults):
                    agent_tabs.append(
                        _build_agent_editor_tab(
                            slot_index=slot_index,
                            labels=labels,
                            defaults=defaults,
                        )
                    )

            with gr.Row():
                agent_count = gr.Slider(
                    label=labels["agents"],
                    info=labels["agents_info"],
                    minimum=AGENT_COUNT_MIN,
                    maximum=AGENT_COUNT_MAX,
                    step=1,
                    value=scenario_default_agent_count(default_scenario),
                    elem_id="agent-count-slider",
                )
                ticks = gr.Slider(
                    label=labels["ticks"],
                    minimum=1,
                    maximum=24,
                    step=1,
                    value=4,
                )

            with gr.Row():
                htn_enabled = gr.Checkbox(
                    label=labels["htn_enabled"],
                    info=labels["htn_info"],
                    value=False,
                    elem_id="htn-enabled-checkbox",
                )
                planning_depth = gr.Slider(
                    label=labels["planning_depth"],
                    info=labels["planning_depth_info"],
                    minimum=2,
                    maximum=5,
                    step=1,
                    value=3,
                    elem_id="planning-depth-slider",
                )

        primary_name = agent_tabs[0]["name"]
        primary_age = agent_tabs[0]["age"]

        scenario_hint = gr.Markdown(
            _hint_markdown_update(
                default_scenario,
                LANGUAGE_CHOICES[0],
                _default_environment_id(),
            ),
            elem_classes=["knoema-hint"],
        )

        scenario_synthesis_panel = gr.Accordion(
            labels["scenario_synthesis_panel"],
            open=False,
            elem_id="scenario-synthesis-panel",
        )
        with scenario_synthesis_panel:
            scenario_synthesis_input = gr.Textbox(
                label=labels["scenario_synthesis_input"],
                placeholder=labels["scenario_synthesis_placeholder"],
                lines=3,
                elem_id="scenario-synthesis-input",
            )
            scenario_synthesis_button = gr.Button(
                labels["scenario_synthesis_button"],
                elem_id="scenario-synthesis-button",
            )
            scenario_synthesis_output = gr.Markdown(
                labels["scenario_synthesis_empty"],
                elem_id="scenario-synthesis-output",
            )

        community_gallery_panel = gr.Accordion(
            labels["community_gallery_panel"],
            open=False,
            elem_id="community-gallery-panel",
        )
        with community_gallery_panel:
            community_gallery_scenario = gr.Dropdown(
                label=labels["community_gallery_scenario"],
                choices=community_scenario_choices(),
                value=community_scenario_choices()[0][1],
                elem_id="community-gallery-scenario",
            )
            community_gallery_load = gr.Button(
                labels["community_gallery_load"],
                elem_id="community-gallery-load",
            )
            community_gallery_preview = gr.Markdown(
                community_gallery_markdown(community_scenario_choices()[0][1], "ko"),
                elem_id="community-gallery-preview",
            )

        with gr.Row():
            batch_mode = gr.Checkbox(
                label=labels["batch_mode"],
                info=labels["batch_mode_info"],
                value=False,
                elem_id="batch-mode-checkbox",
            )
            batch_runs = gr.Slider(
                label=labels["batch_runs"],
                info=labels["batch_runs_info"],
                minimum=1,
                maximum=100,
                step=1,
                value=10,
                interactive=False,
                elem_id="batch-runs-slider",
            )
            master_seed = gr.Number(
                label=labels["master_seed"],
                info=labels["master_seed_info"],
                value=20260419,
                precision=0,
                interactive=False,
                elem_id="master-seed-number",
            )
            live_streaming = gr.Checkbox(
                label=labels["live_streaming"],
                info=labels["live_streaming_info"],
                value=False,
                elem_id="live-streaming-checkbox",
            )
            run_button = gr.Button(labels["run"], variant="primary", elem_id="run-button")
        mirofish_panel = gr.Accordion(
            labels["mirofish_panel"],
            open=False,
            elem_id="mirofish-lab-panel",
        )
        with mirofish_panel:
            with gr.Row():
                seed_prompt = gr.Textbox(
                    label=labels["seed_prompt"],
                    placeholder=labels["seed_prompt_placeholder"],
                    lines=2,
                    elem_id="seed-prompt-input",
                )
                seed_prompt_apply = gr.Button(
                    labels["seed_prompt_apply"],
                    elem_id="seed-prompt-apply",
                )
            seed_prompt_summary = gr.Markdown(
                labels["seed_prompt_empty"],
                elem_id="seed-prompt-summary",
            )
            with gr.Row():
                event_injections = gr.Textbox(
                    label=labels["event_injections"],
                    placeholder=labels["event_injections_placeholder"],
                    lines=4,
                    value="",
                    elem_id="event-injections-input",
                )
                initial_relationships = gr.Textbox(
                    label=labels["initial_relationships"],
                    placeholder=labels["initial_relationships_placeholder"],
                    lines=4,
                    value="",
                    elem_id="initial-relationships-input",
                )
        player_session_state = gr.State(value=None)
        with gr.Column(visible=False, elem_id="player-mode-panel") as player_panel:
            player_status = gr.Markdown("", elem_id="player-status")
            player_stt_engine = gr.Dropdown(
                label=labels["player_stt_engine"],
                choices=stt_engine_choices("ko"),
                value="off",
                elem_id="player-stt-engine",
            )
            player_tts_engine = gr.Dropdown(
                label=labels["player_tts_engine"],
                choices=tts_engine_choices("ko"),
                value="off",
                elem_id="player-tts-engine",
            )
            player_voice_input = gr.Audio(
                label=labels["player_voice_input"],
                sources=["microphone", "upload"],
                type="filepath",
                elem_id="player-voice-input",
            )
            player_input = gr.Textbox(
                label=labels["player_input"],
                placeholder=labels["player_input_placeholder"],
                lines=2,
                elem_id="player-input",
            )
            player_submit = gr.Button(labels["player_submit"], elem_id="player-submit")
            player_voice_output = gr.Audio(
                label=labels["player_voice_output"],
                type="filepath",
                interactive=False,
                elem_id="player-voice-output",
            )
        summary = gr.Textbox(label=labels["summary"], interactive=False, elem_id="run-summary")
        action_chart = gr.Plot(
            label=labels["action_chart"],
            value=initial_action_chart_figure,
            elem_id="action-breakdown-chart",
        )
        graph = gr.HTML(
            initial_relationship_graph_html,
            label=labels["graph"],
            show_label=True,
            container=True,
            padding=False,
            elem_id="relationship-graph",
        )
        tick_scrubber = gr.Slider(
            label=labels["tick_scrubber"],
            minimum=-1,
            maximum=0,
            step=1,
            value=-1,
            interactive=True,
            elem_id="tick-scrubber",
        )
        tick_focus = gr.Markdown(
            labels["tick_focus_empty"],
            label=labels["tick_focus"],
            elem_id="tick-focus-panel",
        )
        with gr.Tabs(elem_id="narrative-tabs"):
            with gr.Tab(labels["timeline"], elem_id="timeline-tab") as timeline_tab:
                timeline = gr.Markdown(
                    label=labels["timeline"],
                    elem_id="timeline-panel",
                    min_height=TIMELINE_MAX_HEIGHT_PX,
                    max_height=TIMELINE_MAX_HEIGHT_PX,
                    container=True,
                )
            with gr.Tab(labels["threads_tab"], elem_id="conversation-threads-tab") as threads_tab:
                thread_view = gr.Markdown(
                    labels["threads_empty"],
                    elem_id="conversation-threads-panel",
                )
        memory_snapshot_state = gr.State({})
        memory_panel = gr.Accordion(
            labels["memory_inspector"],
            open=False,
            elem_id="memory-inspector-panel",
        )
        with memory_panel:
            inspector_agent = gr.Dropdown(
                label=labels["memory_agent"],
                choices=[],
                value=[],
                multiselect=True,
                interactive=False,
                elem_id="memory-inspector-agent",
            )
            memory_view = gr.Markdown(
                labels["memory_empty"],
                elem_id="memory-inspector-markdown",
            )
            emotion_view = gr.Plot(
                label=labels["memory_emotion"],
                value=_emotion_trajectory_figure({}, [], language="ko"),
                elem_id="emotion-trajectory-plot",
            )
        spatial_heatmap_panel = gr.Accordion(
            labels["spatial_heatmap_panel"],
            open=False,
            elem_id="spatial-heatmap-panel",
        )
        with spatial_heatmap_panel:
            spatial_heatmap_view = gr.Plot(
                label=labels["spatial_heatmap"],
                value=_spatial_heatmap_figure("", {}, language="ko"),
                elem_id="spatial-heatmap-treemap",
            )
        action_flow_panel = gr.Accordion(
            labels["action_flow_panel"],
            open=False,
            elem_id="action-flow-panel",
        )
        with action_flow_panel:
            action_flow_view = gr.Plot(
                label=labels["action_flow"],
                value=_action_flow_figure("", language="ko"),
                elem_id="action-flow-sankey",
            )
        mini_map_panel = gr.Accordion(
            labels["mini_map_panel"],
            open=False,
            elem_id="mini-map-panel",
        )
        with mini_map_panel:
            mini_map_view = gr.Plot(
                label=labels["mini_map"],
                value=_mini_map_figure("", -1, language="ko"),
                elem_id="mini-map-plot",
            )
        monologue_panel = gr.Accordion(
            labels["monologue_panel"],
            open=False,
            elem_id="inner-monologue-panel",
        )
        with monologue_panel:
            monologue_view = gr.Markdown(labels["monologue_empty"])
        current_plan_panel = gr.Accordion(
            labels["current_plan_panel"],
            open=False,
            elem_id="current-plan-panel",
        )
        with current_plan_panel:
            current_plan_view = gr.Markdown(labels["current_plan_empty"])
        trait_matrix_panel = gr.Accordion(
            labels["trait_matrix_panel"],
            open=False,
            elem_id="trait-correlation-panel",
        )
        with trait_matrix_panel:
            trait_matrix_plot = gr.Plot(
                label=labels["trait_matrix_plot"],
                value=initial_trait_matrix_figure,
                elem_id="trait-correlation-heatmap",
            )
            trait_matrix_summary = gr.Markdown(
                initial_trait_matrix_summary,
                elem_id="trait-correlation-summary",
            )
        statistics_panel = gr.Accordion(
            labels["statistics_panel"],
            open=False,
            elem_id="statistics-panel",
        )
        with statistics_panel:
            statistics_summary = gr.Markdown(
                _statistical_analysis_markdown("", "ko"),
                elem_id="statistics-summary",
            )
        fairness_panel = gr.Accordion(
            labels["fairness_panel"],
            open=False,
            elem_id="fairness-panel",
        )
        with fairness_panel:
            fairness_plot = gr.Plot(
                label=labels["fairness_plot"],
                value=_fairness_empty_figure(labels["fairness_plot"], labels["fairness_empty"]),
                elem_id="fairness-heatmap",
            )
            fairness_summary = gr.Markdown(
                labels["fairness_empty"],
                elem_id="fairness-summary",
            )
        prereg_panel = gr.Accordion(
            labels["prereg_panel"],
            open=False,
            elem_id="preregistration-panel",
        )
        with prereg_panel:
            prereg_template = gr.Dropdown(
                label=labels["prereg_template"],
                choices=prereg_template_choices("ko"),
                value="theory_of_mind_development",
                elem_id="prereg-template-picker",
            )
            prereg_title = gr.Textbox(
                label=labels["prereg_title"],
                value=prereg_defaults["title"],
                lines=1,
                elem_id="prereg-title",
            )
            prereg_hypotheses = gr.Textbox(
                label=labels["prereg_hypotheses"],
                value=prereg_defaults["hypotheses"],
                lines=4,
                elem_id="prereg-hypotheses",
            )
            prereg_design = gr.Textbox(
                label=labels["prereg_design"],
                value=prereg_defaults["design"],
                lines=3,
                elem_id="prereg-design",
            )
            prereg_data_generation = gr.Textbox(
                label=labels["prereg_data_generation"],
                value=simulation_defaults["data_generation"],
                lines=3,
                elem_id="prereg-data-generation",
            )
            prereg_factor_design = gr.Textbox(
                label=labels["prereg_factor_design"],
                value=simulation_defaults["factor_design"],
                lines=3,
                elem_id="prereg-factor-design",
            )
            prereg_outcomes = gr.Textbox(
                label=labels["prereg_outcomes"],
                value=prereg_defaults["outcomes"],
                lines=3,
                elem_id="prereg-outcomes",
            )
            prereg_performance_metrics = gr.Textbox(
                label=labels["prereg_performance_metrics"],
                value=simulation_defaults["performance_metrics"],
                lines=3,
                elem_id="prereg-performance-metrics",
            )
            prereg_aggregation = gr.Textbox(
                label=labels["prereg_aggregation"],
                value=simulation_defaults["aggregation"],
                lines=3,
                elem_id="prereg-aggregation",
            )
            prereg_analysis = gr.Textbox(
                label=labels["prereg_analysis"],
                value=prereg_defaults["analysis"],
                lines=3,
                elem_id="prereg-analysis",
            )
            prereg_freeze = gr.Checkbox(
                label=labels["prereg_freeze"],
                value=True,
                elem_id="prereg-freeze-checkbox",
            )
            prereg_deviations = gr.Textbox(
                label=labels["prereg_deviations"],
                value=prereg_defaults["deviations"],
                lines=2,
                elem_id="prereg-deviations",
            )
            prereg_planned_n = gr.Number(
                label=labels["prereg_planned_n"],
                value=power_defaults["planned_n"],
                precision=0,
                minimum=1,
                elem_id="prereg-planned-n",
            )
            with gr.Row():
                prereg_power_test = gr.Dropdown(
                    label=labels["prereg_power_test"],
                    choices=_power_test_choices("ko"),
                    value=str(power_defaults["test_family"]),
                    elem_id="prereg-power-test",
                )
                prereg_power_effect = gr.Slider(
                    label=labels["prereg_power_effect"],
                    minimum=0.1,
                    maximum=1.5,
                    step=0.05,
                    value=float(power_defaults["effect_size"]),
                    elem_id="prereg-power-effect",
                )
            with gr.Row():
                prereg_power_alpha = gr.Slider(
                    label=labels["prereg_power_alpha"],
                    minimum=0.01,
                    maximum=0.2,
                    step=0.01,
                    value=float(power_defaults["alpha"]),
                    elem_id="prereg-power-alpha",
                )
                prereg_power_target = gr.Slider(
                    label=labels["prereg_power_target"],
                    minimum=0.5,
                    maximum=0.99,
                    step=0.01,
                    value=float(power_defaults["target_power"]),
                    elem_id="prereg-power-target",
                )
            prereg_power_summary = gr.Markdown(
                _power_analysis_markdown(
                    "ko",
                    str(power_defaults["test_family"]),
                    float(power_defaults["effect_size"]),
                    float(power_defaults["alpha"]),
                    float(power_defaults["target_power"]),
                ),
                elem_id="prereg-power-summary",
            )
            prereg_button = gr.Button(
                labels["prereg_button"],
                variant="secondary",
                elem_id="prereg-button",
            )
            prereg_preview = gr.Markdown(
                _preregistration_markdown(
                    "",
                    "",
                    "ko",
                    prereg_defaults["title"],
                    prereg_defaults["hypotheses"],
                    prereg_defaults["design"],
                    prereg_defaults["outcomes"],
                    prereg_defaults["analysis"],
                    True,
                    prereg_defaults["deviations"],
                    float(power_defaults["planned_n"]),
                    str(power_defaults["test_family"]),
                    float(power_defaults["effect_size"]),
                    float(power_defaults["alpha"]),
                    float(power_defaults["target_power"]),
                    simulation_defaults["data_generation"],
                    simulation_defaults["factor_design"],
                    simulation_defaults["performance_metrics"],
                    simulation_defaults["aggregation"],
                ),
                elem_id="prereg-preview",
            )
            prereg_download = gr.File(
                label=labels["prereg_download"],
                elem_id="prereg-download",
            )

        with gr.Column(elem_id="export-panel"):
            export_heading = gr.Markdown(f"#### {labels['export_panel']}")
            jsonl = gr.Code(label=labels["jsonl"], language="json")
            download = gr.File(label=labels["download"])
            html_report_button = gr.Button(
                labels["html_report_button"],
                variant="secondary",
                elem_id="html-report-button",
            )
            html_report_download = gr.File(
                label=labels["html_report_download"],
                elem_id="html-report-download",
            )
            csv_bundle_button = gr.Button(
                labels["csv_bundle_button"],
                variant="secondary",
                elem_id="csv-bundle-button",
            )
            csv_bundle_download = gr.File(
                label=labels["csv_bundle_download"],
                elem_id="csv-bundle-download",
            )
            finetuning_format = gr.Dropdown(
                label=labels["finetuning_format"],
                choices=_finetuning_format_choices("ko"),
                value="openai",
                elem_id="finetuning-format",
            )
            finetuning_button = gr.Button(
                labels["finetuning_button"],
                variant="secondary",
                elem_id="finetuning-export-button",
            )
            finetuning_download = gr.File(
                label=labels["finetuning_download"],
                elem_id="finetuning-download",
            )
            latex_table_button = gr.Button(
                labels["latex_table_button"],
                variant="secondary",
                elem_id="latex-table-button",
            )
            latex_table_download = gr.File(
                label=labels["latex_table_download"],
                elem_id="latex-table-download",
            )
            replication_package_button = gr.Button(
                labels["replication_button"],
                variant="secondary",
                elem_id="replication-package-button",
            )
            replication_package_download = gr.File(
                label=labels["replication_download"],
                elem_id="replication-package-download",
            )
            repro_certificate_button = gr.Button(
                labels["repro_certificate_button"],
                variant="secondary",
                elem_id="repro-certificate-button",
            )
            repro_certificate_download = gr.File(
                label=labels["repro_certificate_download"],
                elem_id="repro-certificate-download",
            )
            deposit_panel = gr.Accordion(
                labels["deposit_panel"],
                open=False,
                elem_id="deposit-panel",
            )
            with deposit_panel:
                deposit_creators = gr.Textbox(
                    label=labels["deposit_creators"],
                    value=deposit_defaults["creators"],
                    lines=2,
                    elem_id="deposit-creators",
                )
                deposit_description = gr.Textbox(
                    label=labels["deposit_description"],
                    value=deposit_defaults["description"],
                    lines=3,
                    elem_id="deposit-description",
                )
                deposit_keywords = gr.Textbox(
                    label=labels["deposit_keywords"],
                    value=deposit_defaults["keywords"],
                    lines=1,
                    elem_id="deposit-keywords",
                )
                deposit_token = gr.Textbox(
                    label=labels["deposit_token"],
                    value="",
                    type="password",
                    lines=1,
                    elem_id="deposit-token",
                )
                with gr.Row():
                    deposit_sandbox = gr.Checkbox(
                        label=labels["deposit_sandbox"],
                        value=True,
                        elem_id="deposit-sandbox",
                    )
                    deposit_publish = gr.Checkbox(
                        label=labels["deposit_publish"],
                        value=False,
                        elem_id="deposit-publish",
                    )
                deposit_button = gr.Button(
                    labels["deposit_button"],
                    variant="secondary",
                    elem_id="deposit-button",
                )
                deposit_status = gr.Markdown(
                    labels["deposit_status"],
                    elem_id="deposit-status",
                )
                deposit_download = gr.File(
                    label=labels["deposit_download"],
                    elem_id="deposit-download",
                )
        report_agent_panel = gr.Accordion(
            labels["report_agent_panel"],
            open=False,
            elem_id="report-agent-panel",
        )
        with report_agent_panel:
            report_agent_question = gr.Textbox(
                label=labels["report_agent_question"],
                lines=2,
                value="",
                elem_id="report-agent-question",
            )
            report_agent_button = gr.Button(
                labels["report_agent_run"],
                elem_id="report-agent-button",
            )
            report_agent_output = gr.Markdown(
                labels["report_agent_empty"],
                elem_id="report-agent-output",
            )
        competitive_panel = gr.Accordion(
            labels["competitive_panel"],
            open=False,
            elem_id="competitive-comparison-panel",
        )
        with competitive_panel:
            competitive_table = gr.Markdown(
                _competitive_comparison_markdown("ko"),
                elem_id="competitive-comparison-table",
            )
        cross_model_panel = gr.Accordion(
            labels["cross_model_panel"],
            open=False,
            elem_id="cross-model-panel",
        )
        with cross_model_panel:
            cross_model_models = gr.CheckboxGroup(
                label=labels["cross_model_models"],
                choices=list(CROSS_MODEL_CHOICES),
                value=["GPT", "Claude", "Replay"],
                elem_id="cross-model-choices",
            )
            cross_model_button = gr.Button(
                labels["cross_model_button"],
                elem_id="cross-model-button",
            )
            with gr.Row(elem_id="cross-model-results"):
                cross_model_gpt = gr.Markdown(
                    labels["cross_model_empty"],
                    elem_id="cross-model-gpt",
                )
                cross_model_claude = gr.Markdown(
                    labels["cross_model_empty"],
                    elem_id="cross-model-claude",
                )
                cross_model_replay = gr.Markdown(
                    labels["cross_model_empty"],
                    elem_id="cross-model-replay",
                )
            cross_model_diff = gr.Markdown(
                labels["cross_model_empty"],
                elem_id="cross-model-diff",
            )
        compare_panel = gr.Accordion(
            labels["compare_panel"],
            open=False,
            elem_id="compare-panel",
        )
        with compare_panel:
            with gr.Row():
                compare_seed_a = gr.Number(
                    label=labels["compare_seed_a"],
                    value=20260419,
                    precision=0,
                    elem_id="compare-seed-a",
                )
                compare_seed_b = gr.Number(
                    label=labels["compare_seed_b"],
                    value=20260420,
                    precision=0,
                    elem_id="compare-seed-b",
                )
            compare_button = gr.Button(
                labels["compare_button"],
                elem_id="compare-button",
            )
            compare_output = gr.Markdown(
                labels["compare_empty"],
                elem_id="compare-output",
            )
        interview_panel = gr.Accordion(
            labels["interview_panel"],
            open=False,
            elem_id="interview-panel",
        )
        with interview_panel:
            interview_agent = gr.Dropdown(
                label=labels["interview_agent"],
                choices=[],
                value="agent_1",
                allow_custom_value=True,
                elem_id="interview-agent",
            )
            interview_question = gr.Textbox(
                label=labels["interview_question"],
                lines=2,
                value="",
                elem_id="interview-question",
            )
            interview_button = gr.Button(
                labels["interview_button"],
                elem_id="interview-button",
            )
            interview_output = gr.Markdown(
                labels["interview_empty"],
                elem_id="interview-output",
            )

        agent_editor_outputs: list[Any] = []
        for controls in agent_tabs:
            agent_editor_outputs.extend(
                [
                    controls["tab"],
                    controls["editor_column"],
                    controls["unavailable_note"],
                    controls["name"],
                    controls["age"],
                    controls["persona_preset"],
                    controls["routine_preset"],
                    controls["routine_text"],
                    controls["personality_input_mode"],
                    controls["questionnaire_panel"],
                    controls["questionnaire_intro"],
                    *[
                        controls["questionnaire_domain_panels"][domain]
                        for domain in HEXACO_DOMAINS
                    ],
                    controls["questionnaire_apply"],
                    controls["questionnaire_summary"],
                    controls["tier_a_panel"],
                    controls["extended_panel"],
                    controls["extended_panel_note"],
                    controls["tier_bd_panel"],
                    controls["honesty_humility_caveat"],
                    controls["tier_c_panel"],
                    controls["dark_tetrad_notice"],
                    controls["tier_e_panel"],
                    controls["tier_f_panel"],
                    controls["tier_g_panel"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                    *[
                        controls["questionnaire_inputs"][item.item_id]
                        for item in HEXACO_QUESTIONNAIRE_ITEMS
                    ],
                ]
            )
        advanced_research_outputs: list[Any] = [scenario, advanced_research_status]
        for controls in agent_tabs:
            advanced_research_outputs.extend(
                [
                    controls["tier_c_panel"],
                    controls["dark_tetrad_notice"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in DARK_TETRAD_FIELDS
                    ],
                ]
            )

        language_outputs: list[gr.components.Component | gr.layouts.Accordion | gr.Markdown] = [
            header,
            scenario,
            environment_preset,
            provider,
            theme_mode,
            reviewer_mode,
            api_key,
            model,
            agent_panel,
            cultural_prior,
            advanced_research_mode,
            advanced_research_ack,
            advanced_research_notice,
            advanced_research_status,
            *agent_editor_outputs,
            agent_count,
            htn_enabled,
            planning_depth,
            ticks,
            batch_mode,
            batch_runs,
            master_seed,
            live_streaming,
            mirofish_panel,
            seed_prompt,
            seed_prompt_apply,
            event_injections,
            initial_relationships,
            report_agent_panel,
            report_agent_question,
            report_agent_button,
            competitive_panel,
            competitive_table,
            cross_model_panel,
            cross_model_models,
            cross_model_button,
            prereg_panel,
            prereg_template,
            prereg_title,
            prereg_hypotheses,
            prereg_design,
            prereg_data_generation,
            prereg_factor_design,
            prereg_outcomes,
            prereg_performance_metrics,
            prereg_aggregation,
            prereg_analysis,
            prereg_freeze,
            prereg_deviations,
            prereg_planned_n,
            prereg_power_test,
            prereg_power_effect,
            prereg_power_alpha,
            prereg_power_target,
            prereg_power_summary,
            prereg_button,
            prereg_download,
            compare_panel,
            compare_seed_a,
            compare_seed_b,
            compare_button,
            interview_panel,
            interview_agent,
            interview_question,
            interview_button,
            scenario_hint,
            run_button,
            export_heading,
            summary,
            action_chart,
            graph,
            tick_scrubber,
            tick_focus,
            timeline_tab,
            timeline,
            threads_tab,
            thread_view,
            memory_panel,
            inspector_agent,
            memory_view,
            emotion_view,
            spatial_heatmap_panel,
            spatial_heatmap_view,
            action_flow_panel,
            action_flow_view,
            mini_map_panel,
            mini_map_view,
            monologue_panel,
            monologue_view,
            current_plan_panel,
            current_plan_view,
            trait_matrix_panel,
            trait_matrix_plot,
            trait_matrix_summary,
            statistics_panel,
            fairness_panel,
            fairness_plot,
            fairness_summary,
            jsonl,
            download,
            html_report_button,
            html_report_download,
            csv_bundle_button,
            csv_bundle_download,
            finetuning_format,
            finetuning_button,
            finetuning_download,
            latex_table_button,
            latex_table_download,
            replication_package_button,
            replication_package_download,
            repro_certificate_button,
            repro_certificate_download,
            deposit_panel,
            deposit_creators,
            deposit_description,
            deposit_keywords,
            deposit_token,
            deposit_sandbox,
            deposit_publish,
            deposit_button,
            deposit_status,
            deposit_download,
            report_agent_output,
            cross_model_gpt,
            cross_model_claude,
            cross_model_replay,
            cross_model_diff,
            compare_output,
            interview_output,
            language,
        ]
        seed_prompt_outputs: list[Any] = []
        for controls in agent_tabs:
            seed_prompt_outputs.extend(
                [
                    controls["name"],
                    controls["age"],
                    controls["persona_preset"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                ]
            )
        seed_prompt_outputs.extend([initial_relationships, seed_prompt_summary])
        scenario_synthesis_outputs: list[Any] = [agent_count]
        for controls in agent_tabs:
            scenario_synthesis_outputs.extend(
                [
                    controls["name"],
                    controls["age"],
                    controls["persona_preset"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                ]
            )
        scenario_synthesis_outputs.extend(
            [event_injections, initial_relationships, scenario_synthesis_output]
        )
        community_scenario_outputs: list[Any] = [agent_count]
        for controls in agent_tabs:
            community_scenario_outputs.extend(
                [
                    controls["name"],
                    controls["age"],
                    controls["persona_preset"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                ]
            )
        community_scenario_outputs.extend(
            [event_injections, initial_relationships, community_gallery_preview]
        )
        agent_editor_state_inputs: list[Any] = []
        for controls in agent_tabs:
            agent_editor_state_inputs.extend(
                [
                    controls["persona_preset"],
                    controls["routine_preset"],
                    controls["name"],
                    controls["age"],
                    controls["routine_text"],
                    controls["personality_input_mode"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                    *[
                        controls["questionnaire_inputs"][item.item_id]
                        for item in HEXACO_QUESTIONNAIRE_ITEMS
                    ],
                ]
            )

        def _switch(
            lang_choice: str,
            current_provider: str,
            current_scenario: str,
            current_environment: str,
            current_cultural_prior: str,
            current_agent_count: int,
            current_htn_enabled: bool,
            current_planning_depth: int,
            current_batch_mode: bool,
            current_batch_runs: int,
            current_master_seed: int,
            current_live_streaming: bool,
            current_theme_mode: str,
            current_advanced_research_mode: bool,
            current_advanced_research_ack: bool,
            current_power_test: str,
            current_power_effect: float,
            current_power_alpha: float,
            current_power_target: float,
            current_planned_n: float | None,
            *agent_editor_state: Any,
        ) -> list[Any]:
            return _language_updates(
                lang_choice,
                current_provider,
                current_scenario,
                current_environment,
                current_cultural_prior,
                None,
                current_agent_count,
                current_htn_enabled,
                current_planning_depth,
                current_batch_mode,
                current_batch_runs,
                current_master_seed,
                current_live_streaming,
                current_theme_mode,
                current_advanced_research_mode,
                current_advanced_research_ack,
                current_power_test,
                current_power_effect,
                current_power_alpha,
                current_power_target,
                current_planned_n,
                *agent_editor_state,
            )

        tutorial_button.click(
            fn=None,
            inputs=[language],
            outputs=None,
            js="(language) => { window.KNOEMA_TUTORIAL?.start(language); }",
            queue=False,
            show_progress="hidden",
        )

        demo.load(
            fn=None,
            inputs=[language],
            outputs=[theme_mode, reviewer_mode],
            js="(language) => [window.KNOEMA_THEME?.sync(language) ?? 'auto', new URLSearchParams(window.location.search).get('reviewer') === '1']",
            queue=False,
            show_progress="hidden",
        )

        theme_mode.change(
            fn=None,
            inputs=[theme_mode, language],
            outputs=[theme_mode],
            js="(theme, language) => window.KNOEMA_THEME?.setFromLabel(theme, language) ?? theme",
            queue=False,
            show_progress="hidden",
        ).then(
            _relationship_graph_theme_update,
            inputs=[graph, theme_mode],
            outputs=[graph],
        )

        language.change(
            _switch,
            inputs=[
                language,
                provider,
                scenario,
                environment_preset,
                cultural_prior,
                agent_count,
                htn_enabled,
                planning_depth,
                batch_mode,
                batch_runs,
                master_seed,
                live_streaming,
                theme_mode,
                advanced_research_mode,
                advanced_research_ack,
                prereg_power_test,
                prereg_power_effect,
                prereg_power_alpha,
                prereg_power_target,
                prereg_planned_n,
                *agent_editor_state_inputs,
            ],
            outputs=language_outputs,
        )
        language.change(
            _player_mode_language_updates,
            inputs=[provider, language],
            outputs=[
                player_panel,
                player_input,
                player_submit,
                player_voice_input,
                player_voice_output,
                player_stt_engine,
                player_tts_engine,
            ],
        )
        language.change(
            _statistical_analysis_markdown,
            inputs=[jsonl, language],
            outputs=[statistics_summary],
        )
        advanced_research_mode.change(
            _advanced_research_ui_updates,
            inputs=[scenario, language, advanced_research_mode, advanced_research_ack],
            outputs=advanced_research_outputs,
        )
        advanced_research_ack.change(
            _advanced_research_ui_updates,
            inputs=[scenario, language, advanced_research_mode, advanced_research_ack],
            outputs=advanced_research_outputs,
        )
        scenario.change(
            _scenario_agent_count_update,
            inputs=[scenario],
            outputs=[agent_count],
        )
        scenario.change(
            _hint_markdown_update,
            inputs=[scenario, language, environment_preset],
            outputs=[scenario_hint],
        )
        scenario.change(
            _scenario_agent_editor_updates,
            inputs=[scenario, cultural_prior, language],
            outputs=agent_editor_outputs,
        )
        environment_preset.change(
            _hint_markdown_update,
            inputs=[scenario, language, environment_preset],
            outputs=[scenario_hint],
        )
        cultural_prior.change(
            _agent_editor_updates,
            inputs=[scenario, agent_count, cultural_prior, language],
            outputs=agent_editor_outputs,
        )
        agent_count.change(
            _agent_editor_updates,
            inputs=[scenario, agent_count, cultural_prior, language],
            outputs=agent_editor_outputs,
        )
        batch_mode.change(
            _batch_control_updates,
            inputs=[batch_mode],
            outputs=[batch_runs, master_seed],
        )
        provider.change(
            _player_mode_provider_updates,
            inputs=[provider, language],
            outputs=[
                player_panel,
                player_status,
                player_input,
                player_submit,
                player_voice_input,
                player_voice_output,
                player_stt_engine,
                player_tts_engine,
                player_session_state,
            ],
        )
        tick_scrubber.change(
            _tick_focus_markdown,
            inputs=[jsonl, tick_scrubber, language],
            outputs=[tick_focus],
        )
        tick_scrubber.change(
            _mini_map_figure,
            inputs=[jsonl, tick_scrubber, language],
            outputs=[mini_map_view],
        )
        for control in (
            prereg_power_test,
            prereg_power_effect,
            prereg_power_alpha,
            prereg_power_target,
        ):
            control.change(
                _power_analysis_updates,
                inputs=[
                    language,
                    prereg_power_test,
                    prereg_power_effect,
                    prereg_power_alpha,
                    prereg_power_target,
                ],
                outputs=[prereg_planned_n, prereg_power_summary],
            )
        prereg_template.change(
            _prereg_template_updates,
            inputs=[prereg_template, language],
            outputs=[
                prereg_title,
                prereg_hypotheses,
                prereg_design,
                prereg_data_generation,
                prereg_factor_design,
                prereg_outcomes,
                prereg_performance_metrics,
                prereg_aggregation,
                prereg_analysis,
                prereg_deviations,
                prereg_planned_n,
                prereg_power_test,
                prereg_power_effect,
                prereg_power_alpha,
                prereg_power_target,
                prereg_power_summary,
            ],
        )
        html_report_button.click(
            _export_html_report,
            inputs=[timeline, graph, jsonl, summary, language],
            outputs=[html_report_download],
            api_name="export_html_report",
        )
        csv_bundle_button.click(
            _export_csv_bundle,
            inputs=[jsonl, memory_snapshot_state, summary, language],
            outputs=[csv_bundle_download],
            api_name="export_csv_bundle",
        )
        finetuning_button.click(
            _export_finetuning_dataset,
            inputs=[jsonl, finetuning_format, language],
            outputs=[finetuning_download],
            api_name="export_finetuning_dataset",
        )
        latex_table_button.click(
            _export_latex_table,
            inputs=[jsonl, memory_snapshot_state, summary, language],
            outputs=[latex_table_download],
            api_name="export_latex_table",
        )
        prereg_button.click(
            _export_preregistration,
            inputs=[
                summary,
                jsonl,
                language,
                prereg_title,
                prereg_hypotheses,
                prereg_design,
                prereg_outcomes,
                prereg_analysis,
                prereg_freeze,
                prereg_deviations,
                prereg_planned_n,
                prereg_power_test,
                prereg_power_effect,
                prereg_power_alpha,
                prereg_power_target,
                prereg_data_generation,
                prereg_factor_design,
                prereg_performance_metrics,
                prereg_aggregation,
            ],
            outputs=[prereg_preview, prereg_download],
            api_name="export_preregistration",
        )
        replication_package_button.click(
            _export_replication_package,
            inputs=[jsonl, memory_snapshot_state, summary, language],
            outputs=[replication_package_download],
            api_name="export_replication_package",
        )
        repro_certificate_button.click(
            _export_reproducibility_certificate,
            inputs=[
                jsonl,
                summary,
                language,
                scenario,
                environment_preset,
                cultural_prior,
                provider,
                api_key,
                model,
                primary_name,
                primary_age,
                agent_tabs[0]["routine_text"],
                *[
                    agent_tabs[0]["trait_sliders"][field_name]
                    for field_name in PERSONA_TRAIT_FIELDS
                ],
                agent_tabs[1]["name"],
                agent_tabs[1]["age"],
                agent_tabs[1]["routine_text"],
                *[
                    agent_tabs[1]["trait_sliders"][field_name]
                    for field_name in PERSONA_TRAIT_FIELDS
                ],
                agent_tabs[2]["name"],
                agent_tabs[2]["age"],
                agent_tabs[2]["routine_text"],
                *[
                    agent_tabs[2]["trait_sliders"][field_name]
                    for field_name in PERSONA_TRAIT_FIELDS
                ],
                htn_enabled,
                planning_depth,
                ticks,
                agent_count,
                batch_mode,
                batch_runs,
                master_seed,
                language,
                event_injections,
                initial_relationships,
            ],
            outputs=[repro_certificate_download],
            api_name="export_reproducibility_certificate",
        )
        deposit_button.click(
            _export_deposit_bundle,
            inputs=[
                summary,
                jsonl,
                prereg_preview,
                language,
                prereg_title,
                deposit_creators,
                deposit_description,
                deposit_keywords,
                deposit_token,
                deposit_sandbox,
                deposit_publish,
            ],
            outputs=[deposit_status, deposit_download],
            api_name="export_deposit_bundle",
        )
        seed_prompt_apply.click(
            _seed_prompt_updates,
            inputs=[seed_prompt, language],
            outputs=seed_prompt_outputs,
        )
        scenario_synthesis_button.click(
            _scenario_synthesis_updates,
            inputs=[scenario_synthesis_input, language],
            outputs=scenario_synthesis_outputs,
        )
        community_gallery_load.click(
            _community_scenario_updates,
            inputs=[community_gallery_scenario, language],
            outputs=community_scenario_outputs,
        )
        report_agent_button.click(
            _report_agent_answer,
            inputs=[report_agent_question, jsonl, summary, language],
            outputs=[report_agent_output],
        )
        interview_button.click(
            _interview_agent_answer,
            inputs=[interview_agent, interview_question, jsonl, memory_snapshot_state, language],
            outputs=[interview_output],
        )
        inspector_agent.change(
            _memory_inspector_views,
            inputs=[memory_snapshot_state, inspector_agent, language],
            outputs=[memory_view, emotion_view],
        )
        for controls in agent_tabs:
            controls["persona_preset"].change(
                _apply_persona_preset,
                inputs=[controls["persona_preset"]],
                outputs=[
                    controls["trait_sliders"][field_name]
                    for field_name in PERSONA_TRAIT_FIELDS
                ],
            )
            controls["routine_preset"].change(
                _apply_routine_preset,
                inputs=[controls["routine_preset"], language],
                outputs=[controls["routine_text"]],
            )
            controls["personality_input_mode"].change(
                _questionnaire_mode_updates,
                inputs=[
                    controls["personality_input_mode"],
                    language,
                    *[
                        controls["questionnaire_inputs"][item.item_id]
                        for item in HEXACO_QUESTIONNAIRE_ITEMS
                    ],
                ],
                outputs=[
                    controls["questionnaire_panel"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                    controls["questionnaire_summary"],
                ],
            )
            controls["questionnaire_apply"].click(
                _questionnaire_mode_updates,
                inputs=[
                    controls["personality_input_mode"],
                    language,
                    *[
                        controls["questionnaire_inputs"][item.item_id]
                        for item in HEXACO_QUESTIONNAIRE_ITEMS
                    ],
                ],
                outputs=[
                    controls["questionnaire_panel"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                    controls["questionnaire_summary"],
                ],
            )
            for item in HEXACO_QUESTIONNAIRE_ITEMS:
                controls["questionnaire_inputs"][item.item_id].change(
                    _questionnaire_mode_updates,
                    inputs=[
                        controls["personality_input_mode"],
                        language,
                        *[
                            controls["questionnaire_inputs"][question_item.item_id]
                            for question_item in HEXACO_QUESTIONNAIRE_ITEMS
                        ],
                    ],
                    outputs=[
                        controls["questionnaire_panel"],
                        *[
                            controls["trait_sliders"][field_name]
                            for field_name in PERSONA_TRAIT_FIELDS
                        ],
                        controls["questionnaire_summary"],
                    ],
                )
        common_run_inputs = [
            scenario,
            environment_preset,
            cultural_prior,
            provider,
            api_key,
            model,
            primary_name,
            primary_age,
            agent_tabs[0]["routine_text"],
            *[
                agent_tabs[0]["trait_sliders"][field_name]
                for field_name in PERSONA_TRAIT_FIELDS
            ],
            agent_tabs[1]["name"],
            agent_tabs[1]["age"],
            agent_tabs[1]["routine_text"],
            *[
                agent_tabs[1]["trait_sliders"][field_name]
                for field_name in PERSONA_TRAIT_FIELDS
            ],
            agent_tabs[2]["name"],
            agent_tabs[2]["age"],
            agent_tabs[2]["routine_text"],
            *[
                agent_tabs[2]["trait_sliders"][field_name]
                for field_name in PERSONA_TRAIT_FIELDS
            ],
            htn_enabled,
            planning_depth,
            ticks,
            agent_count,
            batch_mode,
            batch_runs,
            master_seed,
            language,
            event_injections,
            initial_relationships,
        ]
        language.change(
            _fairness_audit_outputs,
            inputs=[jsonl, *common_run_inputs],
            outputs=[fairness_plot, fairness_summary],
        )
        run_event = run_button.click(
            _run_with_optional_streaming_ui_theme,
            inputs=[
                live_streaming,
                reviewer_mode,
                theme_mode,
                advanced_research_mode,
                advanced_research_ack,
                *common_run_inputs,
            ],
            outputs=[
                timeline,
                thread_view,
                graph,
                monologue_view,
                current_plan_view,
                jsonl,
                download,
                summary,
                action_chart,
                tick_scrubber,
                tick_focus,
                memory_snapshot_state,
                inspector_agent,
                memory_view,
                emotion_view,
                spatial_heatmap_view,
                action_flow_view,
                mini_map_view,
                player_voice_output,
                player_session_state,
                player_status,
            ],
            api_name="run",
        )
        run_event.then(
            _statistical_analysis_markdown,
            inputs=[jsonl, language],
            outputs=[statistics_summary],
        )
        run_event.then(
            _fairness_audit_outputs,
            inputs=[jsonl, *common_run_inputs],
            outputs=[fairness_plot, fairness_summary],
        )
        compare_button.click(
            _compare_runs,
            inputs=[*common_run_inputs, compare_seed_a, compare_seed_b],
            outputs=[compare_output],
        )
        cross_model_button.click(
            _compare_models,
            inputs=[*common_run_inputs, cross_model_models],
            outputs=[cross_model_gpt, cross_model_claude, cross_model_replay, cross_model_diff],
            api_name="compare_models",
        )
        player_event = player_submit.click(
            _advance_player_mode_theme,
            inputs=[
                player_session_state,
                player_input,
                player_voice_input,
                player_stt_engine,
                player_tts_engine,
                theme_mode,
                reviewer_mode,
            ],
            outputs=[
                timeline,
                thread_view,
                graph,
                monologue_view,
                current_plan_view,
                jsonl,
                download,
                summary,
                action_chart,
                tick_scrubber,
                tick_focus,
                memory_snapshot_state,
                inspector_agent,
                memory_view,
                emotion_view,
                spatial_heatmap_view,
                action_flow_view,
                mini_map_view,
                player_voice_output,
                player_session_state,
                player_status,
                player_input,
            ],
        )
        player_event.then(
            _statistical_analysis_markdown,
            inputs=[jsonl, language],
            outputs=[statistics_summary],
        )
        player_submit_event = player_input.submit(
            _advance_player_mode_theme,
            inputs=[
                player_session_state,
                player_input,
                player_voice_input,
                player_stt_engine,
                player_tts_engine,
                theme_mode,
                reviewer_mode,
            ],
            outputs=[
                timeline,
                thread_view,
                graph,
                monologue_view,
                current_plan_view,
                jsonl,
                download,
                summary,
                action_chart,
                tick_scrubber,
                tick_focus,
                memory_snapshot_state,
                inspector_agent,
                memory_view,
                emotion_view,
                spatial_heatmap_view,
                action_flow_view,
                mini_map_view,
                player_voice_output,
                player_session_state,
                player_status,
                player_input,
            ],
        )
        player_submit_event.then(
            _statistical_analysis_markdown,
            inputs=[jsonl, language],
            outputs=[statistics_summary],
        )

    demo.queue()
    return cast(gr.Blocks, demo)


if __name__ == "__main__":
    cast(Any, build_app()).launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        ssr_mode=False,
        show_error=True,
    )
