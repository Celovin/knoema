"""Build a meeting-ready PDF preview of the Knoema technical report."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "knoema_technical_report.pdf"


def build_pdf() -> None:
    styles = get_styles()
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        rightMargin=0.72 * inch,
        leftMargin=0.72 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.72 * inch,
        title="Knoema Engine Technical Report",
        author="Celovin",
    )
    story = [
        Paragraph("Knoema Engine", styles["Title"]),
        Paragraph(
            "A Lightweight LLM-Based Multi-Agent Social Simulation Runtime",
            styles["Subtitle"],
        ),
        Paragraph("Celovin | hello@celovin.com | April 2026", styles["Meta"]),
        Spacer(1, 0.2 * inch),
    ]

    for heading, body in sections():
        story.append(Paragraph(heading, styles["Heading2"]))
        for paragraph in body:
            if isinstance(paragraph, list):
                story.append(make_table(paragraph, styles))
            else:
                story.append(Paragraph(paragraph, styles["Body"]))
            story.append(Spacer(1, 0.08 * inch))
        if heading in {"4. Implementation Snapshot"}:
            story.append(PageBreak())

    story.append(Paragraph("References", styles["Heading2"]))
    for reference in references():
        story.append(Paragraph(reference, styles["Reference"]))
        story.append(Spacer(1, 0.04 * inch))

    document.build(story, onFirstPage=footer, onLaterPages=footer)


def get_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#111827"),
            spaceAfter=8,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#374151"),
            spaceAfter=4,
        ),
        "Meta": ParagraphStyle(
            "Meta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#6B7280"),
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1F2937"),
        ),
        "Reference": ParagraphStyle(
            "Reference",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            leftIndent=12,
            firstLineIndent=-12,
            textColor=colors.HexColor("#1F2937"),
        ),
        "Table": ParagraphStyle(
            "Table",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#111827"),
        ),
    }


def make_table(rows: list[list[str]], styles: dict[str, ParagraphStyle]) -> Table:
    table = Table(
        [[Paragraph(cell, styles["Table"]) for cell in row] for row in rows],
        colWidths=[1.45 * inch, 2.45 * inch, 2.45 * inch],
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def footer(canvas, document) -> None:  # type: ignore[no-untyped-def]
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(0.72 * inch, 0.42 * inch, "Knoema Engine Technical Report")
    canvas.drawRightString(7.78 * inch, 0.42 * inch, f"Page {document.page}")
    canvas.restoreState()


def sections() -> list[tuple[str, list[str | list[list[str]]]]]:
    return [
        (
            "Abstract",
            [
                "Knoema Engine is an early-stage Python runtime for LLM-based multi-agent social simulation. It combines persona prompts, hierarchical memory, directed social relationships, environment context, PAD emotion state, LLM-backed decision generation, and replayable logs behind a compact API. The MVP demonstrates one shared runtime across persistent-memory game NPCs, fictional public-safety scenario replay, and reproducible academic social simulation.",
            ],
        ),
        (
            "1. Introduction",
            [
                "LLM-based agents make it practical to represent social behavior as language-rich decisions over memory, goals, and environment state. Knoema Engine targets a narrow engineering goal: a small reusable runtime that can be installed as a Python package, demonstrated in notebooks, inspected through a dashboard, and connected to game engines.",
                "The first implementation focuses on reliable boundaries instead of scale. All demos run without API keys through deterministic local responders, while the same interfaces can be connected to Anthropic or OpenAI clients. Simulation logs export as JSONL so notebooks, dashboards, and adapters consume the same artifact.",
            ],
        ),
        (
            "2. Related Work",
            [
                "Generative Agents showed that natural-language memory, planning, and reflection can produce believable social behavior in interactive environments. Concordia frames generative social simulation as grounded interactions among entities. AutoGen focuses on conversable LLM agents for task-oriented applications. Mesa remains a strong classical Python baseline for reproducible agent-based modeling.",
                "Knoema differs by keeping a compact engine API and demonstrating the same runtime across games, synthetic replay research, and academic notebooks.",
            ],
        ),
        (
            "3. Architecture",
            [
                "The core package exposes dataclasses for Personality, Emotion, Memory, Action, and WorldEvent. Higher-level modules compose these types into personas, memory stores, social relationships, environment context, emotion state, and a simulation loop.",
                "Simulation flow: Persona + Memory + Relationship + Environment + Emotion -> DecisionEngine -> LLMGateway -> Action -> Simulator -> JSONL -> Notebooks, Dashboard, Godot Adapter.",
                [
                    ["Module", "Responsibility", "MVP status"],
                    ["Persona", "Identity, values, goals, prompt rendering", "Implemented"],
                    ["Memory", "Short-term FIFO and SQLite + FAISS retrieval", "Implemented"],
                    ["Relationship", "Directed trust, familiarity, and interaction weight", "Implemented"],
                    ["Decision", "Prompt building and strict JSON action parsing", "Implemented"],
                    ["Adapters", "Dashboard and Godot scaffold", "Implemented"],
                ],
            ],
        ),
        (
            "4. Implementation Snapshot",
            [
                "The current repository implements the MVP as an installable Python package named knoema-engine. Source modules live under src/knoema, tests under tests, notebooks under examples, game integration under adapters/godot, and dashboard code under dashboard. The repository also includes dual-language README files, architecture notes, research positioning notes, and GitHub Actions CI.",
                [
                    ["Area", "Files", "Verification"],
                    ["Core package", "src/knoema/*.py", "Unit tests and mypy"],
                    ["Memory", "src/knoema/memory", "Retrieval and persistence tests"],
                    ["Decision loop", "decision.py and llm/", "Mock client tests"],
                    ["Simulation", "simulator.py and events/", "7-day run test"],
                    ["Examples", "examples/*.ipynb", "nbconvert execution"],
                    ["Dashboard", "dashboard/", "Pure logic tests and HTTP smoke test"],
                ],
                "The local verification run before this report passed 52 pytest tests, ruff check ., and mypy src. The GitHub Actions workflow runs the same lint, type, and test gates on Python 3.11 and 3.12. The public repository surface is scanned to keep private planning documents and unrelated entity references out of committed files.",
                "The recommended live demonstration starts with the first notebook, then opens the dashboard with the bundled sample log, and finally shows the Godot adapter directory. This order keeps the narrative concrete: first define agents, then observe exported traces, then show how the same action surface can be consumed by an external runtime.",
                "The repository is private during preparation and is intended to be made public after the first notebook, Godot adapter, and documentation are stable. Runtime artifacts such as logs, SQLite databases, FAISS indexes, checkpoints, and private planning documents are ignored by git.",
            ],
        ),
        (
            "5. MVP Demonstrations",
            [
                [
                    ["Demo", "Purpose", "Verification"],
                    ["Dormitory", "Two synthetic students over seven days", "672 action records"],
                    ["Fictional replay", "Synthetic property incident reconstruction", "Milestone coverage above 0.8"],
                    ["Game NPC", "Cross-session memory retrieval", "Godot-style payload"],
                    ["Dashboard", "JSONL inspection", "52 tests pass"],
                ],
                "The notebooks are demonstration artifacts rather than controlled experiments. They verify that the architecture is runnable, inspectable, and safe to show without private data or API credentials.",
                "The dormitory simulation verifies long-running social interaction and relationship updates. The fictional replay notebook verifies trace consistency against process milestones. The game NPC notebook verifies cross-session memory retrieval and adapter-friendly payloads. The dashboard verifies that exported JSONL can be inspected without rerunning the simulator.",
            ],
        ),
        (
            "6. Safety Boundary and Limitations",
            [
                "The public-safety track is constrained to fictional, synthetic, non-identifying examples. The replay notebook does not estimate risk, identify suspects, or predict future crime. Its milestone coverage metric measures trace consistency against a known synthetic script.",
                "Current limitations include deterministic local responders, a lightweight hash embedding encoder, simple relationship update heuristics, a scaffold-level Godot adapter, and a read-only dashboard.",
                "The next evaluation layer should add model-backed runs, semantic encoder comparisons, larger agent populations, and a review rubric for plausibility, repetitiveness, safety, and trace faithfulness.",
            ],
        ),
        (
            "7. Conclusion",
            [
                "Knoema Engine demonstrates a compact path from LLM-based social simulation research to game and research tooling. The next steps are larger multi-agent scenarios, stronger semantic retrieval, benchmark scripts, richer game-engine adapters, and more formal evaluation protocols for synthetic replay tasks.",
            ],
        ),
    ]


def references() -> list[str]:
    return [
        "Park, J. S. et al. (2023). Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442. https://arxiv.org/abs/2304.03442",
        "Vezhnevets, A. S. et al. (2023). Generative Agent-Based Modeling with Actions Grounded in Physical, Social, or Digital Space Using Concordia. arXiv:2312.03664. https://arxiv.org/abs/2312.03664",
        "Wu, Q. et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv:2308.08155. https://arxiv.org/abs/2308.08155",
        "ter Hoeven, E. et al. (2025). Mesa 3: Agent-Based Modeling with Python in 2025. Journal of Open Source Software, 10(107), 7668. https://doi.org/10.21105/joss.07668",
        "Johnson, J., Douze, M., and Jegou, H. (2017). Billion-Scale Similarity Search with GPUs. arXiv:1702.08734. https://arxiv.org/abs/1702.08734",
    ]


if __name__ == "__main__":
    build_pdf()
