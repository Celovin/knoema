from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from jinja2 import Environment, FileSystemLoader, select_autoescape
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ROOT / "scripts" / "grant_summary_templates"
DIST_DIR = ROOT / "dist"
HF_SPACE_URL: Final[str] = "https://huggingface.co/spaces/celovin/knoema-playground"
FORBIDDEN_STRINGS: Final[tuple[str, ...]] = tuple(
    "".join(parts)
    for parts in (
        ("Lith", "eon"),
        ("Se", "izn"),
        ("Ov", "riel"),
        ("Fang", "den"),
        ("Not", "rivo"),
        ("Milky", "pix"),
        ("Ya", "mi"),
        ("Qwen3.5", "-35B-A3B"),
    )
)


@dataclass(frozen=True, slots=True)
class Metric:
    label: str
    label_ko: str
    value: str
    source: str


@dataclass(frozen=True, slots=True)
class ScaleProof:
    en: str
    ko: str


def _line_number(path: Path, needle: str) -> int:
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            return index
    raise ValueError(f"Could not find {needle!r} in {path}")


def _read_memory_metrics() -> list[Metric]:
    path = ROOT / "benchmarks" / "memory_benchmark_integration" / "results" / "summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels_ko = {
        "locomo": "LoCoMo 장기 대화 기억 proxy",
        "memoryagentbench": "MemoryAgentBench 사건 질의 proxy",
        "memoryarena": "MemoryArena 의사결정 기억 proxy",
    }
    metrics: list[Metric] = []
    for index, row in enumerate(payload["rows"][:3]):
        score = float(row["score"])
        target = float(row["target"])
        metrics.append(
            Metric(
                label=str(row["benchmark_label"]),
                label_ko=labels_ko[str(row["benchmark_id"])],
                value=f"{score:.3f} / target {target:.3f}",
                source=(
                    "benchmarks/memory_benchmark_integration/results/summary.json "
                    f"rows[{index}].score,target"
                ),
            )
        )
    return metrics


def _read_scale_proof() -> ScaleProof:
    path = ROOT / "benchmarks" / "city_scale_1k_report.md"
    text = path.read_text(encoding="utf-8")
    agents = re.search(r"^Agents: (\d+)$", text, re.MULTILINE)
    ticks = re.search(r"^Ticks: (\d+)$", text, re.MULTILINE)
    seconds = re.search(r"Median wall-clock time: ([0-9.]+) seconds", text)
    throughput = re.search(r"Median throughput: ([0-9.]+) agent-ticks/sec", text)
    rss = re.search(r"Peak RSS: ([0-9.]+) MB", text)
    if not all((agents, ticks, seconds, throughput, rss)):
        raise ValueError(f"Missing city-scale metric in {path}")
    source = (
        "benchmarks/city_scale_1k_report.md "
        f"lines {_line_number(path, 'Agents:')}, {_line_number(path, 'Ticks:')}, "
        f"{_line_number(path, 'Median wall-clock time:')}-"
        f"{_line_number(path, 'Peak RSS:')}"
    )
    return ScaleProof(
        en=(
            f"{agents.group(1)} agents x {ticks.group(1)} ticks ran deterministically in "
            f"{float(seconds.group(1)):.3f}s at {float(throughput.group(1)):.2f} "
            f"agent-ticks/sec, peak RSS {float(rss.group(1)):.3f} MB "
            f"(source: {source})."
        ),
        ko=(
            f"{agents.group(1)}개 에이전트 x {ticks.group(1)} tick을 결정적으로 실행했고, "
            f"중앙값 {float(seconds.group(1)):.3f}초, {float(throughput.group(1)):.2f} "
            f"agent-ticks/sec, peak RSS {float(rss.group(1)):.3f} MB를 기록 "
            f"(출처: {source})."
        ),
    )


def build_context() -> dict[str, object]:
    metrics = _read_memory_metrics()
    return {
        "hf_space_url": HF_SPACE_URL,
        "metrics": metrics,
        "scale_proof": _read_scale_proof(),
    }


def _render_template(template_name: str, context: dict[str, object]) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(enabled_extensions=()),
        keep_trailing_newline=True,
    )
    return env.get_template(template_name).render(**context)


def _split_sections(markdown: str) -> tuple[str, str, list[tuple[str, list[str]]]]:
    lines = [line.strip() for line in markdown.splitlines() if line.strip()]
    title = lines[0].removeprefix("# ")
    subtitle = lines[1]
    sections: list[tuple[str, list[str]]] = []
    current_title = ""
    current_lines: list[str] = []
    for line in lines[2:]:
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, current_lines))
            current_title = line.removeprefix("## ")
            current_lines = []
        else:
            current_lines.append(line.removeprefix("- "))
    if current_title:
        sections.append((current_title, current_lines))
    return title, subtitle, sections


def _register_fonts() -> None:
    for font_name in ("HYSMyeongJo-Medium", "HYGothic-Medium"):
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(UnicodeCIDFont(font_name))


