from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


def test_phase50_paper_integrates_latest_evidence() -> None:
    body = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            Path("paper/abstract.tex"),
            Path("paper/sections/01_introduction.tex"),
            Path("paper/sections/02_related_work.tex"),
            Path("paper/sections/04_experiments.tex"),
            Path("paper/sections/06_discussion.tex"),
            Path("paper/appendix.tex"),
        ]
    )

    required_phrases = [
        "triple-use runtime surface",
        "500-agent deterministic metropolis",
        "60,000 total committed actions",
        "Sally-Anne false-belief",
        "Schelling and Axelrod",
        "Persona Consistency Score",
        "Relationship Coherence Score",
        "Papers with Code",
        "Scenario Library Catalog Summary",
        "not used for prediction",
    ]

    missing = [phrase for phrase in required_phrases if phrase not in body]

    assert missing == []
    assert body.count("Luvoire") >= 20
    assert "Stanford" in body
    assert "Concordia" in body
    assert "AutoGen" in body
    assert "CrewAI" in body
    assert "LangGraph" in body
    assert "Mesa" in body
    assert "NetLogo" in body
    assert "GAMA" in body


def test_phase50_references_bib_has_80_plus_valid_entries() -> None:
    references = Path("paper/references.bib").read_text(encoding="utf-8")
    entries = re.findall(r"^@(\w+)\{([^,]+),(.*?)(?=\n@|\Z)", references, flags=re.MULTILINE | re.DOTALL)
    keys = [key for _, key, _ in entries]

    assert len(entries) >= 80
    assert len(keys) == len(set(keys))
    assert {"schelling1971dynamic", "axelrod1984evolution", "baroncohen1985does"} <= set(keys)

    invalid_entries = []
    for entry_type, key, body in entries:
        if entry_type not in {"article", "book", "incollection", "inproceedings"}:
            invalid_entries.append(key)
            continue
        if not re.search(r"\btitle\s*=", body):
            invalid_entries.append(key)
        if not re.search(r"\byear\s*=", body):
            invalid_entries.append(key)
        if not re.search(r"\b(author|editor)\s*=", body):
            invalid_entries.append(key)

    assert invalid_entries == []


def test_phase50_papers_with_code_packet_schema() -> None:
    packet_path = Path("docs/research/papers_with_code_submission.md")
    schema_path = Path("docs/research/papers_with_code_submission.json")
    packet = packet_path.read_text(encoding="utf-8")
    data = json.loads(schema_path.read_text(encoding="utf-8"))

    assert data["schema_version"] == "luvoire.papers_with_code.packet.v1"
    assert data["paper"]["arxiv_id"] == "ARXIV_ID_PENDING"
    assert data["paper"]["repository"] == "https://github.com/Celovin/luvoire"
    assert {task["name"] for task in data["tasks"]} == {
        "Multi-agent RL",
        "Agent-based modeling",
        "Social simulation",
        "Theory of mind",
    }
    assert {dataset["name"] for dataset in data["datasets"]} >= {
        "500-agent metropolis logs",
        "Sally-Anne benchmark",
        "Scenario marketplace library",
        "Classic ABM reproductions",
    }
    assert len(data["results"]) >= 8
    assert all(result["model"].startswith("Luvoire") for result in data["results"])
    assert "ARXIV_ID_PENDING" in packet
    assert "mean throughput actions/s" in packet
    assert "safety boundary" in packet.lower()

    missing_sources = [
        result["source"] for result in data["results"] if not Path(result["source"]).exists()
    ]
    assert missing_sources == []


def test_phase50_pdf_preview_has_required_page_count() -> None:
    pdf = Path("paper/luvoire_technical_report.pdf")
    reader = PdfReader(pdf)

    assert len(reader.pages) >= 30
    assert len(reader.pages) <= 45
    assert reader.metadata is not None
    assert "Luvoire arXiv v2 Technical Report" in str(reader.metadata.title)


def test_phase50_docs_surface_packet() -> None:
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    academic_indexing = Path("docs/research/academic-indexing.md").read_text(encoding="utf-8")

    assert "Papers with Code Packet: research/papers_with_code_submission.md" in mkdocs
    assert "docs/research/papers_with_code_submission.md" in readme
    assert "docs/research/papers_with_code_submission.json" in readme
    assert "ARXIV_ID_PENDING" in academic_indexing
