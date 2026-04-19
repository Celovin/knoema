"""Gradio app for the Knoema Playground."""

from __future__ import annotations

import json
import tempfile
from collections import Counter
from datetime import UTC, datetime
from html import escape
from typing import Any, cast

import gradio as gr
import plotly.graph_objects as go
from plotly.colors import qualitative
from plotly.subplots import make_subplots

try:
    from .simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        AGENT_EDITOR_SLOT_COUNT,
        PERSONA_TRAIT_DEFAULTS,
        PERSONA_TRAIT_FIELDS,
        Provider,
        advance_player_session,
        agent_editor_defaults,
        build_playground_hint,
        compute_trait_correlation_study,
        cultural_prior_choices,
        cultural_prior_trait_values,
        environment_note,
        host_key_active,
        load_environment_presets,
        persona_choices,
        persona_trait_values,
        routine_preset_choices,
        routine_preset_text,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
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
    from simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        AGENT_EDITOR_SLOT_COUNT,
        PERSONA_TRAIT_DEFAULTS,
        PERSONA_TRAIT_FIELDS,
        Provider,
        advance_player_session,
        agent_editor_defaults,
        build_playground_hint,
        compute_trait_correlation_study,
        cultural_prior_choices,
        cultural_prior_trait_values,
        environment_note,
        host_key_active,
        load_environment_presets,
        persona_choices,
        persona_trait_values,
        routine_preset_choices,
        routine_preset_text,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
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


