from __future__ import annotations

import subprocess
from pathlib import Path


TOKEN_ARGS = ["knoema", "Knoema", "KNOEMA"]

ALLOWLIST = {
    Path("src/knoema/__init__.py"),
    Path("src/knoema_compat/__init__.py"),
    Path("tests/test_knoema_compat_shim.py"),
    Path("tests/test_v7_rename_sweep.py"),
    # Slot B backward-compat env var references (KNOEMA_* string literals accepted
    # for one release cycle per v7 handoff §2.2 env var compatibility shim).
    Path("src/luvoire/api/auth.py"),
    Path("src/luvoire/api/rate_limit.py"),
    Path("src/luvoire/api/server.py"),
    Path("src/luvoire/config.py"),
    Path("src/luvoire/multimodal/tts.py"),
    Path("src/luvoire/telemetry/client.py"),
    Path("tests/test_bench_replay_perf.py"),
    Path("tests/test_env_var_compat_shim.py"),
}


def test_slot_a_python_sources_have_only_explicit_legacy_compat_tokens() -> None:
    candidates = [
        path
        for path in subprocess.check_output(["git", "ls-files"], text=True).splitlines()
        if path.startswith(("src/", "tests/", "scripts/")) and Path(path).suffix == ".py"
    ]
    offenders: list[str] = []
    for rel in candidates:
        path = Path(rel)
        if path in ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in TOKEN_ARGS):
            offenders.append(rel)

    assert offenders == []
