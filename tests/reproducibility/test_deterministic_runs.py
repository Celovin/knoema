from __future__ import annotations

from tests.reproducibility._helpers import (
    build_seeded_simulator,
    canonical_memory_text,
    export_log_text,
    sha256_text,
)


def test_same_seed_produces_bit_for_bit_logs_and_canonical_memories() -> None:
    log_hashes: set[str] = set()
    memory_hashes: set[str] = set()

    for _ in range(10):
        simulator = build_seeded_simulator(seed=20260418)
        logs = simulator.run(duration_days=1)
        log_hashes.add(sha256_text(export_log_text(logs)))
        memory_hashes.add(sha256_text(canonical_memory_text(simulator)))

    assert len(log_hashes) == 1
    assert len(memory_hashes) == 1