KOREAN_CHOICE = "한국어"
LANGUAGE_CHOICES = [KOREAN_CHOICE, "English"]
TUTORIAL_STORAGE_KEY = "knoema_tutorial_completed"
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
LABELS["en"]["html_report_button"] = "Export HTML report"
LABELS["en"]["html_report_download"] = "Download HTML report"
LABELS["en"]["html_report_title"] = "Knoema Playground HTML report"
LABELS["en"]["generated_at"] = "Generated at"
LABELS["ko"]["mirofish_panel"] = "MiroFish 스타일 실험실"
LABELS["ko"]["seed_prompt"] = "시드 프롬프트"
LABELS["ko"]["seed_prompt_placeholder"] = "예: 분주한 항구 술집, 세 명의 NPC, 경쟁과 협력"
LABELS["ko"]["seed_prompt_apply"] = "시드로 3명 페르소나 생성"
LABELS["ko"]["seed_prompt_empty"] = "시드 프롬프트를 입력하면 첫 3명 에이전트와 초기 관계 초안을 채웁니다."
LABELS["ko"]["event_injections"] = "이벤트 주입"
LABELS["ko"]["event_injections_placeholder"] = "0 | Tavern Bar | A courier bursts in with a sealed letter | agent_1,agent_2 | urgent_news"
LABELS["ko"]["initial_relationships"] = "초기 관계 시드"
LABELS["ko"]["initial_relationships_placeholder"] = "agent_1 | agent_2 | colleague | 0.55 | 0.70 | 0.30"
LABELS["ko"]["report_agent_panel"] = "ReportAgent Q&A"
LABELS["ko"]["report_agent_question"] = "런 질문"
LABELS["ko"]["report_agent_run"] = "현재 런 요약 답변"
LABELS["ko"]["report_agent_empty"] = "런을 실행한 뒤 질문하면 JSONL 기반 요약을 돌려줍니다."
LABELS["ko"]["compare_panel"] = "A/B 비교"
LABELS["ko"]["compare_seed_a"] = "비교 시드 A"
LABELS["ko"]["compare_seed_b"] = "비교 시드 B"
LABELS["ko"]["compare_button"] = "두 시드 비교"
LABELS["ko"]["compare_empty"] = "같은 설정으로 두 시드를 돌려 차이를 비교합니다."
LABELS["ko"]["interview_panel"] = "에이전트 인터뷰"
LABELS["ko"]["interview_agent"] = "에이전트 ID"
LABELS["ko"]["interview_question"] = "인터뷰 질문"
LABELS["ko"]["interview_button"] = "인터뷰 생성"
LABELS["ko"]["interview_empty"] = "런 이후 에이전트 ID와 질문을 넣으면 최근 기억과 행동을 바탕으로 답변합니다."
LABELS["en"]["mirofish_panel"] = "MiroFish-style lab"
LABELS["en"]["seed_prompt"] = "Seed prompt"
LABELS["en"]["seed_prompt_placeholder"] = "Example: a crowded harbor tavern with three NPCs balancing rivalry and cooperation"
LABELS["en"]["seed_prompt_apply"] = "Generate three personas from seed"
LABELS["en"]["seed_prompt_empty"] = "Enter a seed prompt to fill the first three agent editors and draft initial relationship seeds."
LABELS["en"]["event_injections"] = "Event injections"
LABELS["en"]["event_injections_placeholder"] = "0 | Tavern Bar | A courier bursts in with a sealed letter | agent_1,agent_2 | urgent_news"
LABELS["en"]["initial_relationships"] = "Initial relationship seeds"
LABELS["en"]["initial_relationships_placeholder"] = "agent_1 | agent_2 | colleague | 0.55 | 0.70 | 0.30"
LABELS["en"]["report_agent_panel"] = "ReportAgent Q&A"
LABELS["en"]["report_agent_question"] = "Run question"
LABELS["en"]["report_agent_run"] = "Answer from current run"
LABELS["en"]["report_agent_empty"] = "Run a scenario first, then ask a question to get a JSONL-grounded summary."
LABELS["en"]["compare_panel"] = "A/B compare"
LABELS["en"]["compare_seed_a"] = "Compare seed A"
LABELS["en"]["compare_seed_b"] = "Compare seed B"
LABELS["en"]["compare_button"] = "Compare two seeds"
LABELS["en"]["compare_empty"] = "Run the current setup twice with two seeds and inspect the delta."
LABELS["en"]["interview_panel"] = "Agent interview"
LABELS["en"]["interview_agent"] = "Agent ID"
LABELS["en"]["interview_question"] = "Interview question"
LABELS["en"]["interview_button"] = "Generate interview"
LABELS["en"]["interview_empty"] = "After a run, provide an agent id and question to synthesize an answer from recent memories and actions."
LABELS["ko"]["cultural_prior"] = "문화 prior"
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
LABELS["ko"]["planning_depth_info"] = "HTN이 시작할 때 2~4개 하위 목표로 분해합니다."
LABELS["ko"]["current_plan_panel"] = "현재 계획"
LABELS["ko"]["current_plan_empty"] = "아직 생성된 HTN 계획이 없습니다."
LABELS["ko"]["agent_panel"] = "에이전트 성격"
LABELS["ko"]["agent_tab_prefix"] = "에이전트"
LABELS["ko"]["agent_tab_disabled"] = "이 슬롯을 사용하려면 agent count를 늘리세요."
LABELS["en"]["htn_enabled"] = "Enable hierarchical planning (HTN)"
LABELS["en"]["htn_info"] = "Applies to the primary agent in the current playground layout."
LABELS["en"]["planning_depth"] = "Planning depth"
LABELS["en"]["planning_depth_info"] = "Decompose the top goal into 2 to 4 subtasks at simulation start."
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
LABELS["ko"]["trait_matrix_panel"] = "Trait 상관/ablation"
LABELS["ko"]["trait_matrix_plot"] = "Trait correlation matrix"
LABELS["ko"]["trait_matrix_summary"] = "Trait ablation summary"
LABELS["en"]["trait_matrix_panel"] = "Trait correlation / ablation"
LABELS["en"]["trait_matrix_plot"] = "Trait correlation matrix"
LABELS["en"]["trait_matrix_summary"] = "Trait ablation summary"
LABELS["ko"]["batch_mode"] = "배치 모드"
LABELS["ko"]["batch_mode_info"] = "같은 시나리오를 여러 시드로 반복 실행해 집계합니다."
LABELS["ko"]["batch_runs"] = "반복 횟수"
LABELS["ko"]["batch_runs_info"] = "1~100회까지 반복 실행합니다. 단일 실행은 1회로 고정됩니다."
LABELS["ko"]["master_seed"] = "마스터 시드"
LABELS["ko"]["master_seed_info"] = "각 배치 시드는 master_seed + run_index로 파생됩니다."
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
AGENT_COLOR_SEQUENCE: tuple[str, ...] = tuple(qualitative.Bold)
ACTION_PATTERN_SEQUENCE: tuple[str, ...] = ("", "/", "\\", "x", "-", "|", "+", ".", "o")
ACTION_FLOW_SELF_TYPES = frozenset({"alone", "move", "query_memory"})
ACTION_FLOW_COLOR_SEQUENCE: tuple[str, ...] = tuple(qualitative.Set3 + qualitative.Bold)

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

