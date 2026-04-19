"""Gradio app for the Knoema Playground."""

from __future__ import annotations

import json
from typing import Any

import gradio as gr
import plotly.graph_objects as go

try:
    from .simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        PERSONA_TRAIT_DEFAULTS,
        PERSONA_TRAIT_FIELDS,
        Provider,
        build_playground_hint,
        cultural_prior_choices,
        cultural_prior_trait_values,
        environment_note,
        host_key_active,
        load_environment_presets,
        persona_choices,
        persona_trait_values,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
    )
except ImportError:  # pragma: no cover - Hugging Face runs app.py as a script.
    from simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        PERSONA_TRAIT_DEFAULTS,
        PERSONA_TRAIT_FIELDS,
        Provider,
        build_playground_hint,
        cultural_prior_choices,
        cultural_prior_trait_values,
        environment_note,
        host_key_active,
        load_environment_presets,
        persona_choices,
        persona_trait_values,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
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
        "timeline": "Timeline",
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
ENVIRONMENT_PRESETS = load_environment_presets()
GRAPH_HEIGHT_PX = 620
TIMELINE_MAX_HEIGHT_PX = 360

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


def _cultural_prior_choices(language: str) -> list[tuple[str, str]]:
    return cultural_prior_choices(language, include_blank=True)


def _provider_choices(language: str) -> list[str]:
    labels = LABELS[language]
    return [labels["replay"], "OpenAI", "Anthropic"]


def _normalize_provider(provider: str) -> Provider:
    if provider in {LABELS["ko"]["replay"], LABELS["en"]["replay"]}:
        return "Replay only"
    if provider == "OpenAI":
        return "OpenAI"
    if provider == "Anthropic":
        return "Anthropic"
    return "Replay only"


def _trait_slider(
    field_name: str,
    labels: dict[str, str],
) -> gr.Slider:
    return gr.Slider(
        label=labels[field_name],
        info=labels[f"{field_name}_info"],
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        value=float(PERSONA_TRAIT_DEFAULTS[field_name]),
        elem_id=f"trait-{field_name}",
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
) -> tuple[str, go.Figure, str, str, str, str]:
    expected_with_language = len(PERSONA_TRAIT_FIELDS) + 3
    expected_without_language = len(PERSONA_TRAIT_FIELDS) + 2
    if len(trait_and_runtime) == expected_with_language:
        *trait_values, ticks, agent_count, language_choice = trait_and_runtime
    elif len(trait_and_runtime) == expected_without_language:
        *trait_values, ticks, agent_count = trait_and_runtime
        language_choice = KOREAN_CHOICE
    else:  # pragma: no cover - defensive guard
        raise ValueError(
            f"expected {expected_with_language} or {expected_without_language} personality/runtime values, got {len(trait_and_runtime)}"
        )

    language = _language_key(str(language_choice))
    personality_overrides = {
        field_name: float(value)
        for field_name, value in zip(PERSONA_TRAIT_FIELDS, trait_values, strict=True)
    }
    result = run_playground_scenario(
        scenario_name=scenario_name,
        provider=_normalize_provider(provider),
        api_key=api_key,
        model=model,
        primary_name=primary_name,
        primary_age=int(primary_age),
        openness=float(personality_overrides["openness"]),
        conscientiousness=float(personality_overrides["conscientiousness"]),
        extraversion=float(personality_overrides["extraversion"]),
        agreeableness=float(personality_overrides["agreeableness"]),
        neuroticism=float(personality_overrides["neuroticism"]),
        personality_overrides=personality_overrides,
        ticks=int(ticks),
        agent_count=int(agent_count),
        environment_preset_id=environment_preset_id,
        cultural_prior_id=cultural_prior_id,
        language=language,
    )
    host_provider = host_key_active(_normalize_provider(provider), api_key)
    if language == "ko":
        summary = (
            f"모드: {result.mode} | 에이전트: {result.agent_count}명 | "
            f"틱: {result.tick_count} | 로그 항목: {result.log_count}"
        )
        if host_provider:
            summary += f" | (Celovin 호스트 {host_provider} 키 사용 중 - 데모 전용)"
    else:
        summary = (
            f"Mode: {result.mode} | Agents: {result.agent_count} | "
            f"Ticks: {result.tick_count} | Log entries: {result.log_count}"
        )
        if host_provider:
            summary += f" | (Celovin host {host_provider} key in use - demo only)"
    return (
        result.timeline_markdown,
        _relationship_figure(result.relationship_rows, language=language),
        result.monologue_markdown,
        result.jsonl,
        result.download_path,
        summary,
    )


def _scenario_agent_count_update(scenario_name: str) -> dict[str, Any]:
    return gr.update(value=scenario_default_agent_count(scenario_name))


def _apply_persona_preset(preset_id: str | None) -> list[dict[str, Any]]:
    values = persona_trait_values(preset_id, PERSONA_TRAIT_FIELDS)
    if values is None:
        return [gr.update() for _ in PERSONA_TRAIT_FIELDS]
    return [gr.update(value=value) for value in values]


