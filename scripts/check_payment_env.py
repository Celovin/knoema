"""Print payment-related environment variable status without revealing values."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover - fallback for minimal environments
    dotenv_values = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env.local"
REQUIRED_KEYS = [
    "TOSS_CLIENT_KEY",
    "TOSS_SECRET_KEY",
    "PADDLE_API_KEY",
    "PADDLE_WEBHOOK_SECRET",
    "STRIPE_TEST_SECRET_KEY",
]


def main() -> None:
    values = _load_env_file()
    print("Payment environment status")
    print(f".env.local: {'found' if ENV_PATH.exists() else 'missing'}")
    print("")
    print("| Variable | Status |")
    print("| --- | --- |")
    for key in REQUIRED_KEYS:
        is_set = bool(os.environ.get(key) or values.get(key))
        print(f"| {key} | {'set' if is_set else 'unset'} |")


def _load_env_file() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    if dotenv_values is not None:
        parsed = dotenv_values(ENV_PATH)
        return {key: value for key, value in parsed.items() if key and value}
    return _parse_simple_env(ENV_PATH)


def _parse_simple_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() and value.strip():
            values[key.strip()] = value.strip().strip("'\"")
    return values


if __name__ == "__main__":
    main()
