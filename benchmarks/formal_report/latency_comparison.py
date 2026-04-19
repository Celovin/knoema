"""Tick latency comparison helpers for the formal benchmark bundle."""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

LATENCY_COMPARISON_PATH = Path(__file__).resolve().parent / "results" / "latency_comparison.json"

MeasuredMode = Literal["Replay only", "OpenAI"]


@dataclass(frozen=True, slots=True)
class LatencyReferenceSource:
    label: str
    url: str

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class LatencyRun:
    elapsed_ms: float
    tick_count: int
    per_tick_latency_ms: float
    log_count: int

    def to_json_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MeasuredLatencyRow:
    path_id: str
    label: str
    mode: MeasuredMode
    model: str
    repetitions: int
    mean_tick_latency_ms: float
    p95_tick_latency_ms: float
    runs: tuple[LatencyRun, ...]
    notes: str

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["runs"] = [run.to_json_dict() for run in self.runs]
        return payload


@dataclass(frozen=True, slots=True)
class PublishedLatencyRow:
    reference_id: str
    label: str
    latency_ms_low: float
    latency_ms_high: float
    notes: str
    sources: tuple[LatencyReferenceSource, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["sources"] = [source.to_json_dict() for source in self.sources]
        return payload


@dataclass(frozen=True, slots=True)
class LatencyComparisonReport:
    measured_at_utc: str
    scenario_name: str
    ticks: int
    measured_rows: tuple[MeasuredLatencyRow, ...]
    published_rows: tuple[PublishedLatencyRow, ...]

    def to_json_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["measured_rows"] = [row.to_json_dict() for row in self.measured_rows]
        payload["published_rows"] = [row.to_json_dict() for row in self.published_rows]
        return payload


def build_latency_comparison_report(
    *,
    openai_api_key: str,
    model: str = "gpt-4o-mini",
    scenario_name: str = "Dorm: two agents",
    ticks: int = 2,
    repetitions: int = 2,
) -> LatencyComparisonReport:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")
    replay_row = _measure_playground_mode(
        provider="Replay only",
        api_key="",
        model=model,
        scenario_name=scenario_name,
        ticks=ticks,
        repetitions=repetitions,
    )
    openai_row = _measure_playground_mode(
        provider="OpenAI",
        api_key=openai_api_key,
        model=model,
        scenario_name=scenario_name,
        ticks=ticks,
        repetitions=repetitions,
    )
    return LatencyComparisonReport(
        measured_at_utc=datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
        scenario_name=scenario_name,
        ticks=ticks,
        measured_rows=(replay_row, openai_row),
        published_rows=_published_latency_rows(),
    )


def write_latency_comparison_report(
    output_path: Path = LATENCY_COMPARISON_PATH,
    *,
    openai_api_key: str | None = None,
    model: str = "gpt-4o-mini",
    scenario_name: str = "Dorm: two agents",
    ticks: int = 2,
    repetitions: int = 2,
) -> LatencyComparisonReport:
    key = (openai_api_key or os.environ.get("OPENAI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is required to measure the live OpenAI provider path")
    report = build_latency_comparison_report(
        openai_api_key=key,
        model=model,
        scenario_name=scenario_name,
        ticks=ticks,
        repetitions=repetitions,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_json_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def load_latency_comparison_report(path: Path = LATENCY_COMPARISON_PATH) -> LatencyComparisonReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    measured_rows = tuple(
        MeasuredLatencyRow(
            path_id=str(row["path_id"]),
            label=str(row["label"]),
            mode=str(row["mode"]),
            model=str(row["model"]),
            repetitions=int(row["repetitions"]),
            mean_tick_latency_ms=float(row["mean_tick_latency_ms"]),
            p95_tick_latency_ms=float(row["p95_tick_latency_ms"]),
            runs=tuple(
                LatencyRun(
                    elapsed_ms=float(run["elapsed_ms"]),
                    tick_count=int(run["tick_count"]),
                    per_tick_latency_ms=float(run["per_tick_latency_ms"]),
                    log_count=int(run["log_count"]),
                )
                for run in row["runs"]
            ),
            notes=str(row["notes"]),
        )
        for row in payload["measured_rows"]
    )
    published_rows = tuple(
        PublishedLatencyRow(
            reference_id=str(row["reference_id"]),
            label=str(row["label"]),
            latency_ms_low=float(row["latency_ms_low"]),
            latency_ms_high=float(row["latency_ms_high"]),
            notes=str(row["notes"]),
            sources=tuple(
                LatencyReferenceSource(
                    label=str(source["label"]),
                    url=str(source["url"]),
                )
                for source in row["sources"]
            ),
        )
        for row in payload["published_rows"]
    )
    return LatencyComparisonReport(
        measured_at_utc=str(payload["measured_at_utc"]),
        scenario_name=str(payload["scenario_name"]),
        ticks=int(payload["ticks"]),
        measured_rows=measured_rows,
        published_rows=published_rows,
    )


def _measure_playground_mode(
    *,
    provider: MeasuredMode,
    api_key: str,
    model: str,
    scenario_name: str,
    ticks: int,
    repetitions: int,
) -> MeasuredLatencyRow:
    from playground.simulation import run_playground_scenario

    runs: list[LatencyRun] = []
    for _ in range(repetitions):
        started = time.perf_counter()
        result = run_playground_scenario(
            scenario_name=scenario_name,
            provider=provider,
            api_key=api_key,
            model=model,
            primary_name="Latency Probe",
            primary_age=24,
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
            ticks=ticks,
            language="en",
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        runs.append(
            LatencyRun(
                elapsed_ms=round(elapsed_ms, 3),
                tick_count=result.tick_count,
                per_tick_latency_ms=round(elapsed_ms / max(1, result.tick_count), 3),
                log_count=result.log_count,
            )
        )
    per_tick = [run.per_tick_latency_ms for run in runs]
    return MeasuredLatencyRow(
        path_id="playground_replay" if provider == "Replay only" else "playground_openai",
        label=(
            "Knoema Playground replay-only"
            if provider == "Replay only"
            else "Knoema Playground OpenAI mode"
        ),
        mode=provider,
        model=model,
        repetitions=repetitions,
        mean_tick_latency_ms=round(mean(per_tick), 3),
        p95_tick_latency_ms=round(_p95(per_tick), 3),
        runs=tuple(runs),
        notes=(
            "Local scripted responder, no network I/O."
            if provider == "Replay only"
            else (
                "Measured with a live OpenAI Responses API call path; includes network, model, "
                "monologue generation, and playground orchestration."
            )
        ),
    )


def _published_latency_rows() -> tuple[PublishedLatencyRow, ...]:
    return (
        PublishedLatencyRow(
            reference_id="nvidia_ace_target",
            label="NVIDIA ACE target envelope",
            latency_ms_low=198.0,
            latency_ms_high=200.0,
            notes=(
                "NVIDIA technical blogs describe ACE or NVIGI as real-time, low-latency inference. "
                "ACE release notes list 198 ms algorithmic latency for Speech Live Portrait, which "
                "the repo rounds to a 200 ms target envelope."
            ),
            sources=(
                LatencyReferenceSource(
                    label="NVIDIA Technical Blog (2025-02-20)",
                    url="https://developer.nvidia.com/blog/bring-nvidia-ace-ai-characters-to-games-with-the-new-in-game-inference-sdk",
                ),
                LatencyReferenceSource(
                    label="NVIDIA Technical Blog (2024-06-04)",
                    url="https://developer.nvidia.com/blog/build-lifelike-digital-humans-with-nvidia-ace-now-generally-available/",
                ),
                LatencyReferenceSource(
                    label="ACE Release Notes 24.06",
                    url="https://docs.nvidia.com/ace/overview/2025.03.06/ace-release-notes.html",
                ),
            ),
        ),
        PublishedLatencyRow(
            reference_id="inworld_tts_1",
            label="Inworld TTS-1 first audio chunk",
            latency_ms_low=200.0,
            latency_ms_high=200.0,
            notes=(
                "The August 15, 2025 Inworld blog reports the first two-second audio chunk in as few "
                "as 200 ms, excluding networking."
            ),
            sources=(
                LatencyReferenceSource(
                    label="Inworld blog (2025-08-15)",
                    url="https://inworld.ai/blog/introducing-inworld-tts",
                ),
            ),
        ),
        PublishedLatencyRow(
            reference_id="inworld_tts_1_5",
            label="Inworld TTS-1.5 first audio chunk",
            latency_ms_low=130.0,
            latency_ms_high=250.0,
            notes=(
                "The January 21, 2026 Inworld blog reports P90 time-to-first-audio under 250 ms "
                "for Max and under 130 ms for Mini."
            ),
            sources=(
                LatencyReferenceSource(
                    label="Inworld blog (2026-01-21)",
                    url="https://inworld.ai/blog/introducing-inworld-tts-1-5",
                ),
            ),
        ),
        PublishedLatencyRow(
            reference_id="inworld_runtime_guidance",
            label="Inworld end-to-end conversational guidance",
            latency_ms_low=1000.0,
            latency_ms_high=3000.0,
            notes=(
                "Official Runtime guidance published by Inworld staff in November 2025 says a full "
                "audio-input to audio-output turn is typically about 1-3 seconds."
            ),
            sources=(
                LatencyReferenceSource(
                    label="Inworld Runtime guidance (2025-11-19)",
                    url="https://community.inworld.ai/t/what-latency-do-you-have-when-running-through-a-full-conversational-pipeline-not-just-tts/67",
                ),
            ),
        ),
    )


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = 0.95 * (len(ordered) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    fraction = rank - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)


__all__ = [
    "LATENCY_COMPARISON_PATH",
    "LatencyComparisonReport",
    "LatencyReferenceSource",
    "MeasuredLatencyRow",
    "PublishedLatencyRow",
    "load_latency_comparison_report",
    "write_latency_comparison_report",
]