FOOTER_CSS = f"""
footer {{display: none !important;}}
.footer {{display: none !important;}}
.api-docs {{display: none !important;}}
#relationship-graph .js-plotly-plot,
#relationship-graph .plot-container {{
    min-height: {GRAPH_HEIGHT_PX}px;
}}
#timeline-panel {{
    max-height: {TIMELINE_MAX_HEIGHT_PX}px;
    overflow-y: auto;
}}
.knoema-hint {{
    color: #475569;
    font-size: 0.95rem;
}}
.knoema-hint p {{
    margin-bottom: 0;
}}
.knoema-muted {{
    color: #64748b;
    font-size: 0.92rem;
}}
"""


def _language_key(language_choice: str) -> str:
    return "ko" if language_choice == KOREAN_CHOICE else "en"


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


def _provider_choices(language: str) -> list[str]:
    labels = LABELS[language]
    return [labels["replay"], "OpenAI", "Anthropic", labels["player_mode"]]


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
    go.Figure,
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
    controls: dict[str, Any] = {"trait_sliders": {}}

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
                with tier_bd_panel, gr.Row():
                    for field_name in TIER_BD_FIELDS:
                        controls["trait_sliders"][field_name] = _trait_slider(
                            field_name,
                            labels,
                            value=float(defaults["personality"][field_name]),
                            elem_id_prefix=trait_prefix,
                        )

                tier_c_panel = gr.Accordion(
                    labels["tier_c_panel"],
                    open=False,
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
            "tier_a_panel": tier_a_panel,
            "extended_panel": extended_panel,
            "extended_panel_note": extended_panel_note,
            "tier_bd_panel": tier_bd_panel,
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


def _render_result_outputs(
    result: Any,
    *,
    mode_label: str,
    provider: str,
    api_key: str,
    language: str,
) -> RunOutputs:
    host_provider = host_key_active(provider, api_key)
    batch_result = getattr(result, "batch_result", None)
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
    agent_ids = sorted(
        set(result.action_breakdown)
        | set(result.memory_snapshot)
        | {str(row["source"]) for row in result.relationship_rows}
        | {str(row["target"]) for row in result.relationship_rows}
    )
    agent_colors = _agent_color_map(agent_ids)
    memory_snapshot, memory_agent, memory_markdown, emotion_trajectory = _memory_inspector_outputs(
        result.memory_snapshot,
        language=language,
        batch_mode=batch_result is not None,
    )
    return (
        _timeline_markdown_with_agent_colors(
            result.jsonl,
            result.timeline_markdown,
            agent_colors,
            language=language,
        ),
        _conversation_threads_markdown(
            result.jsonl,
            result.memory_snapshot,
            agent_colors,
            language=language,
        ),
        _relationship_figure(
            result.relationship_rows,
            language=language,
            agent_colors=agent_colors,
        ),
        result.monologue_markdown,
        result.plan_markdown,
        result.jsonl,
        result.download_path,
        summary,
        _action_chart_figure(result.action_breakdown, language=language),
        gr.update(minimum=-1, maximum=max(-1, int(result.tick_count) - 1), value=-1),
        _tick_focus_markdown(result.jsonl, -1, language=language),
        memory_snapshot,
        memory_agent,
        memory_markdown,
        emotion_trajectory,
        _spatial_heatmap_figure(result.jsonl, result.memory_snapshot, language=language),
        _action_flow_figure(result.jsonl, language=language),
        _mini_map_figure(result.jsonl, -1, language=language),
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
) -> tuple[Any, ...]:
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
        ),
        gr.update(value=None),
        None,
        "",
    )


