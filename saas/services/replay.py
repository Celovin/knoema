"""Replay helpers for dashboard windows and A/B timelines."""

from __future__ import annotations

from typing import Any


def playback_window(
    rows: list[dict[str, Any]],
    *,
    tick_start: int,
    tick_end: int,
) -> list[dict[str, Any]]:
    return [row for row in rows if tick_start <= int(row["tick"]) <= tick_end]


def ab_timeline(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ticks = sorted({int(row["tick"]) for row in [*left, *right]})
    output: list[dict[str, Any]] = []
    for tick in ticks:
        left_count = sum(1 for row in left if int(row["tick"]) == tick)
        right_count = sum(1 for row in right if int(row["tick"]) == tick)
        output.append({"tick": tick, "A": left_count, "B": right_count, "delta": right_count - left_count})
    return output
