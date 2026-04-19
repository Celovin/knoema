"""Gradio app for the Knoema Playground."""

from __future__ import annotations

from typing import Any

import gradio as gr
import plotly.graph_objects as go

try:
    from .simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        Provider,
        host_key_active,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
    )
except ImportError:  # pragma: no cover - Hugging Face runs app.py as a script.
    from simulation import (
        AGENT_COUNT_MAX,
        AGENT_COUNT_MIN,
        Provider,
        host_key_active,
        run_playground_scenario,
        scenario_choices,
        scenario_default_agent_count,
    )


LANGUAGE_CHOICES = ["한국어", "English"]


def _normalize_provider(provider: str) -> Provider:
    if provider in {"재생 전용", "Replay only"}:
        return "Replay only"
    if provider == "OpenAI":
        return "OpenAI"
    if provider == "Anthropic":
        return "Anthropic"
    return "Replay only"


def _run(
    scenario_name: str,
    provider: str,
    api_key: str,
    model: str,
    primary_name: str,
    primary_age: int,
    openness: float,
    conscientiousness: float,
    extraversion: float,
    agreeableness: float,
    neuroticism: float,
    ticks: int,
    agent_count: int,
    language_choice: str = "한국어",
) -> tuple[str, go.Figure, str, str, str]:
    lang = "ko" if language_choice == "한국어" else "en"
    result = run_playground_scenario(
        scenario_name=scenario_name,
        provider=_normalize_provider(provider),
        api_key=api_key,
        model=model,
        primary_name=primary_name,
        primary_age=primary_age,
        openness=openness,
        conscientiousness=conscientiousness,
        extraversion=extraversion,
        agreeableness=agreeableness,
        neuroticism=neuroticism,
        ticks=ticks,
        agent_count=agent_count,
        language=lang,
    )
    host_provider = host_key_active(_normalize_provider(provider), api_key)
    if lang == "ko":
        summary = (
            f"모드: {result.mode} | 에이전트: {result.agent_count}명 | "
            f"틱: {result.tick_count} | 로그 항목: {result.log_count}개"
        )
        if host_provider:
            summary += f" | (셀로빈 호스팅 {host_provider} 키 사용 중 - 데모 한정)"
    else:
        summary = (
            f"Mode: {result.mode} | Agents: {result.agent_count} | "
            f"Ticks: {result.tick_count} | Log entries: {result.log_count}"
        )
        if host_provider:
            summary += f" | (Celovin host {host_provider} key in use - demo only)"
    return (
        result.timeline_markdown,
        _relationship_figure(result.relationship_rows, language=lang),
        result.jsonl,
        result.download_path,
        summary,
    )


def _scenario_agent_count_update(scenario_name: str) -> dict[str, Any]:
    return gr.update(value=scenario_default_agent_count(scenario_name))


def _language_updates(lang_choice: str, current_provider: str | None) -> list[Any]:
    key = "ko" if lang_choice == LANGUAGE_CHOICES[0] else "en"
    labels = LABELS[key]
    replay_values = (LABELS["ko"]["replay"], LABELS["en"]["replay"])
    provider_value = labels["replay"] if current_provider in replay_values else current_provider
    return [
        labels["header"],
        gr.update(label=labels["scenario"]),
        gr.update(
            label=labels["mode"],
            choices=[labels["replay"], "OpenAI", "Anthropic"],
            value=provider_value,
        ),
        gr.update(label=labels["api_key"], placeholder=labels["api_key_ph"]),
        gr.update(label=labels["model"]),
        gr.update(label=labels["agent_panel"]),
        gr.update(label=labels["name"]),
        gr.update(label=labels["age"]),
        gr.update(label=labels["openness"], info=labels["openness_info"]),
        gr.update(
            label=labels["conscientiousness"],
            info=labels["conscientiousness_info"],
        ),
        gr.update(label=labels["extraversion"], info=labels["extraversion_info"]),
        gr.update(label=labels["agreeableness"], info=labels["agreeableness_info"]),
        gr.update(label=labels["neuroticism"], info=labels["neuroticism_info"]),
        gr.update(label=labels["agents"], info=labels["agents_info"]),
        gr.update(label=labels["ticks"]),
        gr.update(value=labels["run"]),
        gr.update(label=labels["summary"]),
        gr.update(label=labels["timeline"]),
        gr.update(label=labels["graph"]),
        gr.update(label=labels["jsonl"]),
        gr.update(label=labels["download"]),
        gr.update(label=labels["lang"]),
    ]