def _noop_run_outputs() -> tuple[Any, ...]:
    return tuple(gr.update() for _ in range(18))


def _coerce_plotly_figure(figure: Any) -> go.Figure:
    if isinstance(figure, go.Figure):
        return figure
    if isinstance(figure, dict):
        return go.Figure(figure)
    return go.Figure()


def _report_section(title: str, body: str) -> str:
    if not str(body).strip():
        return (
            f"<section><h2>{escape(title)}</h2>"
            "<p class='empty'>No data available.</p></section>"
        )
    return (
        f"<section><h2>{escape(title)}</h2>"
        f"<pre>{escape(str(body))}</pre></section>"
    )


def _export_html_report(
    timeline_markdown: str,
    graph_figure: Any,
    jsonl_text: str,
    summary: str,
    language: str,
) -> str:
    language_key = _language_key(language)
    labels = LABELS[language_key]
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
    {_report_section(labels["timeline"], timeline_markdown)}
    {_report_section(labels["jsonl"], jsonl_text)}
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
) -> tuple[Any, ...]:
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
        ),
        gr.update(value=response_audio),
        updated_session,
        _status_with_voice_notes(status, voice_notes),
        gr.update(value=""),
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


def _apply_routine_preset(preset_id: str | None) -> dict[str, Any]:
    return gr.update(value=routine_preset_text(preset_id), placeholder=LABELS["en"]["routine_text_placeholder"])


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
) -> list[Any]:
    language = _language_key(language_choice)
    labels = LABELS[language]
    defaults = agent_editor_defaults(
        scenario_name,
        agent_count=agent_count,
        slot_count=AGENT_EDITOR_SLOT_COUNT,
        cultural_prior_id=cultural_prior_id,
        language=language,
    )
    updates: list[Any] = []
    for slot_index, default in enumerate(defaults):
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
                gr.update(label=labels["name"], value=default["name"]),
                gr.update(label=labels["age"], value=int(default["age"])),
                gr.update(
                    label=labels["persona_preset"],
                    choices=_persona_choices(language),
                    value="",
                    info=labels["persona_preset_info"],
                ),
                gr.update(
                    label=labels["routine_preset"],
                    choices=_routine_preset_choices(language),
                    value="free",
                    info=labels["routine_preset_info"],
                ),
                gr.update(
                    label=labels["routine_text"],
                    value=str(default.get("routine_text", "")),
                    info=labels["routine_text_info"],
                    placeholder=labels["routine_text_placeholder"],
                ),
                gr.update(label=labels["tier_a_panel"]),
                gr.update(label=labels["extended_panel"]),
                labels["extended_panel_note"],
                gr.update(label=labels["tier_bd_panel"]),
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
                    value=float(default["personality"][field_name]),
                )
                for field_name in PERSONA_TRAIT_FIELDS
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


def _batch_control_updates(enabled: bool) -> list[dict[str, Any]]:
    return [
        gr.update(interactive=bool(enabled)),
        gr.update(interactive=bool(enabled)),
    ]


