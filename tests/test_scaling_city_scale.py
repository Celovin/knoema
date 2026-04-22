from __future__ import annotations

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
