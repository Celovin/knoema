"""Validate a Luvoire Bench YAML submission."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from build_leaderboard import validate_submission_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", type=Path, help="Path to a bench/submissions/*.yaml file")
    args = parser.parse_args(argv)

    try:
        validate_submission_file(args.submission)
    except Exception as exc:
        print(f"FAIL {args.submission}: {exc}", file=sys.stderr)
        return 1

    print(f"PASS {args.submission}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
