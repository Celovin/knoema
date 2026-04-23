from __future__ import annotations

import hashlib
from pathlib import Path

REPLAY_SHA256_BASELINES = {
    "demo/replay/replay_100agents_gangnam_7pm.msgpack": "8e00496a491218ef541378ebe990b20040f071c1fb7821ba82e050b00c7447ab",
    "demo/replay/replay_1000agents_gangnam_7pm.msgpack": "0cc79baf78a81cfdbad33fae7b437a2cb9de135b39a6abcde1fffbdb4dfb884b",
    "demo/replay/replay_5000agents_gangnam_7pm.msgpack": "d253d008f340a2661d15aa0f86f4cf1e5aa7b403c689e07eea5d0b1cc7a39c01",
    "demo/replay/replay_10000agents_gangnam_7pm.msgpack": "af326a00b59286d5eb24d1dbab1442e74f8f2a6908d33325864c184b34e4e4d2",
    "demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack": "9b3fc9944ee08da97f6775199ce4ef6a3fad0fc2e5db25093e1122547faeb3f9",
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures: list[str] = []
    for rel_path, expected in REPLAY_SHA256_BASELINES.items():
        path = root / rel_path
        if not path.exists():
            failures.append(f"{rel_path}: missing")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            failures.append(f"{rel_path}: {actual} != {expected}")
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(f"verified {len(REPLAY_SHA256_BASELINES)} replay SHA256 baselines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