def _trait_update(field_name: str, labels: dict[str, str]) -> dict[str, Any]:
    return gr.update(label=labels[field_name], info=labels[f"{field_name}_info"])


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
) -> list[Any]:
    key = _language_key(lang_choice)
    labels = LABELS[key]
    provider_value = _provider_label(
        _normalize_provider(current_provider or labels["replay"]),
        key,
    )
    scenario_value = current_scenario or scenario_choices()[0]
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
    )
    trait_matrix_figure, trait_matrix_summary = _trait_correlation_outputs(key)
    return [
        labels["header"],
        gr.update(label=labels["scenario"]),
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
        gr.update(label=labels["api_key"], placeholder=labels["api_key_ph"]),
        gr.update(label=labels["model"]),
        gr.update(label=labels["agent_panel"]),
        gr.update(
            label=labels["cultural_prior"],
            choices=_cultural_prior_choices(key),
            value=current_cultural_prior or "",
            info=labels["cultural_prior_info"],
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
        gr.update(label=labels["jsonl"]),
        gr.update(label=labels["download"]),
        gr.update(value=labels["html_report_button"]),
        gr.update(label=labels["html_report_download"]),
        labels["report_agent_empty"],
        labels["compare_empty"],
        labels["interview_empty"],
        gr.update(label=labels["lang"]),
    ]


def _trait_axis_label(field_name: str, language: str) -> str:
    label = LABELS[language].get(field_name, field_name.replace("_", " ").title())
    return label.replace(" / ", "<br>")


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
    selected_agents = _selected_memory_agents(snapshot, agent_id)
    if not snapshot or not selected_agents:
        return LABELS[language]["memory_empty"]

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
        lines.append(f"> {LABELS[language]['memory_multi_hint']}")
    lines.extend(
        _memory_section_lines(
            LABELS[language]["memory_short_term"],
            list(memory.get("short_term", [])),
            language=language,
            section="short_term",
        )
    )
    lines.extend(
        _memory_section_lines(
            LABELS[language]["memory_long_term"],
            list(memory.get("long_term", [])),
            language=language,
            section="long_term",
        )
    )
    lines.extend(
        _memory_section_lines(
            LABELS[language]["memory_monologue"],
            list(memory.get("monologue", [])),
            language=language,
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
    selected_agents = _selected_memory_agents(snapshot, agent_id)
    return (
        _memory_inspector_markdown(snapshot, selected_agents, language=language),
        _emotion_trajectory_figure(snapshot, selected_agents, language=language),
    )


def _emotion_trajectory_figure(
    snapshot: dict[str, dict[str, list[dict[str, Any]]]],
    agent_id: str | list[str] | None,
    *,
    language: str = "en",
) -> go.Figure:
    selected_agents = _selected_memory_agents(snapshot, agent_id)[:EMOTION_TRAJECTORY_MAX_AGENTS]
    title = LABELS[language]["memory_emotion"]
    tick_label = "Tick"
    valence_label = "Valence"
    arousal_label = "Arousal / Dominance"
    empty_text = LABELS[language]["memory_emotion_empty"]
    if language == "ko":
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
        "camera": {"eye": {"x": 1.6, "y": 1.6, "z": 1.0}},
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
    positions = _sphere_positions(agents)
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    edge_z: list[float | None] = []
    for row in rows:
        source = str(row["source"])
        target = str(row["target"])
        sx, sy, sz = positions[source]
        tx, ty, tz = positions[target]
        edge_x.extend([sx, tx, None])
        edge_y.extend([sy, ty, None])
        edge_z.extend([sz, tz, None])

    node_x = [positions[agent][0] for agent in agents]
    node_y = [positions[agent][1] for agent in agents]
    node_z = [positions[agent][2] for agent in agents]
    node_text = list(agents)
    node_color = [color_map.get(agent, "#0f172a") for agent in agents]

    figure = go.Figure(
        data=[
            go.Scatter3d(
                x=edge_x,
                y=edge_y,
                z=edge_z,
                mode="lines",
                line={"width": 4, "color": "#94a3b8"},
                hoverinfo="none",
            ),
            go.Scatter3d(
                x=node_x,
                y=node_y,
                z=node_z,
                mode="markers+text",
                text=node_text,
                textposition="top center",
                marker={
                    "size": 14,
                    "color": node_color,
                    "colorscale": "Viridis",
                    "cmin": 0.0,
                    "cmax": 1.0,
                    "opacity": 0.95,
                    "line": {"width": 1, "color": "#1e293b"},
                    "colorbar": {
                        "title": "신뢰" if language == "ko" else "Trust",
                        "thickness": 12,
                        "len": 0.6,
                    },
                },
                hovertext=_node_hover_text(agents, rows, language=language),
                hoverinfo="text",
            ),
        ]
    )
    figure.update_layout(
        title=title,
        showlegend=False,
        scene=scene_layout,
        height=GRAPH_HEIGHT_PX,
        margin={"l": 0, "r": 0, "t": 40, "b": 0},
    )
    return figure


def _sphere_positions(agents: list[str]) -> dict[str, tuple[float, float, float]]:
    import math

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
    default_scenario = scenario_choices()[0]
    initial_agent_defaults = agent_editor_defaults(
        default_scenario,
        agent_count=scenario_default_agent_count(default_scenario),
        cultural_prior_id=None,
        language="ko",
    )
    initial_action_chart_figure = _action_chart_figure({}, language="ko")
    initial_trait_matrix_figure, initial_trait_matrix_summary = _trait_correlation_outputs("ko")

    with gr.Blocks(
        title="Knoema Playground",
        css=FOOTER_CSS,
        head=TUTORIAL_HEAD,
        analytics_enabled=False,
    ) as demo:
        with gr.Row():
            language = gr.Radio(
                label=labels["lang"],
                choices=LANGUAGE_CHOICES,
                value=LANGUAGE_CHOICES[0],
                scale=0,
            )
            tutorial_button = gr.Button("?", elem_id="tutorial-button", scale=0, min_width=52)

        header = gr.Markdown(labels["header"])

        with gr.Row():
            scenario = gr.Dropdown(
                label=labels["scenario"],
                choices=scenario_choices(),
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
                value=labels["replay"],
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
                    maximum=4,
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
        summary = gr.Textbox(label=labels["summary"], interactive=False)
        action_chart = gr.Plot(
            label=labels["action_chart"],
            value=initial_action_chart_figure,
            elem_id="action-breakdown-chart",
        )
        graph = gr.Plot(label=labels["graph"], elem_id="relationship-graph")
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
                    controls["tier_a_panel"],
                    controls["extended_panel"],
                    controls["extended_panel_note"],
                    controls["tier_bd_panel"],
                    controls["tier_c_panel"],
                    controls["dark_tetrad_notice"],
                    controls["tier_e_panel"],
                    controls["tier_f_panel"],
                    controls["tier_g_panel"],
                    *[
                        controls["trait_sliders"][field_name]
                        for field_name in PERSONA_TRAIT_FIELDS
                    ],
                ]
            )

        language_outputs: list[gr.components.Component | gr.layouts.Accordion | gr.Markdown] = [
            header,
            scenario,
            environment_preset,
            provider,
            api_key,
            model,
            agent_panel,
            cultural_prior,
            *agent_editor_outputs,
            agent_count,
            htn_enabled,
            planning_depth,
            ticks,
            batch_mode,
            batch_runs,
            master_seed,
            mirofish_panel,
            seed_prompt,
            seed_prompt_apply,
            event_injections,
            initial_relationships,
            report_agent_panel,
            report_agent_question,
            report_agent_button,
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
            jsonl,
            download,
            html_report_button,
            html_report_download,
            report_agent_output,
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

        def _switch(lang_choice: str) -> list[Any]:
            return _language_updates(
                lang_choice,
                provider.value,
                scenario.value,
                environment_preset.value,
                cultural_prior.value,
                None,
                agent_count.value,
                htn_enabled.value,
                planning_depth.value,
                batch_mode.value,
                batch_runs.value,
                master_seed.value,
            )

        tutorial_button.click(
            fn=None,
            inputs=[language],
            outputs=None,
            js="(language) => { window.KNOEMA_TUTORIAL?.start(language); }",
            queue=False,
            show_progress="hidden",
        )

        language.change(
            _switch,
            inputs=[language],
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
        html_report_button.click(
            _export_html_report,
            inputs=[timeline, graph, jsonl, summary, language],
            outputs=[html_report_download],
            api_name="export_html_report",
        )
        seed_prompt_apply.click(
            _seed_prompt_updates,
            inputs=[seed_prompt, language],
            outputs=seed_prompt_outputs,
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
                inputs=[controls["routine_preset"]],
                outputs=[controls["routine_text"]],
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
        run_button.click(
            _run_with_player_mode,
            inputs=common_run_inputs,
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
        compare_button.click(
            _compare_runs,
            inputs=[*common_run_inputs, compare_seed_a, compare_seed_b],
            outputs=[compare_output],
        )
        player_submit.click(
            _advance_player_mode,
            inputs=[
                player_session_state,
                player_input,
                player_voice_input,
                player_stt_engine,
                player_tts_engine,
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
        player_input.submit(
            _advance_player_mode,
            inputs=[
                player_session_state,
                player_input,
                player_voice_input,
                player_stt_engine,
                player_tts_engine,
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

    demo.queue()
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860)
