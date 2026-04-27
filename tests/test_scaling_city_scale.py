from __future__ import annotations

from pathlib import Path

import pytest

from luvoire.scaling import CityScaleConfig, CityScaleRunner


def test_city_scale_small_run_is_reproducible_across_backends() -> None:
    base = CityScaleConfig(
        agent_count=50,
        tick_count=10,
        seed=20260421,
        workers=4,
        backend="single",
    )
    single_first = CityScaleRunner(base).run()
    single_second = CityScaleRunner(base).run()
    multiprocess = CityScaleRunner(
        CityScaleConfig(
            agent_count=50,
            tick_count=10,
            seed=20260421,
            workers=4,
            backend="multiprocessing",
        )
    ).run()

    assert single_first.output_hash == single_second.output_hash
    assert single_first.output_hash == multiprocess.output_hash
    assert single_first.to_json_dict(include_frames=False)["event_count"] >= 0


def test_city_scale_result_tracks_throughput_and_messages() -> None:
    result = CityScaleRunner(
        CityScaleConfig(agent_count=12, tick_count=3, seed=7, workers=2, backend="single")
    ).run()

    assert result.config.agent_ticks == 36
    assert result.throughput_agent_ticks_per_second > 0
    assert result.inter_shard_messages >= 0


def test_city_scale_aggregate_mode_stores_only_sampled_frames() -> None:
    config = CityScaleConfig(
        agent_count=100,
        tick_count=4,
        seed=11,
        workers=4,
        backend="single",
        trace_mode="aggregate",
        sample_agent_count=7,
    )

    first = CityScaleRunner(config).run()
    second = CityScaleRunner(config).run()

    assert first.output_hash == second.output_hash
    assert first.frame_count_total == 400
    assert len(first.frames) == 28
    assert len(first.aggregates) == 4
    assert first.aggregates[0].agent_count == 100
    assert first.to_json_dict(include_frames=False)["stored_frame_count"] == 28


def test_city_scale_aggregate_parquet_export(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    pytest.importorskip("pyarrow.parquet")

    result = CityScaleRunner(
        CityScaleConfig(
            agent_count=30,
            tick_count=3,
            seed=17,
            workers=2,
            backend="single",
            trace_mode="aggregate",
            sample_agent_count=5,
        )
    ).run()
    parquet_path = tmp_path / "aggregates.parquet"
    jsonl_path = tmp_path / "aggregates.jsonl"

    result.write_aggregate_parquet(parquet_path)
    result.write_aggregate_jsonl(jsonl_path)

    assert parquet_path.exists()
    assert jsonl_path.read_text(encoding="utf-8").count("\n") == 3
