"""Build a meeting-ready PDF preview of the Knoema arXiv v2 report."""

from __future__ import annotations

import re
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
        title="Knoema Engine arXiv v2 Technical Report",
        author="Celovin",
    )
    story = [
        Paragraph("Knoema Engine", styles["Title"]),
        Paragraph(
            "An Open Runtime for Persistent NPCs, Synthetic Replay Research, and Reproducible Agent Simulation",
            styles["Subtitle"],
        ),
        Paragraph("Celovin | hello@celovin.com | arXiv v2 draft | April 2026", styles["Meta"]),
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
            fontSize=9.2,
            leading=12.5,
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
                "Knoema Engine is an open, MIT-licensed runtime for persistent social agents whose state is inspectable outside of a model prompt. The system combines persona definitions, short-term and long-term memory, directed relationship state, environment context, PAD-style emotion, event scheduling, deterministic logs, REST and WebSocket interfaces, game adapters, and optional LLM-backed decisions.",
                "This arXiv v2 revision extends that runtime with persona opt-in theory-of-mind tracking, classic ABM reproductions, a 500-agent metropolis run, PCS/RCS scoring, a scenario-library catalog, and a Papers with Code submission packet.",
                "The report keeps the central claim modest: persistent-agent applications need explicit runtime state, replayable artifacts, adapter contracts, and safety-bounded scenario definitions before they need larger prompts.",
            ],
        ),
        (
            "1. Introduction",
            [
                "LLM-based agents can generate plausible language, but prompt-only designs often hide the state that a simulation, game, or research workflow needs to inspect. Persistent NPCs need memory and relationship state that a game can test. Research simulations need fixed configuration, deterministic replay, and exportable logs. Synthetic replay workflows need explicit safety boundaries around data use and claims.",
                "Knoema addresses this engineering layer. It is not a general task-automation framework and it is not a hosted model service. It is a small runtime for building agents whose state is represented by ordinary package objects: persona, memory, relationships, environment, emotion, events, decisions, and logs.",
                [
                    ["Track", "Primary surface", "arXiv v2 status"],
                    ["Games", "Python, TypeScript, GDScript, Unity, Godot, and Unreal surfaces", "Implemented"],
                    ["Synthetic replay", "Scenario DSL, safety validator, and 50-scenario library", "Implemented"],
                    ["Academic simulation", "Reproducible configs, logs, reports, docs, and PWC packet", "Implemented"],
                ],
            ],
        ),
        (
            "2. Related Work",
            [
                "Generative Agents showed that natural-language memory, planning, and reflection can produce believable behavior in interactive environments. Concordia frames generative agent-based modeling as grounded interaction among entities. The Sally-Anne task remains a compact probe for explicit false-belief reasoning. AutoGen, CAMEL, MetaGPT, ChatDev, Voyager, Reflexion, ReAct, and Toolformer explore ways to coordinate LLM behavior through roles, tools, self-reflection, or conversational protocols.",
                "Classical agent-based modeling systems such as Mesa, NetLogo, MASON, Repast, Swarm, GAMA, and AnyLogic represent a long tradition of explicit model state, scheduling, and reproducible simulation loops. Knoema borrows this inspectable-loop discipline while adding natural-language memory and model-backed decision generation.",
                "Retrieval-augmented generation, dense passage retrieval, approximate nearest-neighbor indexes, and vector stores provide the substrate for long-term agent context. Knoema currently uses deterministic hash embeddings in tests and examples to keep local runs reproducible.",
            ],
        ),
        (
            "3. Architecture",
            [
                "Knoema separates persistent state, decision generation, and adapters. State modules build an agent-specific context, the decision layer produces an action, and the simulator commits that action to logs, memories, relationship state, and downstream artifacts.",
                [
                    ["Module", "Responsibility", "MVP status"],
                    ["Persona", "Identity, values, goals, prompt rendering", "Implemented"],
                    ["Memory", "Short-term FIFO plus SQLite and FAISS retrieval", "Implemented"],
                    ["Relationship", "Directed trust, familiarity, and interaction weight", "Implemented"],
                    ["Environment", "Time, location, conditions, and recent events", "Implemented"],
                    ["Emotion", "PAD state for valence, arousal, and dominance", "Implemented"],
                    ["Theory of mind", "Persona opt-in symbolic belief tracking", "Implemented"],
                    ["Decision", "Message rendering and strict action parsing", "Implemented"],
                    ["Adapters", "Dashboard, Godot, Unity, and SDK surfaces", "Implemented"],
                ],
                "At every tick the simulator gathers persona, memory, relationship, environment, emotion, and optional theory-of-mind context for an agent. The decision engine renders messages, calls an LLMClient, and parses a strict action structure when possible. Deterministic local clients are used throughout tests and public demos.",
                "The Scenario DSL expresses agents, environment, events, duration, metrics, and ethics flags in YAML. The parser returns typed scenario objects, the validator rejects unsafe or unsupported public-safety claims, and the serializer supports round trips for reproducibility.",
            ],
        ),
        (
            "4. Experiments and Evidence",
            [
                "Knoema's arXiv v2 evidence is engineering-oriented. The experiments answer whether the runtime can generate reproducible artifacts, whether the memory policy improves deterministic proxy metrics over a naive full-context baseline, whether theory-of-mind behavior can be tested in an opt-in module, and whether larger deterministic runs can be committed and replayed as public artifacts.",
                "The 50-agent village experiment runs a deterministic week with 50 synthetic agents, 42 ticks, and 2,100 committed actions. Each agent contributes 42 actions. The run records 100 relationship edges, a deterministic seed of 20260418, a bit-for-bit artifact check, and zero provider cost because it uses local deterministic decisions.",
                [
                    ["50-agent metric", "Value", "Artifact"],
                    ["Agents", "50", "config.yaml"],
                    ["Ticks", "42", "metrics.json"],
                    ["Actions", "2,100", "sim_log.jsonl"],
                    ["Latency", "p50 46.95 ms, p95 53.80 ms, p99 56.20 ms", "metrics.json"],
                    ["Relationship edges", "100", "metrics.json"],
                    ["Provider cost", "0.0 USD", "deterministic-local"],
                ],
                "The formal benchmark bundle runs four scenarios across two approaches and three local model profiles, producing 24 deterministic runs. The comparison baseline is a naive full-context prompt policy.",
                [
                    ["Scenario", "Knoema recall", "Naive recall"],
                    ["A memory recall", "0.789", "0.500"],
                    ["B relationship dynamics", "0.786", "0.495"],
                    ["C narrative branching", "0.784", "0.492"],
                    ["D scalability", "0.780", "0.487"],
                ],
                "Across the deterministic matrix, the Knoema memory policy improves top-k memory recall proxies and token efficiency proxies in every scenario. The paired sign-test over the composite score reports p=0.000244. This is deterministic evidence over the benchmark proxy, not a real-world behavioral claim.",
                "Phase 43 adds a persona opt-in theory-of-mind module and a deterministic Sally-Anne harness. The harness covers 20 structured cases and reproduces the expected search location in 20 out of 20 cases for an accuracy of 1.000 against a target gate of 0.800.",
                [
                    ["Theory-of-mind metric", "Knoema", "Reference status"],
                    ["Opt-in surface", "Persona opt-in symbolic belief tracker", "Concordia and Stanford are reference only"],
                    ["Sally-Anne reproduction", "20/20 (1.000)", "No public external score asserted"],
                ],
                "Phase 45 adds two compact reproductions drawn from classical agent-based modeling literature. The Schelling run preserves the expected medium-versus-high segregation contrast, and the Axelrod tournament keeps Tit-for-Tat inside the top cooperative cluster.",
                [
                    ["Classic reproduction", "Deterministic result", "Acceptance note"],
                    ["Schelling threshold 0.3", "0.548 segregation index", "Expected band satisfied"],
                    ["Schelling threshold 0.7", "0.942 segregation index", "Expected band satisfied"],
                    ["Axelrod top three", "Tit for Tat, Grudger, Generous Tit for Tat", "Tit for Tat remains in top three"],
                ],
                "Phase 46 adds two lightweight behavioral metrics that can be computed directly from committed JSONL logs. Persona Consistency Score uses a weighted mix of action recurrence, location stability, normalized content stability, and target focus. Relationship Coherence Score uses reciprocal coverage, pairwise location alignment, action alignment, and interaction density.",
                [
                    ["Evaluation metric", "Result", "Acceptance note"],
                    ["Village PCS average", "0.948", "Passes >= 0.75 gate"],
                    ["Village PCS range", "0.948 to 0.948", "Stable across 50 agents"],
                    ["Metropolis RCS average", "0.760", "Passes >= 0.70 gate"],
                    ["Metropolis RCS range", "0.760 to 0.760", "Stable across 2,500 pairs"],
                ],
            ],
        ),
        (
            "5. Applications",
            [
                "The game path treats the LLM as an optional dialogue provider behind a deterministic NPC contract. The current SDK response contains text, emotion, branch flags, and raw debugging state. This contract is intentionally small so a game can test behavior before connecting provider-backed dialogue.",
                "The replay path uses fictional, non-identifying scenarios to inspect event traces. A scenario can define a known event sequence, run synthetic agents, and compare generated actions against process milestones. This is a replay and education workflow, not a prediction workflow.",
                "The academic path emphasizes reproducible artifacts. Configurations, seeds, logs, metrics, dashboards, and reports remain close to the code. The MkDocs site and LaTeX report make the public API and evidence bundle easier to audit.",
                [
                    ["Application", "Public artifact", "Primary risk control"],
                    ["Game NPCs", "SDK facades and adapters", "Deterministic contract before live model calls"],
                    ["Synthetic replay", "Scenario DSL and dashboard", "No real personal data or prediction claims"],
                    ["Academic workflows", "Reports and reproducibility tests", "Config, seed, log, and hash checks"],
                ],
            ],
        ),
        (
            "6. Discussion",
            [
                "The current evidence supports an engineering claim: explicit state, deterministic logs, and adapter contracts make persistent-agent systems easier to inspect and test. The repository demonstrates this through a 250+ test gate, benchmark artifacts, API routes, dashboards, SDK facades, game-engine adapters, a scenario editor, and generated documentation.",
                "The current evidence does not establish real-world behavioral validity, general human simulation accuracy, production game quality, or safe deployment in operational public-safety environments. The public-safety track is limited to synthetic replay and prevention-oriented analysis.",
                "Threats to validity include deterministic local clients, lightweight hash embeddings, a simple naive baseline, and the absence of human evaluation. Larger-scale experiments need memory-store stress tests, model comparisons, and independent review.",
                "Knoema uses repository-level checks to prevent private planning documents and unrelated entity references from entering public files. Runtime artifacts such as logs, SQLite databases, FAISS indexes, checkpoints, and documentation build output are ignored by git.",
            ],
        ),
        (
            "7. Safety Boundary",
            [
                "Public-safety examples are fictional, synthetic, and non-identifying. The system is not designed for prediction, suspect scoring, surveillance, or enforcement automation. Sensitive scenarios must include purpose notes, non-use boundaries, and reproducible artifacts.",
                [
                    ["Allowed", "Rejected", "Required"],
                    ["Fictional replay", "Real personal data", "Synthetic data notes"],
                    ["Education demos", "Prediction or suspect ranking", "Explicit non-use boundary"],
                    ["Reproducibility checks", "Surveillance workflows", "Config and log artifacts"],
                ],
            ],
        ),
        (
            "8. Conclusion",
            [
                "Knoema Engine demonstrates a compact open runtime for persistent social agents. The arXiv v2 version expands the original technical report with scenario DSL artifacts, SDK surfaces, API surfaces, a formal benchmark bundle, a 50-agent village experiment, a 500-agent metropolis run, classic reproductions, theory-of-mind tests, documentation infrastructure, and a stricter safety boundary.",
                "The next research step is to replace deterministic proxy evaluation with controlled provider-backed runs, stronger semantic retrieval, human review of plausibility and safety, and fairer external baseline reproduction.",
            ],
        ),
        (
            "Appendix A. Artifact Map",
            [
                "The public repository is organized so each claim in the report points to a runnable artifact. Core runtime code lives in src/knoema. Scenario definitions and DSL docs live in examples/scenarios, schemas, and docs/dsl. Game integrations live in adapters and sdk. Benchmarks and committed results live in experiments and benchmarks. Documentation surfaces live in docs, website, and mkdocs.yml.",
                [
                    ["Artifact", "Path", "Purpose"],
                    ["Core runtime", "src/knoema", "State, decisions, events, memory, and simulation"],
                    ["Scenario DSL", "src/knoema/dsl and schemas", "Validated YAML scenario definitions"],
                    ["50-agent run", "experiments/50_agent_village", "Scale and reproducibility artifact"],
                    ["Formal benchmark", "benchmarks/formal_report", "Deterministic memory-policy comparison"],
                    ["Game SDKs", "sdk and adapters", "NPC response contracts and engine scaffolds"],
                    ["Docs site", "mkdocs.yml and docs", "API and workflow documentation"],
                ],
                "The LaTeX source includes figure and table fragments under paper/figures and paper/tables. The generated PDF preview is committed as paper/knoema_technical_report.pdf for reviewers who do not have a local TeX installation.",
            ],
        ),
        (
            "Appendix B. Reproducibility Checklist",
            [
                "Knoema treats reproducibility as an implementation requirement. Fixed seeds are part of scenario and experiment configuration. JSONL logs are committed for formal experiments when appropriate. Dashboard inspection consumes exported logs rather than simulator internals. Public-safety examples are fictional, synthetic, and non-identifying.",
                [
                    ["Check", "Current status", "Verification path"],
                    ["Same-seed determinism", "Implemented", "tests/reproducibility/test_deterministic_runs.py"],
                    ["Seed propagation", "Implemented", "tests/reproducibility/test_seed_propagation.py"],
                    ["Config serialization", "Implemented", "tests/reproducibility/test_config_serialization.py"],
                    ["JSONL replay", "Implemented", "tests/reproducibility/test_logs_replay.py"],
                    ["Scenario guardrails", "Implemented", "tests/test_phase22_dsl.py"],
                    ["Entity separation scans", "Manual release gate", "rg public-surface scans"],
                ],
                "Provider keys are not committed or persisted in public demos. The public Playground supports replay-only mode without a key and accepts optional user-supplied keys only for the current session.",
            ],
        ),
        *phase50_annex_sections(),
    ]