def _apply_cultural_prior(prior_id: str | None) -> list[dict[str, Any]]:
    values = cultural_prior_trait_values(prior_id, PERSONA_TRAIT_FIELDS)
    return [gr.update(value=value) for value in values]


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


def _trait_update(field_name: str, labels: dict[str, str]) -> dict[str, Any]:
    return gr.update(label=labels[field_name], info=labels[f"{field_name}_info"])


def _language_updates(
    lang_choice: str,
    current_provider: str | None,
    current_scenario: str | None = None,
    current_environment: str | None = None,
    current_cultural_prior: str | None = None,
    current_persona: str | None = None,
) -> list[Any]:
    key = _language_key(lang_choice)
    labels = LABELS[key]
    provider_value = labels["replay"] if _normalize_provider(current_provider or labels["replay"]) == "Replay only" else current_provider
    environment_value = current_environment or _default_environment_id()
    trait_updates = [_trait_update(field_name, labels) for field_name in PERSONA_TRAIT_FIELDS]
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
        gr.update(label=labels["tier_a_panel"]),
        gr.update(label=labels["extended_panel"]),
        labels["extended_panel_note"],
        gr.update(label=labels["tier_bd_panel"]),
        gr.update(label=labels["tier_c_panel"]),
        labels["dark_tetrad_notice"],
        gr.update(label=labels["tier_e_panel"]),
        gr.update(label=labels["tier_f_panel"]),
        gr.update(label=labels["tier_g_panel"]),
        gr.update(label=labels["name"]),
        gr.update(label=labels["age"]),
        gr.update(
            label=labels["cultural_prior"],
            choices=_cultural_prior_choices(key),
            value=current_cultural_prior or "",
            info=labels["cultural_prior_info"],
        ),
        gr.update(
            label=labels["persona_preset"],
            choices=_persona_choices(key),
            value=current_persona or "",
            info=labels["persona_preset_info"],
        ),
        *trait_updates,
        gr.update(label=labels["agents"], info=labels["agents_info"]),
        gr.update(label=labels["ticks"]),
        _hint_markdown_update(current_scenario, lang_choice, environment_value),
        gr.update(value=labels["run"]),
        gr.update(value=f"#### {labels['export_panel']}"),
        gr.update(label=labels["summary"]),
        gr.update(label=labels["timeline"]),
        gr.update(label=labels["graph"]),
        gr.update(label=labels["monologue_panel"]),
        labels["monologue_empty"],
        gr.update(label=labels["jsonl"]),
        gr.update(label=labels["download"]),
        gr.update(label=labels["lang"]),
    ]