def _relationship_figure(rows: list[dict[str, Any]], *, language: str = "en") -> go.Figure:
    title = "관계 그래프" if language == "ko" else "Relationship graph"
    empty_msg = (
        "관계 엣지가 아직 없습니다. 틱 수를 늘리거나 대화형 시나리오를 사용해 보세요."
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
            trust_lookup.get(str(row["source"]), 0.0), float(row.get("trust", 0.5))
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
                hovertext=_node_hover_text(agents, rows),
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


def _node_hover_text(agents: list[str], rows: list[dict[str, Any]]) -> list[str]:
    hover: list[str] = []
    for agent in agents:
        outgoing = [row for row in rows if row["source"] == agent]
        if not outgoing:
            hover.append(f"{agent}<br>No outgoing relationships")
            continue
        lines = [agent]
        for row in outgoing:
            lines.append(
                f"{row['target']}: trust={row['trust']}, weight={row['weight']}, "
                f"type={row['relationship_type']}"
            )
        hover.append("<br>".join(lines))
    return hover


LABELS = {
    "ko": {
        "header": (
            "# Knoema Playground\n\n"
            "브라우저에서 지속형 에이전트 시뮬레이션을 짧게 실행합니다. **재생 전용**은 "
            "API 키 없이 결정론적으로 동작하며, OpenAI 또는 Anthropic 키를 입력하면 "
            "라이브 LLM 호출이 가능합니다. API 키는 현재 요청에만 사용되고 디스크에 저장되지 않습니다."
        ),
        "scenario": "시나리오",
        "mode": "모드",
        "replay": "재생 전용",
        "api_key": "API 키",
        "api_key_ph": "OpenAI/Anthropic 사용 시 필수, 재생 전용은 비워두세요",
        "model": "모델",
        "agent_panel": "주 에이전트 설정",
        "name": "이름",
        "age": "나이",
        "openness": "개방성",
        "openness_info": "호기심과 새로운 경험에 대한 개방성. 높을수록 변화에 더 잘 적응합니다.",
        "conscientiousness": "성실성",
        "conscientiousness_info": "자기통제와 목표 지향성. 높을수록 계획을 꾸준히 실행합니다.",
        "extraversion": "외향성",
        "extraversion_info": "사교성과 자극 추구 성향. 높을수록 사람과 활동에서 에너지를 얻습니다.",
        "agreeableness": "친화성",
        "agreeableness_info": "협력과 공감 성향. 높을수록 갈등을 줄이고 타인을 배려합니다.",
        "neuroticism": "정서 불안정성",
        "neuroticism_info": "스트레스와 부정적 감정에 대한 민감성. 높을수록 걱정이나 짜증이 잦습니다.",
        "agents": "에이전트 수",
        "agents_info": (
            "시나리오 기본값보다 크게 설정하면 마지막 페르소나를 바탕으로 추가 에이전트를 자동 생성합니다."
        ),
        "ticks": "틱 수",
        "run": "시뮬레이션 실행",
        "summary": "실행 요약",
        "timeline": "타임라인",
        "graph": "관계 그래프",
        "jsonl": "JSONL 로그",
        "download": "JSONL 다운로드",
        "lang": "언어",
    },
    "en": {
        "header": (
            "# Knoema Playground\n\n"
            "Run a short persistent-agent simulation in the browser. Use **Replay only** "
            "for a no-key deterministic demo, or provide your own API key for a live "
            "LLM-backed run. API keys are used only for the current request and are not "
            "written to disk."
        ),
        "scenario": "Scenario",
        "mode": "Mode",
        "replay": "Replay only",
        "api_key": "API key",
        "api_key_ph": "Required for OpenAI/Anthropic, leave blank for Replay only",
        "model": "Model",
        "agent_panel": "Primary agent controls",
        "name": "Name",
        "age": "Age",
        "openness": "Openness",
        "openness_info": "Curiosity and openness to new experience. Higher = more receptive to change.",
        "conscientiousness": "Conscientiousness",
        "conscientiousness_info": (
            "Self-discipline and goal-directedness. Higher = more consistent follow-through."
        ),
        "extraversion": "Extraversion",
        "extraversion_info": "Sociability and stimulation seeking. Higher = energized by people and events.",
        "agreeableness": "Agreeableness",
        "agreeableness_info": (
            "Cooperation and empathy. Higher = avoids conflict and prioritizes others."
        ),
        "neuroticism": "Emotional volatility (Neuroticism)",
        "neuroticism_info": (
            "Sensitivity to stress and negative emotion. Higher = more frequent worry or irritation."
        ),
        "agents": "Agents",
        "agents_info": (
            "How many agents take part. Extras above the scenario default are auto-generated."
        ),
        "ticks": "Ticks",
        "run": "Run simulation",
        "summary": "Run summary",
        "timeline": "Timeline",
        "graph": "Relationship graph",
        "jsonl": "JSONL log",
        "download": "Download JSONL",
        "lang": "Language",
    },
}


GRAPH_HEIGHT_PX = 620
TIMELINE_MAX_HEIGHT_PX = 360


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
"""


def build_app() -> gr.Blocks:
    labels = LABELS["ko"]
    default_scenario = scenario_choices()[0]
    with gr.Blocks(title="Knoema Playground", css=FOOTER_CSS, analytics_enabled=False) as demo:
        with gr.Row():
            language = gr.Radio(
                label=labels["lang"],
                choices=LANGUAGE_CHOICES,
                value=LANGUAGE_CHOICES[0],
                scale=0,
            )
        header = gr.Markdown(labels["header"])
        with gr.Row():
            scenario = gr.Dropdown(
                label=labels["scenario"],
                choices=scenario_choices(),
                value=default_scenario,
            )
            provider = gr.Radio(
                label=labels["mode"],
                choices=[labels["replay"], "OpenAI", "Anthropic"],
                value=labels["replay"],
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
        agent_panel = gr.Accordion(labels["agent_panel"], open=True)
        with agent_panel:
            with gr.Row():
                primary_name = gr.Textbox(label=labels["name"], value="Mina")
                primary_age = gr.Slider(
                    label=labels["age"], minimum=12, maximum=80, step=1, value=21
                )
            with gr.Row():
                openness = gr.Slider(
                    label=labels["openness"],
                    info=labels["openness_info"],
                    minimum=0,
                    maximum=1,
                    value=0.75,
                )
                conscientiousness = gr.Slider(
                    label=labels["conscientiousness"],
                    info=labels["conscientiousness_info"],
                    minimum=0,
                    maximum=1,
                    value=0.62,
                )
                extraversion = gr.Slider(
                    label=labels["extraversion"],
                    info=labels["extraversion_info"],
                    minimum=0,
                    maximum=1,
                    value=0.52,
                )
            with gr.Row():
                agreeableness = gr.Slider(
                    label=labels["agreeableness"],
                    info=labels["agreeableness_info"],
                    minimum=0,
                    maximum=1,
                    value=0.68,
                )
                neuroticism = gr.Slider(
                    label=labels["neuroticism"],
                    info=labels["neuroticism_info"],
                    minimum=0,
                    maximum=1,
                    value=0.36,
                )
                agent_count = gr.Slider(
                    label=labels["agents"],
                    info=labels["agents_info"],
                    minimum=AGENT_COUNT_MIN,
                    maximum=AGENT_COUNT_MAX,
                    step=1,
                    value=scenario_default_agent_count(default_scenario),
                )
            with gr.Row():
                ticks = gr.Slider(
                    label=labels["ticks"], minimum=1, maximum=24, step=1, value=4
                )
        run_button = gr.Button(labels["run"], variant="primary")
        summary = gr.Textbox(label=labels["summary"], interactive=False)
        graph = gr.Plot(label=labels["graph"], elem_id="relationship-graph")
        timeline = gr.Markdown(
            label=labels["timeline"],
            elem_id="timeline-panel",
            min_height=TIMELINE_MAX_HEIGHT_PX,
            max_height=TIMELINE_MAX_HEIGHT_PX,
            container=True,
        )
        jsonl = gr.Code(label=labels["jsonl"], language="json")
        download = gr.File(label=labels["download"])

        def _switch(lang_choice: str) -> list[Any]:
            return _language_updates(lang_choice, provider.value)

        language.change(
            _switch,
            inputs=[language],
            outputs=[
                header,
                scenario,
                provider,
                api_key,
                model,
                agent_panel,
                primary_name,
                primary_age,
                openness,
                conscientiousness,
                extraversion,
                agreeableness,
                neuroticism,
                agent_count,
                ticks,
                run_button,
                summary,
                timeline,
                graph,
                jsonl,
                download,
                language,
            ],
        )
        scenario.change(
            _scenario_agent_count_update,
            inputs=[scenario],
            outputs=[agent_count],
        )
        run_button.click(
            _run,
            inputs=[
                scenario,
                provider,
                api_key,
                model,
                primary_name,
                primary_age,
                openness,
                conscientiousness,
                extraversion,
                agreeableness,
                neuroticism,
                ticks,
                agent_count,
                language,
            ],
            outputs=[timeline, graph, jsonl, download, summary],
            api_name="run",
        )
    demo.queue()
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860)
