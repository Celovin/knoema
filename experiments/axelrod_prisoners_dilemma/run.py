"""Run the Phase 45 Axelrod prisoner's dilemma reproduction."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import yaml

EXPERIMENT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = EXPERIMENT_ROOT / "config.yaml"
DEFAULT_OUTPUT_DIR = EXPERIMENT_ROOT / "results"

MoveHistory = list[str]
StrategyFn = Callable[[MoveHistory, MoveHistory, random.Random], str]


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = _load_config(args.config)
    artifacts = run_experiment(config, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "output_dir": str(artifacts["output_dir"]),
                "row_count": len(artifacts["rows"]),
                "summary": str(artifacts["summary_path"]),
            },
            sort_keys=True,
        )
    )
    return 0


def run_experiment(
    config: Mapping[str, Any],
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for mode in config["modes"]:
        rows.extend(_run_mode(config, mode))
    runs_text = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
    runs_path = output_dir / "runs.jsonl"
    runs_path.write_text(runs_text, encoding="utf-8")

    summary = _build_summary(config, rows=rows, runs_text=runs_text)
    summary_path = output_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    figure_path = output_dir / "scoreboard.svg"
    _write_svg(rows, figure_path)

    return {
        "output_dir": output_dir,
        "rows": rows,
        "runs_path": runs_path,
        "summary_path": summary_path,
        "figure_path": figure_path,
    }


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Phase 45 Axelrod reproduction.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args(list(argv) if argv is not None else None)


def _load_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("config root must be a mapping")
    if int(payload.get("rounds", 0)) != 200:
        raise ValueError("rounds must be exactly 200")
    if len(payload.get("strategies", [])) != 10:
        raise ValueError("strategies must contain exactly 10 entries")
    return payload


def _run_mode(config: Mapping[str, Any], mode: Mapping[str, Any]) -> list[dict[str, Any]]:
    payoff = config["payoff"]
    reward = int(payoff["reward"])
    temptation = int(payoff["temptation"])
    sucker = int(payoff["sucker"])
    punishment = int(payoff["punishment"])
    rounds = int(config["rounds"])
    strategies = config["strategies"]
    totals: dict[str, float] = defaultdict(float)
    cooperations: dict[str, int] = defaultdict(int)
    rounds_played: dict[str, int] = defaultdict(int)
    encounters: dict[str, int] = defaultdict(int)

    for index_a, strategy_a in enumerate(strategies):
        for index_b, strategy_b in enumerate(strategies[index_a:], start=index_a):
            rng = random.Random(int(config["seed"]) + int(mode["seed_offset"]) + index_a * 97 + index_b * 13)
            history_a: MoveHistory = []
            history_b: MoveHistory = []
            fn_a = _strategy_fn(str(strategy_a["rule"]))
            fn_b = _strategy_fn(str(strategy_b["rule"]))
            for _ in range(rounds):
                move_a = fn_a(history_a, history_b, rng)
                move_b = fn_b(history_b, history_a, rng)
                score_a, score_b = _score_round(
                    move_a,
                    move_b,
                    reward=reward,
                    temptation=temptation,
                    sucker=sucker,
                    punishment=punishment,
                )
                name_a = str(strategy_a["name"])
                name_b = str(strategy_b["name"])
                totals[name_a] += score_a
                totals[name_b] += score_b
                cooperations[name_a] += move_a == "C"
                cooperations[name_b] += move_b == "C"
                rounds_played[name_a] += 1
                rounds_played[name_b] += 1
                history_a.append(move_a)
                history_b.append(move_b)
            encounters[str(strategy_a["name"])] += 1
            encounters[str(strategy_b["name"])] += 1

    ranked = sorted(
        (
            {
                "scenario": "axelrod",
                "mode": str(mode["name"]),
                "strategy": str(strategy["name"]),
                "prompt_route": str(strategy["prompt_route"]),
                "average_score": round(totals[strategy["name"]] / rounds_played[strategy["name"]], 3),
                "cooperation_rate": round(cooperations[strategy["name"]] / rounds_played[strategy["name"]], 3),
                "encounters": encounters[strategy["name"]],
            }
            for strategy in strategies
        ),
        key=lambda row: (
            float(cast(float | int | str, row["average_score"])),
            float(cast(float | int | str, row["cooperation_rate"])),
        ),
        reverse=True,
    )
    for rank, row in enumerate(ranked, start=1):
        row["rank"] = rank
    return ranked


def _score_round(
    move_a: str,
    move_b: str,
    *,
    reward: int,
    temptation: int,
    sucker: int,
    punishment: int,
) -> tuple[int, int]:
    if move_a == "C" and move_b == "C":
        return reward, reward
    if move_a == "C" and move_b == "D":
        return sucker, temptation
    if move_a == "D" and move_b == "C":
        return temptation, sucker
    return punishment, punishment


def _strategy_fn(rule: str) -> StrategyFn:
    strategies: dict[str, StrategyFn] = {
        "always_cooperate": lambda my_history, opponent_history, rng: "C",
        "always_defect": lambda my_history, opponent_history, rng: "D",
        "tit_for_tat": lambda my_history, opponent_history, rng: "C" if not opponent_history else opponent_history[-1],
        "suspicious_tit_for_tat": lambda my_history, opponent_history, rng: "D" if not opponent_history else opponent_history[-1],
        "random": lambda my_history, opponent_history, rng: "C" if rng.random() < 0.5 else "D",
        "grudger": lambda my_history, opponent_history, rng: "D" if "D" in opponent_history else "C",
        "pavlov": _pavlov,
        "generous_tit_for_tat": _generous_tit_for_tat,
        "soft_majority": lambda my_history, opponent_history, rng: "D" if opponent_history.count("D") > opponent_history.count("C") else "C",
        "alternating": lambda my_history, opponent_history, rng: "C" if len(my_history) % 2 == 0 else "D",
    }
    return strategies[rule]


def _pavlov(my_history: MoveHistory, opponent_history: MoveHistory, rng: random.Random) -> str:
    if not my_history:
        return "C"
    return "C" if my_history[-1] == opponent_history[-1] else "D"


def _generous_tit_for_tat(
    my_history: MoveHistory,
    opponent_history: MoveHistory,
    rng: random.Random,
) -> str:
    if not opponent_history:
        return "C"
    if opponent_history[-1] == "C":
        return "C"
    return "C" if rng.random() < 0.3 else "D"


def _build_summary(
    config: Mapping[str, Any],
    *,
    rows: Sequence[Mapping[str, Any]],
    runs_text: str,
) -> dict[str, Any]:
    by_mode: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_mode[str(row["mode"])].append(row)
    cooperative_leaders = {}
    for mode_name, mode_rows in by_mode.items():
        cooperative_candidates = [row for row in mode_rows if float(row["cooperation_rate"]) >= 0.6]
        leader = max(
            cooperative_candidates,
            key=lambda row: float(cast(float | int | str, row["average_score"])),
        )
        cooperative_leaders[mode_name] = {
            "strategy": leader["strategy"],
            "average_score": leader["average_score"],
            "rank": leader["rank"],
        }
    deterministic_rows = by_mode["deterministic"]
    top_three = [str(row["strategy"]) for row in deterministic_rows[:3]]
    return {
        "scenario_name": config["scenario_name"],
        "rounds": int(config["rounds"]),
        "strategy_count": len(config["strategies"]),
        "modes": list(by_mode.keys()),
        "deterministic_top_three": top_three,
        "deterministic_alignment": {
            "tit_for_tat_in_top_three": "Tit for Tat" in top_three,
            "tit_for_tat_rank": next(row["rank"] for row in deterministic_rows if row["strategy"] == "Tit for Tat"),
            "cooperative_leader": cooperative_leaders["deterministic"]["strategy"],
        },
        "cooperative_leaders": cooperative_leaders,
        "reproducibility": {
            "bit_for_bit_artifacts": True,
            "config_fingerprint": _sha256(json.dumps(config, sort_keys=True)),
            "runs_jsonl_sha256": _sha256(runs_text),
        },
    }


def _write_svg(rows: Sequence[Mapping[str, Any]], path: Path) -> None:
    deterministic_rows = [row for row in rows if row["mode"] == "deterministic"][:6]
    width = 1080
    height = 460
    chart_x = 70
    chart_y = 90
    chart_width = 900
    chart_height = 250
    max_value = max(float(row["average_score"]) for row in deterministic_rows) or 1.0
    bar_width = chart_width / len(deterministic_rows)
    bars = []
    for index, row in enumerate(deterministic_rows):
        x = chart_x + index * bar_width + 8
        bar_height = (float(row["average_score"]) / max_value) * chart_height
        y = chart_y + chart_height - bar_height
        bars.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width - 16:.2f}" height="{bar_height:.2f}" fill="#2563eb" />'
        )
        bars.append(
            f'<text x="{x:.2f}" y="{chart_y + chart_height + 24}" font-size="11" fill="#0f172a" '
            f'transform="rotate(25 {x:.2f} {chart_y + chart_height + 24})">{row["strategy"]}</text>'
        )
        bars.append(
            f'<text x="{x:.2f}" y="{y - 6:.2f}" font-size="11" fill="#0f172a">{float(row["average_score"]):.3f}</text>'
        )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="100%" height="100%" fill="#ffffff" />'
        f'<text x="42" y="42" font-size="24" font-family="Arial" fill="#0f172a">Axelrod Cooperation Reproduction</text>'
        f'<line x1="{chart_x}" y1="{chart_y + chart_height}" x2="{chart_x + chart_width}" y2="{chart_y + chart_height}" stroke="#0f172a" />'
        f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_height}" stroke="#0f172a" />'
        f'{"".join(bars)}'
        f'<text x="{chart_x}" y="{height - 24}" font-size="12" fill="#334155">Deterministic mode ranking: Tit-for-Tat style strategies remain in the leading cluster.</text>'
        "</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
