"""Gradio app for the Knoema Playground."""

from __future__ import annotations

from typing import Any

import gradio as gr
import plotly.graph_objects as go

try:
    from .simulation import Provider, host_key_active, run_playground_scenario, scenario_choices
except ImportError:  # pragma: no cover - Hugging Face runs app.py as a script.
    from simulation import Provider, host_key_active, run_playground_scenario, scenario_choices


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
        language=lang,
    )
    host_provider = host_key_active(_normalize_provider(provider), api_key)
    if lang == "ko":
        summary = (
            f"모드: {result.mode} | 에이전트: {result.agent_count}명 | "
            f"틱: {result.tick_count} | 로그 항목: {result.log_count}개"
        )
        if host_provider:
            summary += f" | (셀로빈 호스팅 {host_provider} 키 사용 중 — 데모 한정)"
    else:
        summary = (
            f"Mode: {result.mode} | Agents: {result.agent_count} | "
            f"Ticks: {result.tick_count} | Log entries: {result.log_count}"
        )
        if host_provider:
            summary += f" | (Celovin host {host_provider} key in use — demo only)"
    return (
        result.timeline_markdown,
        _relationship_figure(result.relationship_rows, language=lang),
        result.jsonl,
        result.download_path,
        summary,
    )


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
        "conscientiousness": "성실성",
        "extraversion": "외향성",
        "agreeableness": "친화성",
        "neuroticism": "신경성",
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
        "conscientiousness": "Conscientiousness",
        "extraversion": "Extraversion",
        "agreeableness": "Agreeableness",
        "neuroticism": "Neuroticism",
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


FOOTER_CSS = """
footer {display: none !important;}
.footer {display: none !important;}
.api-docs {display: none !important;}
"""


def build_app() -> gr.Blocks:
    L = LABELS["ko"]
    with gr.Blocks(title="Knoema Playground", css=FOOTER_CSS, analytics_enabled=False) as demo:
        with gr.Row():
            language = gr.Radio(
                label=L["lang"],
                choices=["한국어", "English"],
                value="한국어",
                scale=0,
            )
        header = gr.Markdown(L["header"])
        with gr.Row():
            scenario = gr.Dropdown(
                label=L["scenario"],
                choices=scenario_choices(),
                value=scenario_choices()[0],
            )
            provider = gr.Radio(
                label=L["mode"],
                choices=[L["replay"], "OpenAI", "Anthropic"],
                value=L["replay"],
            )
        with gr.Row():
            api_key = gr.Textbox(
                label=L["api_key"],
                type="password",
                placeholder=L["api_key_ph"],
            )
            model = gr.Dropdown(
                label=L["model"],
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
        agent_panel = gr.Accordion(L["agent_panel"], open=True)
        with agent_panel:
            with gr.Row():
                primary_name = gr.Textbox(label=L["name"], value="Mina")
                primary_age = gr.Slider(label=L["age"], minimum=12, maximum=80, step=1, value=21)
            with gr.Row():
                openness = gr.Slider(label=L["openness"], minimum=0, maximum=1, value=0.75)
                conscientiousness = gr.Slider(
                    label=L["conscientiousness"],
                    minimum=0,
                    maximum=1,
                    value=0.62,
                )
                extraversion = gr.Slider(label=L["extraversion"], minimum=0, maximum=1, value=0.52)
            with gr.Row():
                agreeableness = gr.Slider(label=L["agreeableness"], minimum=0, maximum=1, value=0.68)
                neuroticism = gr.Slider(label=L["neuroticism"], minimum=0, maximum=1, value=0.36)
                ticks = gr.Slider(label=L["ticks"], minimum=1, maximum=24, step=1, value=4)
        run_button = gr.Button(L["run"], variant="primary")
        summary = gr.Textbox(label=L["summary"], interactive=False)
        with gr.Row():
            timeline = gr.Markdown(label=L["timeline"])
            graph = gr.Plot(label=L["graph"])
        jsonl = gr.Code(label=L["jsonl"], language="json")
        download = gr.File(label=L["download"])

        def _switch(lang_choice: str) -> list[Any]:
            key = "ko" if lang_choice == "한국어" else "en"
            t = LABELS[key]
            current_provider = provider.value
            new_provider_choices = [t["replay"], "OpenAI", "Anthropic"]
            new_provider_value = (
                t["replay"] if current_provider in (LABELS["ko"]["replay"], LABELS["en"]["replay"])
                else current_provider
            )
            return [
                t["header"],
                gr.update(label=t["scenario"]),
                gr.update(label=t["mode"], choices=new_provider_choices, value=new_provider_value),
                gr.update(label=t["api_key"], placeholder=t["api_key_ph"]),
                gr.update(label=t["model"]),
                gr.update(label=t["agent_panel"]),
                gr.update(label=t["name"]),
                gr.update(label=t["age"]),
                gr.update(label=t["openness"]),
                gr.update(label=t["conscientiousness"]),
                gr.update(label=t["extraversion"]),
                gr.update(label=t["agreeableness"]),
                gr.update(label=t["neuroticism"]),
                gr.update(label=t["ticks"]),
                gr.update(value=t["run"]),
                gr.update(label=t["summary"]),
                gr.update(label=t["timeline"]),
                gr.update(label=t["graph"]),
                gr.update(label=t["jsonl"]),
                gr.update(label=t["download"]),
                gr.update(label=t["lang"]),
            ]

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
                language,
            ],
            outputs=[timeline, graph, jsonl, download, summary],
            api_name="run",
        )
    demo.queue()
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="0.0.0.0", server_port=7860)
