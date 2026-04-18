"""Gradio app for the Knoema Playground."""

from __future__ import annotations

from typing import Any

import gradio as gr
import plotly.graph_objects as go

try:
    from .simulation import Provider, run_playground_scenario, scenario_choices
except ImportError:  # pragma: no cover - Hugging Face runs app.py as a script.
    from simulation import Provider, run_playground_scenario, scenario_choices


def _run(
    scenario_name: str,
    provider: Provider,
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
) -> tuple[str, go.Figure, str, str, str]:
    result = run_playground_scenario(
        scenario_name=scenario_name,
        provider=provider,
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
    )
    summary = (
        f"Mode: {result.mode} | Agents: {result.agent_count} | "
        f"Ticks: {result.tick_count} | Log entries: {result.log_count}"
    )
    return (
        result.timeline_markdown,
        _relationship_figure(result.relationship_rows),
        result.jsonl,
        result.download_path,
        summary,
    )


def _relationship_figure(rows: list[dict[str, Any]]) -> go.Figure:
    if not rows:
        figure = go.Figure()
        figure.update_layout(
            title="Relationship graph",
            annotations=[
                {
                    "text": "No relationship edges yet. Run more ticks or use a conversational scenario.",
                    "showarrow": False,
                }
            ],
        )
        return figure

    agents = sorted({str(row["source"]) for row in rows} | {str(row["target"]) for row in rows})
    positions = _circle_positions(agents)
    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for row in rows:
        source = str(row["source"])
        target = str(row["target"])
        sx, sy = positions[source]
        tx, ty = positions[target]
        edge_x.extend([sx, tx, None])
        edge_y.extend([sy, ty, None])

    node_x = [positions[agent][0] for agent in agents]
    node_y = [positions[agent][1] for agent in agents]
    node_text = list(agents)
    figure = go.Figure(
        data=[
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line={"width": 1.5, "color": "#64748b"},
                hoverinfo="none",
            ),
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                text=node_text,
                textposition="top center",
                marker={"size": 18, "color": "#2563eb"},
                hovertext=_node_hover_text(agents, rows),
                hoverinfo="text",
            ),
        ]
    )
    figure.update_layout(
        title="Relationship graph",
        showlegend=False,
        xaxis={"visible": False},
        yaxis={"visible": False},
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
    )
    return figure


def _circle_positions(agents: list[str]) -> dict[str, tuple[float, float]]:
    import math

    count = max(1, len(agents))
    return {
        agent: (
            math.cos((2 * math.pi * index) / count),
            math.sin((2 * math.pi * index) / count),
        )
        for index, agent in enumerate(agents)
    }


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


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Knoema Playground") as demo:
        gr.Markdown(
            """
            # Knoema Playground

            Run a short persistent-agent simulation in the browser. Use **Replay only**
            for a no-key deterministic demo, or provide your own API key for a live LLM-backed run.
            API keys are used only for the current request and are not written to disk.
            """
        )
        with gr.Row():
            scenario = gr.Dropdown(
                label="Scenario",
                choices=scenario_choices(),
                value=scenario_choices()[0],
            )
            provider = gr.Radio(
                label="Mode",
                choices=["Replay only", "OpenAI", "Anthropic"],
                value="Replay only",
            )
        with gr.Row():
            api_key = gr.Textbox(label="API key", type="password", placeholder="Optional")
            model = gr.Textbox(label="Model", value="gpt-4o-mini")
        with gr.Accordion("Primary agent controls", open=True):
            with gr.Row():
                primary_name = gr.Textbox(label="Name", value="Mina")
                primary_age = gr.Slider(label="Age", minimum=12, maximum=80, step=1, value=21)
            with gr.Row():
                openness = gr.Slider(label="Openness", minimum=0, maximum=1, value=0.75)
                conscientiousness = gr.Slider(
                    label="Conscientiousness",
                    minimum=0,
                    maximum=1,
                    value=0.62,
                )
                extraversion = gr.Slider(label="Extraversion", minimum=0, maximum=1, value=0.52)
            with gr.Row():
                agreeableness = gr.Slider(label="Agreeableness", minimum=0, maximum=1, value=0.68)
                neuroticism = gr.Slider(label="Neuroticism", minimum=0, maximum=1, value=0.36)
                ticks = gr.Slider(label="Ticks", minimum=1, maximum=24, step=1, value=4)
        run_button = gr.Button("Run simulation", variant="primary")
        summary = gr.Textbox(label="Run summary", interactive=False)
        with gr.Row():
            timeline = gr.Markdown(label="Timeline")
            graph = gr.Plot(label="Relationship graph")
        jsonl = gr.Code(label="JSONL log", language="json")
        download = gr.File(label="Download JSONL")

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
            ],
            outputs=[timeline, graph, jsonl, download, summary],
        )
    return demo


if __name__ == "__main__":
    build_app().launch()