def phase50_annex_sections() -> list[tuple[str, list[str | list[list[str]]]]]:
    return [
        (
            "9. 500-Agent Metropolis Evidence",
            [
                "The Phase 42 metropolis run is the largest deterministic artifact included in the arXiv v2 packet. It uses 500 synthetic agents, 20 fixed seeds, six 30-minute ticks per seed, and 60,000 total committed actions.",
                [
                    ["Metric", "Value", "Source"],
                    ["Mean throughput", "1,657.527 actions/sec", "summary.json"],
                    ["Mean p95 latency", "65.055 ms", "summary.json"],
                    ["Mean peak memory", "431.725 MB", "summary.json"],
                    ["Relationship edges", "5,000 mean", "summary.json"],
                    ["Reproducibility", "Bit-for-bit artifacts true", "summary.json"],
                ],
                "The scale evidence is not presented as an external benchmark victory. It is presented as a local envelope check with committed configuration, seed manifest, JSONL output, summary JSON, representative log, and SVG plot.",
            ],
        ),
        (
            "10. Theory-of-Mind Evidence",
            [
                "The theory-of-mind module is opt-in at the persona level. Disabled personas preserve the prior behavior and do not receive belief-state prompt sections.",
                "The Sally-Anne harness alternates false-belief and witnessed-move cases. Knoema returns the expected search location in 20 out of 20 deterministic cases, clearing the 0.800 acceptance gate.",
                [
                    ["Comparison point", "Knoema", "External reference"],
                    ["Opt-in ToM API", "Yes", "No public equivalent asserted for Stanford or Concordia"],
                    ["Sally-Anne score", "1.000", "No external score asserted"],
                    ["Claim boundary", "Symbolic false-belief check", "Not human-level cognition"],
                ],
            ],
        ),
        (
            "11. Classic ABM Reproductions",
            [
                "The Schelling reproduction checks whether deterministic agents preserve the expected threshold contrast. Threshold 0.3 lands at a segregation index of 0.548, while threshold 0.7 lands at 0.942.",
                "The Axelrod reproduction runs 10 strategy profiles over 200 rounds per pairing. Tit-for-Tat ranks first in deterministic, Ollama-labeled, and API-labeled summaries, with deterministic top three entries of Tit for Tat, Grudger, and Generous Tit for Tat.",
                [
                    ["Experiment", "Result", "Interpretation"],
                    ["Schelling 0.3", "0.548", "Expected medium segregation band"],
                    ["Schelling 0.7", "0.942", "Expected high segregation band"],
                    ["Axelrod", "Tit-for-Tat rank 1", "Classic cooperative pattern preserved"],
                ],
            ],
        ),
        (
            "12. Persona and Relationship Metrics",
            [
                "Persona Consistency Score summarizes action recurrence, location stability, normalized content stability, and target focus for a single agent. Relationship Coherence Score summarizes reciprocal interaction coverage, pairwise location alignment, action alignment, and interaction density for an agent pair.",
                [
                    ["Metric", "Artifact", "Value"],
                    ["PCS average", "50-agent village log", "0.948"],
                    ["PCS range", "50-agent village log", "0.948 to 0.948"],
                    ["RCS average", "500-agent representative log", "0.760"],
                    ["RCS range", "500-agent representative log", "0.760 to 0.760"],
                ],
                "These metrics are quality proxies for committed logs. They do not replace human evaluation and should not be used as evidence of real-world behavioral validity.",
            ],
        ),
        (
            "13. Scenario Library Catalog",
            [
                "The Phase 48 library contains 50 fictional scenarios across school, workplace, family, community, and social-experiment categories. Each scenario has a YAML DSL file and a one-page Markdown description.",
                [
                    ["Category", "Count", "Primary use"],
                    ["School", "10", "Education and mentoring scenes"],
                    ["Workplace", "10", "Coordination and conflict scenes"],
                    ["Family", "10", "Household relationship scenes"],
                    ["Community", "10", "Civic and mutual-aid scenes"],
                    ["Social experiment", "10", "Ethics-first fictional variants"],
                ],
                "The library is a marketplace seed corpus and a validation target. Sensitive examples must include non-use language and fictional participants.",
            ],
        ),
        (
            "14. Web Scenario Editor",
            [
                "The Phase 49 editor provides a browser surface for arranging agents, editing relationships, scheduling events, previewing YAML, and exporting a scenario definition. The editor is implemented under website/app/editor and verified with Playwright.",
                "The UI is not a marketing page. It is a functional scenario-authoring surface that supports drag-and-drop placement, stable property editing, live YAML preview, and an export path that is compatible with the Scenario DSL validator.",
                [
                    ["Gate", "Result", "Scope"],
                    ["Next build", "Pass", "Production static build"],
                    ["Playwright", "3 tests pass", "Editor flow"],
                    ["Lighthouse", "Performance 100, accessibility 100", "Desktop/provided throttle"],
                ],
            ],
        ),
        (
            "15. API and Deployment Surface",
            [
                "The FastAPI layer wraps the simulator behind REST and WebSocket routes. The API can create simulations, inspect agents, retrieve memory, inject events, and stream tick-by-tick JSON envelopes.",
                "Docker Compose packages the API server with the Streamlit dashboard and research dashboard so a reviewer can inspect the deployment shape locally without external provider credentials.",
                [
                    ["Surface", "Route or artifact", "Purpose"],
                    ["Create run", "POST /simulations", "Start an in-memory simulation"],
                    ["Inspect agents", "GET /simulations/{id}/agents", "View state"],
                    ["Stream ticks", "WebSocket /simulations/{id}/stream", "Live JSON events"],
                    ["Health", "GET /healthz", "Deployment smoke check"],
                ],
            ],
        ),
        (
            "16. Game Adapter Coverage",
            [
                "Knoema now covers the three major indie and professional engine paths at scaffold level: Godot, Unity, and Unreal Engine 5. The adapters consume action contracts and REST/log surfaces rather than private simulator internals.",
                [
                    ["Adapter", "Status", "Contract"],
                    ["Godot", "Scaffold and GDScript SDK", "Local fallback and HTTP client path"],
                    ["Unity", "UPM package scaffold", "Runtime HTTP/fallback client"],
                    ["Unreal", "UE5 plugin scaffold", "REST API client and tick component"],
                ],
                "The Unreal plugin intentionally keeps the Blueprint asset as a text placeholder because a full UE build environment is not assumed in the Python CI path.",
            ],
        ),
        (
            "17. Papers with Code Packet",
            [
                "The Papers with Code packet is split into a human-readable Markdown file and a JSON companion. Both files use ARXIV_ID_PENDING until the arXiv identifier is available.",
                [
                    ["Field", "Value", "File"],
                    ["Tasks", "Multi-agent RL, Agent-based modeling, Social simulation, Theory of mind", "Markdown and JSON"],
                    ["Datasets", "Metropolis logs, Sally-Anne benchmark, scenario library", "Markdown and JSON"],
                    ["Results", "Throughput, latency, ToM, Schelling, Axelrod, PCS, RCS", "Markdown and JSON"],
                ],
                "The packet avoids unmeasured external baseline rows. External rows can be added only after controlled re-runs with recorded commits, dependencies, prompts, and seeds.",
            ],
        ),
        (
            "18. Reproducibility Checklist",
            [
                "The repository follows a practical reproducibility checklist: code, configuration, seeds, logs, summaries, figures, citations, license, and test gates are all represented as versioned artifacts.",
                [
                    ["Checklist item", "Status", "Evidence"],
                    ["Code availability", "Ready", "GitHub repository"],
                    ["Fixed seeds", "Ready", "Experiment configs and seed files"],
                    ["Raw outputs", "Ready", "JSONL logs"],
                    ["Summary metrics", "Ready", "summary.json and metrics.json"],
                    ["Citation metadata", "Ready", "CITATION.cff and .zenodo.json"],
                    ["External submission", "Blocked", "arXiv and PWC account actions"],
                ],
            ],
        ),
        (
            "19. Safety Boundary",
            [
                "Criminal or sensitive scenarios are replay artifacts, not prediction instruments. They may encode fictional event sequences, safeguards, and process milestones, but they must not be used for suspect scoring, investigative prioritization, surveillance, enforcement automation, or profiling of identifiable people.",
                [
                    ["Allowed", "Rejected", "Reason"],
                    ["Fictional replay", "Real personal data", "No consent or validation basis"],
                    ["Education demo", "Prediction claim", "No external validity established"],
                    ["Prevention analysis", "Enforcement automation", "Unacceptable operational risk"],
                ],
                "This boundary is repeated in the paper, docs, scenario library, security policy, and Papers with Code packet.",
            ],
        ),
        (
            "20. External Baseline Discipline",
            [
                "Stanford Generative Agents, Concordia, Mesa, NetLogo, GAMA, AnyLogic, AutoGen, CrewAI, and LangGraph are comparison references, not measured baselines in this report.",
                "A fair baseline would require a recorded external commit, equivalent scenario translation, dependency lockfile, provider/model setting, prompt policy, seed set, and artifact storage. Until that exists, Knoema reports only local deterministic results.",
                [
                    ["External system", "Current treatment", "Future requirement"],
                    ["Stanford", "Architecture reference", "Controlled equivalent scenario"],
                    ["Concordia", "Architecture reference", "Controlled equivalent scenario"],
                    ["ABM platforms", "Design lineage", "Equivalent model translation"],
                ],
            ],
        ),
        (
            "21. Package and Quality Gate",
            [
                "The Phase 50 acceptance gate keeps the same repository discipline as prior phases: full pytest without coverage, ruff, mypy over src, PDF page-count verification, BibTeX shape checks, and Papers with Code JSON validation.",
                "The gate is designed to fail before a commit if a report artifact drifts from the code artifacts it cites.",
                [
                    ["Gate", "Command or test", "Purpose"],
                    ["Tests", "pytest --no-cov", "Behavioral regression guard"],
                    ["Lint", "ruff check .", "Style and static hygiene"],
                    ["Types", "mypy src", "Typed package surface"],
                    ["Paper packet", "tests/test_phase50_arxiv_packet.py", "Report and PWC checks"],
                ],
            ],
        ),
        (
            "22. Limitations",
            [
                "The strongest limitation is that deterministic local clients understate provider variability. Live model runs can change with provider version, latency, context handling, and refusal behavior.",
                "The current semantic path uses deterministic hash embeddings for local reproducibility. Production semantic encoders can improve retrieval but also introduce versioning and privacy questions.",
                "Human evaluation has not yet been performed. PCS, RCS, and Sally-Anne scores are engineering checks, not substitutes for external review.",
            ],
        ),
        (
            "23. arXiv Submission Notes",
            [
                "The paper source is ready for a TeX distribution, but this Windows environment uses ReportLab for the committed preview PDF because pdflatex and bibtex are not installed locally.",
                "After arXiv accepts the paper, the assigned identifier should be wired into paper metadata and the Papers with Code packet. The blockers file records these account-dependent actions.",
                [
                    ["Action", "Owner", "Repository state"],
                    ["arXiv account and endorsement", "Human", "Blocked externally"],
                    ["arXiv submission", "Human", "Packet ready"],
                    ["Papers with Code entry", "Human", "Wait for arXiv ID"],
                ],
            ],
        ),
        (
            "24. Conclusion for Reviewers",
            [
                "Knoema should be evaluated as an inspectable runtime, not as a claim that LLM agents accurately model real people. Its value is the integration of typed state, deterministic artifacts, scenario safety rules, adapters, and reproducible reports.",
                "The v2 packet gives reviewers a direct path from claims to files: code, configs, logs, summaries, figures, tables, paper source, PDF preview, citation metadata, and external-submission packet.",
            ],
        ),
    ]