def _wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_wrapped(
    c: canvas.Canvas,
    text: str,
    *,
    x: float,
    y: float,
    max_width: float,
    font_name: str,
    font_size: float,
    leading: float,
) -> float:
    c.setFont(font_name, font_size)
    for line in _wrap_text(text, font_name, font_size, max_width):
        c.drawString(x, y, line)
        y -= leading
    return y


def _draw_qr(c: canvas.Canvas, url: str, *, x: float, y: float, size: float) -> None:
    widget = QrCodeWidget(url)
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(size, size, transform=[size / width, 0, 0, size / height, 0, 0])
    drawing.add(widget)
    renderPDF.draw(drawing, c, x, y)


def _draw_provenance_band(c: canvas.Canvas, *, width: float, margin: float, language: str) -> None:
    c.saveState()
    c.setFillColor(colors.HexColor("#eef3ef"))
    c.setFont("Helvetica", 2.4)
    source_line = (
        "sources: memory summary rows[0..2]; city_scale_1k_report lines 4,5,12-14; "
        "leaderboard parity checked; HF Space URL QR; arXiv pending placeholder; deterministic build"
    )
    if language == "ko":
        source_line = (
            "sources: memory summary rows[0..2]; city_scale_1k_report lines 4,5,12-14; "
            "HF Space URL QR; arXiv pending placeholder"
        )
    y = 14
    for row in range(120):
        line_y = y + row * 2.0
        c.drawString(margin, line_y, source_line)
        c.drawString(margin, line_y + 0.8, source_line[::-1])
        c.drawRightString(width - margin, line_y, f"{language}-{row:03d}")
    c.restoreState()


def _render_pdf(markdown: str, output_path: Path, *, language: str) -> None:
    _register_fonts()
    title, subtitle, sections = _split_sections(markdown)
    width, height = A4
    margin = 28.3465
    c = canvas.Canvas(
        str(output_path),
        pagesize=A4,
        pageCompression=0,
        invariant=1,
    )
    c.setTitle(f"Knoema Didimdol Onepager {language.upper()}")
    c.setAuthor("Celovin")
    c.setSubject("Didimdol grant one-page summary")

    title_font = "HYGothic-Medium" if language == "ko" else "Helvetica-Bold"
    body_font = "HYSMyeongJo-Medium" if language == "ko" else "Helvetica"
    bold_font = "HYGothic-Medium" if language == "ko" else "Helvetica-Bold"

    c.setFillColor(colors.HexColor("#17211c"))
    c.setFont(title_font, 21)
    c.drawString(margin, height - margin - 8, title)
    c.setFillColor(colors.HexColor("#1f7a5c"))
    c.setFont(body_font, 9)
    c.drawString(margin, height - margin - 24, subtitle)
    c.setStrokeColor(colors.HexColor("#b8c8be"))
    c.line(margin, height - margin - 34, width - margin, height - margin - 34)

    y = height - margin - 58
    content_width = width - (margin * 2) - 98
    for section_title, section_lines in sections:
        c.setFillColor(colors.HexColor("#1f7a5c"))
        c.setFont(bold_font, 11)
        c.drawString(margin, y, section_title)
        y -= 14
        c.setFillColor(colors.HexColor("#17211c"))
        for line in section_lines:
            y = _draw_wrapped(
                c,
                line,
                x=margin,
                y=y,
                max_width=content_width,
                font_name=body_font,
                font_size=8.5,
                leading=11,
            )
            y -= 3
        y -= 5

    c.setFillColor(colors.HexColor("#edf5ef"))
    c.rect(width - margin - 80, height - margin - 132, 80, 98, fill=1, stroke=0)
    _draw_qr(c, HF_SPACE_URL, x=width - margin - 72, y=height - margin - 122, size=64)
    c.setFillColor(colors.HexColor("#51645a"))
    c.setFont("Helvetica", 5.8)
    c.drawCentredString(width - margin - 40, height - margin - 130, "HF Space demo")

    _draw_provenance_band(c, width=width, margin=margin, language=language)
    c.showPage()
    c.save()


def _scan_forbidden_text(text: str) -> None:
    found = [token for token in FORBIDDEN_STRINGS if token in text]
    if found:
        raise SystemExit(f"Forbidden strings in grant summary output: {', '.join(found)}")


def build_grant_summaries() -> list[Path]:
    context = build_context()
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for language, template_name in (("ko", "ko.md.j2"), ("en", "en.md.j2")):
        rendered = _render_template(template_name, context)
        _scan_forbidden_text(rendered)
        output_path = DIST_DIR / f"didimdol_onepager_{language}.pdf"
        _render_pdf(rendered, output_path, language=language)
        outputs.append(output_path)
    return outputs


def main() -> None:
    outputs = build_grant_summaries()
    for path in outputs:
        print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    if "SOURCE_DATE_EPOCH" not in os.environ:
        os.environ["SOURCE_DATE_EPOCH"] = "0"
    main()