def _relationship_figure(rows: list[dict[str, Any]], *, language: str = "en") -> go.Figure:
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

    trust_lookup: dict[str, float] = {}
    for row in rows:
        trust_lookup[str(row["source"])] = max(
            trust_lookup.get(str(row["source"]), 0.0),
            float(row.get("trust", 0.5)),
        )

    node_x = [positions[agent][0] for agent in agents]
    node_y = [positions[agent][1] for agent in agents]
    node_z = [positions[agent][2] for agent in agents]
    node_text = list(agents)
    node_color = [trust_lookup.get(agent, 0.5) for agent in agents]

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

        trait_sliders: dict[str, gr.Slider] = {}
        agent_panel = gr.Accordion(
            labels["agent_panel"],
            open=True,
            elem_id="personality-panel",
        )
        with agent_panel:
            with gr.Row():
                primary_name = gr.Textbox(label=labels["name"], value="Mina")
                primary_age = gr.Slider(
                    label=labels["age"],
                    minimum=12,
                    maximum=80,
                    step=1,
                    value=21,
                )

            cultural_prior = gr.Dropdown(
                label=labels["cultural_prior"],
                choices=_cultural_prior_choices("ko"),
                value="",
                info=labels["cultural_prior_info"],
                elem_id="cultural-prior-dropdown",
            )

            persona_preset = gr.Dropdown(
                label=labels["persona_preset"],
                choices=_persona_choices("ko"),
                value="",
                info=labels["persona_preset_info"],
                elem_id="persona-preset-dropdown",
            )

            tier_a_panel = gr.Accordion(labels["tier_a_panel"], open=True, elem_id="tier-a-panel")
            with tier_a_panel:
                with gr.Row():
                    for field_name in BIG_FIVE_FIELDS[:3]:
                        trait_sliders[field_name] = _trait_slider(field_name, labels)
                with gr.Row():
                    for field_name in BIG_FIVE_FIELDS[3:]:
                        trait_sliders[field_name] = _trait_slider(field_name, labels)

            extended_panel = gr.Accordion(
                labels["extended_panel"],
                open=True,
                elem_id="extended-personality-panel",
            )
            with extended_panel:
                extended_panel_note = gr.Markdown(labels["extended_panel_note"])

                tier_bd_panel = gr.Accordion(labels["tier_bd_panel"], open=False, elem_id="tier-bd-panel")
                with tier_bd_panel, gr.Row():
                    for field_name in TIER_BD_FIELDS:
                        trait_sliders[field_name] = _trait_slider(field_name, labels)

                tier_c_panel = gr.Accordion(labels["tier_c_panel"], open=False, elem_id="tier-c-panel")
                with tier_c_panel:
                    dark_tetrad_notice = gr.Markdown(labels["dark_tetrad_notice"])
                    with gr.Row():
                        for field_name in TIER_C_FIELDS:
                            trait_sliders[field_name] = _trait_slider(field_name, labels)

                tier_e_panel = gr.Accordion(labels["tier_e_panel"], open=False, elem_id="tier-e-panel")
                with tier_e_panel, gr.Row():
                    for field_name in TIER_E_FIELDS:
                        trait_sliders[field_name] = _trait_slider(field_name, labels)

                tier_f_panel = gr.Accordion(labels["tier_f_panel"], open=False, elem_id="tier-f-panel")
                with tier_f_panel, gr.Row():
                    for field_name in TIER_F_FIELDS:
                        trait_sliders[field_name] = _trait_slider(field_name, labels)

                tier_g_panel = gr.Accordion(labels["tier_g_panel"], open=False, elem_id="tier-g-panel")
                with tier_g_panel:
                    for row_fields in TIER_G_ROWS:
                        with gr.Row():
                            for field_name in row_fields:
                                trait_sliders[field_name] = _trait_slider(field_name, labels)

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

        scenario_hint = gr.Markdown(
            _hint_markdown_update(
                default_scenario,
                LANGUAGE_CHOICES[0],
                _default_environment_id(),
            ),
            elem_classes=["knoema-hint"],
        )

        run_button = gr.Button(labels["run"], variant="primary", elem_id="run-button")
        summary = gr.Textbox(label=labels["summary"], interactive=False)
        graph = gr.Plot(label=labels["graph"], elem_id="relationship-graph")
        timeline = gr.Markdown(
            label=labels["timeline"],
            elem_id="timeline-panel",
            min_height=TIMELINE_MAX_HEIGHT_PX,
            max_height=TIMELINE_MAX_HEIGHT_PX,
            container=True,
        )
        monologue_panel = gr.Accordion(
            labels["monologue_panel"],
            open=False,
            elem_id="inner-monologue-panel",
        )
        with monologue_panel:
            monologue_view = gr.Markdown(labels["monologue_empty"])

        with gr.Column(elem_id="export-panel"):
            export_heading = gr.Markdown(f"#### {labels['export_panel']}")
            jsonl = gr.Code(label=labels["jsonl"], language="json")
            download = gr.File(label=labels["download"])

        language_outputs: list[gr.components.Component | gr.layouts.Accordion | gr.Markdown] = [
            header,
            scenario,
            environment_preset,
            provider,
            api_key,
            model,
            agent_panel,
            tier_a_panel,
            extended_panel,
            extended_panel_note,
            tier_bd_panel,
            tier_c_panel,
            dark_tetrad_notice,
            tier_e_panel,
            tier_f_panel,
            tier_g_panel,
            primary_name,
            primary_age,
            cultural_prior,
            persona_preset,
            *[trait_sliders[field_name] for field_name in PERSONA_TRAIT_FIELDS],
            agent_count,
            ticks,
            scenario_hint,
            run_button,
            export_heading,
            summary,
            timeline,
            graph,
            monologue_panel,
            monologue_view,
            jsonl,
            download,
            language,
        ]

        def _switch(lang_choice: str) -> list[Any]:
            return _language_updates(
                lang_choice,
                provider.value,
                scenario.value,
                environment_preset.value,
                cultural_prior.value,
                persona_preset.value,
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
        environment_preset.change(
            _hint_markdown_update,
            inputs=[scenario, language, environment_preset],
            outputs=[scenario_hint],
        )
        cultural_prior.change(
            _apply_cultural_prior,
            inputs=[cultural_prior],
            outputs=[trait_sliders[field_name] for field_name in PERSONA_TRAIT_FIELDS],
        )
        persona_preset.change(
            _apply_persona_preset,
            inputs=[persona_preset],
            outputs=[trait_sliders[field_name] for field_name in PERSONA_TRAIT_FIELDS],
        )
        run_button.click(
            _run,
            inputs=[
                scenario,
                environment_preset,
                cultural_prior,
                provider,
                api_key,
                model,
                primary_name,
                primary_age,
                *[trait_sliders[field_name] for field_name in PERSONA_TRAIT_FIELDS],
                ticks,
                agent_count,
                language,
            ],
            outputs=[timeline, graph, monologue_view, jsonl, download, summary],
            api_name="run",
        )

    demo.queue()
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860)