def references() -> list[str]:
    text = (ROOT / "references.bib").read_text(encoding="utf-8")
    parsed: list[str] = []
    for match in re.finditer(r"@\w+\{([^,]+),(.*?)(?=\n@|\Z)", text, flags=re.DOTALL):
        key = match.group(1).strip()
        body = match.group(2)
        author = _bib_field(body, "author") or key
        title = _bib_field(body, "title") or "Untitled"
        year = _bib_field(body, "year") or "n.d."
        venue = (
            _bib_field(body, "journal")
            or _bib_field(body, "booktitle")
            or _bib_field(body, "publisher")
            or "Reference"
        )
        parsed.append(f"{author} ({year}). {title}. {venue}.")
    return parsed


def _bib_field(body: str, field: str) -> str | None:
    match = re.search(rf"\b{field}\s*=\s*\{{(.*?)\}}\s*,?", body, flags=re.DOTALL)
    if match is None:
        return None
    return _clean_bib_value(match.group(1))


def _clean_bib_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    value = value.replace("{", "").replace("}", "")
    value = value.replace("--", "-")
    value = re.sub(r"\\[`'\"~=^.][A-Za-z]?", "", value)
    value = value.replace("\\", "")
    return value.strip()


if __name__ == "__main__":
    build_pdf()
