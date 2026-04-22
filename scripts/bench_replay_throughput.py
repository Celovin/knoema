"""Benchmark committed offline replay artifacts."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import platform
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, cast

import msgpack  # type: ignore[import-untyped]
import psutil

ROOT = Path(__file__).resolve().parents[1]
REPLAY_DIR = ROOT / "demo" / "replay"
DEFAULT_JSON = ROOT / "docs" / "benchmarks" / "replay-perf.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "benchmarks" / "replay-perf.md"
REPLAY_LOOPS = 20
REGRESSION_TOLERANCE = 0.15
TIME_NOISE_FLOOR_SECONDS = 0.05
CHECK_REPEATS = 3
HARDWARE_CAVEAT = (
    "Single-thread sequential on Windows 10, i5-class CPU. Throughput on Linux / "
    "modern server-class hardware is typically 2-4x higher but not yet published."
)
ARTIFACTS = (
    {
        "label": "100",
        "filename": "replay_100agents_gangnam_7pm.msgpack",
        "expected_sha256": "8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab",
    },
    {
        "label": "1000",
        "filename": "replay_1000agents_gangnam_7pm.msgpack",
        "expected_sha256": "0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b",
    },
    {
        "label": "5000",
        "filename": "replay_5000agents_gangnam_7pm.msgpack",
        "expected_sha256": "d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01",
    },
    {
        "label": "10000",
        "filename": "replay_10000agents_gangnam_7pm.msgpack",
        "expected_sha256": "af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2",
    },
    {
        "label": "10000 nemotron",
        "filename": "replay_10000agents_nemotron_gangnam_7pm.msgpack",
        "expected_sha256": "9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9",
    },
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.check:
        _check(args.output_json)
        return 0

    report = build_report()
    _write_json(args.output_json, report)
    _write_markdown(args.output_md, report)
    print(f"Wrote {args.output_json}")
    print(f"Wrote {args.output_md}")
    return 0


def build_report() -> dict[str, object]:
    return {
        "artifacts": [_benchmark_artifact(artifact) for artifact in ARTIFACTS],
        "generated_at": datetime.now(UTC).isoformat(),
        "hardware": _hardware_snapshot(),
        "methodology": {
            "script": "scripts/bench_replay_throughput.py",
            "check_repeats": CHECK_REPEATS,
            "sequential_replay_loops": REPLAY_LOOPS,
            "regression_tolerance": REGRESSION_TOLERANCE,
            "time_noise_floor_seconds": TIME_NOISE_FLOOR_SECONDS,
            "timers": "time.perf_counter",
        },
    }


def _benchmark_artifact(artifact: Mapping[str, str]) -> dict[str, object]:
    path = REPLAY_DIR / artifact["filename"]
    digest = _sha256(path)
    if digest != artifact["expected_sha256"]:
        raise SystemExit(f"{path.name} SHA256 mismatch: {digest} != {artifact['expected_sha256']}")

    process = psutil.Process()
    gc.collect()
    rss_before = process.memory_info().rss
    started = perf_counter()
    payload = msgpack.unpackb(path.read_bytes(), raw=False)
    load_time = perf_counter() - started
    rss_after_load = process.memory_info().rss

    started = perf_counter()
    ticks_applied = _apply_replay(cast(Mapping[str, object], payload), loops=REPLAY_LOOPS)
    tick_wall = perf_counter() - started
    rss_after_replay = process.memory_info().rss

    metadata = _mapping(payload["metadata"])
    grid = _mapping(metadata["grid_bounds"])
    agent_count = int(metadata["agent_count"])
    rss_delta_mb = max(0.0, (max(rss_after_load, rss_after_replay) - rss_before) / (1024 * 1024))
    return {
        "agent_count": agent_count,
        "artifact_commit": _artifact_commit(path),
        "filename": path.name,
        "fps_20x": _rounded(ticks_applied / tick_wall if tick_wall > 0 else 0.0),
        "grid": f"{grid['width']}x{grid['height']}",
        "label": artifact["label"],
        "load_time_s": _rounded(load_time),
        "msgpack_sha256": digest,
        "msgpack_size_mb": _rounded(path.stat().st_size / (1024 * 1024)),
        "rss_delta_mb": _rounded(rss_delta_mb),
        "tick_count": int(metadata["tick_count"]),
        "tick_wall_s_per_20x": _rounded(tick_wall),
    }


def _apply_replay(payload: Mapping[str, object], *, loops: int) -> int:
    agents = _sequence(payload["agents"])
    frames = _sequence(payload["frames"])
    state: dict[str, dict[str, object]] = {}
    for agent in agents:
        agent_payload = _mapping(agent)
        state[str(agent_payload["id"])] = {
            "position": tuple(_sequence(agent_payload["initial_position"])),
            "status_flags": tuple(_sequence(agent_payload["initial_status_flags"])),
        }

    ticks_applied = 0
    for _loop in range(loops):
        for frame in frames:
            frame_payload = _mapping(frame)
            deltas = _mapping(frame_payload["deltas"])
            for agent_id, delta in deltas.items():
                current = state.setdefault(str(agent_id), {})
                delta_payload = _mapping(delta)
                if "position" in delta_payload:
                    current["position"] = tuple(_sequence(delta_payload["position"]))
                if "status_flags" in delta_payload:
                    current["status_flags"] = tuple(_sequence(delta_payload["status_flags"]))
            ticks_applied += 1
    return ticks_applied


def _hardware_snapshot() -> dict[str, object]:
    uname = platform.uname()
    return {
        "machine": uname.machine,
        "node": uname.node,
        "platform": platform.platform(),
        "processor": uname.processor or "unknown",
        "python": platform.python_version(),
        "ram_gb": _rounded(psutil.virtual_memory().total / (1024**3)),
        "system": uname.system,
    }


def _write_json(path: Path, report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown(path: Path, report: Mapping[str, object]) -> None:
    artifacts = [cast(dict[str, object], artifact) for artifact in _sequence(report["artifacts"])]
    hardware = cast(dict[str, object], report["hardware"])
    generated_at = str(report["generated_at"])
    lines = [
        "# Replay Throughput Benchmark",
        "",
        f"Generated at: `{generated_at}`",
        "",
        "## Methodology",
        "",
        "The benchmark loads each committed msgpack artifact with `msgpack.unpackb`, then applies "
        "all replay tick deltas in order for 20 sequential loops. Timings use `time.perf_counter`; "
        "RSS deltas use `psutil.Process().memory_info().rss` around load and replay phases.",
        "",
        "Check mode runs three measurements and compares the best current value to the committed "
        "baseline. It fails when load time, replay wall time, or FPS regresses by more than 15%. "
        "A 0.05s floor is applied to time metrics so millisecond-scale I/O noise does not fail "
        "small artifacts.",
        "",
        f"Hardware caveat: {HARDWARE_CAVEAT}",
        "",
        "Methodology script: "
        "[scripts/bench_replay_throughput.py]"
        "(https://github.com/Celovin/luvoire/blob/main/scripts/bench_replay_throughput.py).",
        "",
        "## Hardware",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| System | {hardware['system']} |",
        f"| Platform | {hardware['platform']} |",
        f"| Machine | {hardware['machine']} |",
        f"| Processor | {hardware['processor']} |",
        f"| RAM GB | {hardware['ram_gb']} |",
        f"| Python | {hardware['python']} |",
        "",
        "## Results",
        "",
        "| Artifact | Agent count | Grid | load_time_s | tick_wall_s_per_20x | fps_20x | rss_delta_mb | msgpack_size_mb | msgpack_sha256 |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for artifact in artifacts:
        lines.append(
            "| `{filename}` | {agent_count} | {grid} | {load_time_s} | {tick_wall_s_per_20x} | "
            "{fps_20x} | {rss_delta_mb} | {msgpack_size_mb} | `{msgpack_sha256}` |".format(
                **artifact
            )
        )
    lines.extend(
        [
            "",
            "## Artifact Commits",
            "",
            "| Artifact | Source commit |",
            "| --- | --- |",
        ]
    )
    for artifact in artifacts:
        lines.append(f"| `{artifact['filename']}` | `{artifact['artifact_commit']}` |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _check(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"missing benchmark baseline: {path}")
    baseline = json.loads(path.read_text(encoding="utf-8"))
    current = _best_check_report([build_report() for _ in range(CHECK_REPEATS)])
    failures = _compare_reports(
        cast(Mapping[str, object], baseline),
        cast(Mapping[str, object], current),
    )
    if failures:
        raise SystemExit("\n".join(failures))
    print("Replay throughput benchmark check OK.")


def _compare_reports(
    baseline: Mapping[str, object],
    current: Mapping[str, object],
) -> list[str]:
    baseline_artifacts = {
        str(artifact["filename"]): artifact
        for artifact in cast(Sequence[Mapping[str, object]], baseline["artifacts"])
    }
    current_artifacts = {
        str(artifact["filename"]): artifact
        for artifact in cast(Sequence[Mapping[str, object]], current["artifacts"])
    }
    failures: list[str] = []
    for filename, expected in baseline_artifacts.items():
        observed = current_artifacts.get(filename)
        if observed is None:
            failures.append(f"{filename}: missing current benchmark row")
            continue
        for key in ("agent_count", "grid", "msgpack_sha256", "msgpack_size_mb"):
            if observed[key] != expected[key]:
                failures.append(f"{filename}: {key} changed from {expected[key]} to {observed[key]}")
        _compare_slower_metric(failures, filename, expected, observed, "load_time_s")
        _compare_slower_metric(failures, filename, expected, observed, "tick_wall_s_per_20x")
        _compare_fps_metric(failures, filename, expected, observed)
    return failures


def _compare_slower_metric(
    failures: list[str],
    filename: str,
    expected: Mapping[str, object],
    observed: Mapping[str, object],
    key: str,
) -> None:
    baseline_value = float(expected[key])
    current_value = float(observed[key])
    threshold = max(
        baseline_value * (1 + REGRESSION_TOLERANCE),
        baseline_value + TIME_NOISE_FLOOR_SECONDS,
    )
    if current_value > threshold:
        failures.append(f"{filename}: {key} regressed from {baseline_value} to {current_value}")


def _compare_fps_metric(
    failures: list[str],
    filename: str,
    expected: Mapping[str, object],
    observed: Mapping[str, object],
) -> None:
    baseline_value = float(expected["fps_20x"])
    current_value = float(observed["fps_20x"])
    baseline_tick_wall = float(expected["tick_wall_s_per_20x"])
    ticks_per_replay = int(expected["tick_count"]) * REPLAY_LOOPS
    time_floor_fps = ticks_per_replay / (baseline_tick_wall + TIME_NOISE_FLOOR_SECONDS)
    threshold = min(baseline_value * (1 - REGRESSION_TOLERANCE), time_floor_fps)
    if current_value < threshold:
        failures.append(f"{filename}: fps_20x regressed from {baseline_value} to {current_value}")


def _best_check_report(reports: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not reports:
        raise ValueError("at least one report is required")
    first = reports[0]
    best_by_filename: dict[str, dict[str, object]] = {}
    for report in reports:
        for artifact in cast(Sequence[Mapping[str, object]], report["artifacts"]):
            filename = str(artifact["filename"])
            candidate = dict(artifact)
            current_best = best_by_filename.get(filename)
            if current_best is None:
                best_by_filename[filename] = candidate
                continue
            current_best["load_time_s"] = min(
                float(current_best["load_time_s"]),
                float(candidate["load_time_s"]),
            )
            current_best["tick_wall_s_per_20x"] = min(
                float(current_best["tick_wall_s_per_20x"]),
                float(candidate["tick_wall_s_per_20x"]),
            )
            current_best["fps_20x"] = max(
                float(current_best["fps_20x"]),
                float(candidate["fps_20x"]),
            )
            current_best["rss_delta_mb"] = min(
                float(current_best["rss_delta_mb"]),
                float(candidate["rss_delta_mb"]),
            )
    return {
        "artifacts": [
            best_by_filename[str(artifact["filename"])]
            for artifact in cast(Sequence[Mapping[str, object]], first["artifacts"])
        ],
        "generated_at": first["generated_at"],
        "hardware": first["hardware"],
        "methodology": first["methodology"],
    }


def _artifact_commit(path: Path) -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(path.relative_to(ROOT))],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("expected mapping")
    return cast(Mapping[str, Any], value)


def _sequence(value: object) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        raise TypeError("expected sequence")
    return cast(Sequence[Any], value)


def _rounded(value: float) -> float:
    return round(value, 6)


if __name__ == "__main__":
    raise SystemExit(main())
