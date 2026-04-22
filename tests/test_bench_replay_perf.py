from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(
    os.environ.get("KNOEMA_SKIP_PERF_TESTS") == "1",
    reason="KNOEMA_SKIP_PERF_TESTS=1 disables replay throughput checks.",
)
def test_replay_throughput_benchmark_matches_committed_baseline() -> None:
    subprocess.run(
        [sys.executable, "scripts/bench_replay_throughput.py", "--check"],
        cwd=ROOT,
        check=True,
        timeout=180,
    )
