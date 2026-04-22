"""Replace ARXIV_ID_PENDING with a confirmed arXiv identifier across all metadata.

After arXiv accepts the Luvoire paper and assigns an identifier, run:

    python scripts/set_arxiv_id.py 2604.12345

This sweeps every committed file (excluding planning, runs, build artifacts) and
substitutes the placeholder. Refuses to touch the tree if no occurrences are
found, and prints a summary of files modified for the resulting commit.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER = "ARXIV_ID_PENDING"
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "tmp", "runs", "dist", "build", "planning", "site"}
SKIP_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".woff", ".woff2", ".ttf", ".pyc", ".pyo"}


def find_candidates(root: Path) -> list[Path]:
    matches: list[Path] = []
    self_path = Path(__file__).resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() == self_path:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if PLACEHOLDER in text:
            matches.append(path)
    return matches


def replace_in_file(path: Path, new_id: str) -> int:
    text = path.read_text(encoding="utf-8")
    new_text, count = re.subn(re.escape(PLACEHOLDER), new_id, text)
    if count:
        path.write_text(new_text, encoding="utf-8")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arxiv_id", help="arXiv identifier (e.g. 2604.12345 or 2604.12345v1)")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to scan (default: parent of this script)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    args = parser.parse_args()

    if not ARXIV_ID_PATTERN.match(args.arxiv_id):
        print(f"error: '{args.arxiv_id}' does not match arXiv id pattern YYMM.NNNNN[vN]", file=sys.stderr)
        return 2

    candidates = find_candidates(args.root)
    if not candidates:
        print(f"no occurrences of {PLACEHOLDER} found under {args.root}")
        return 1

    print(f"found {PLACEHOLDER} in {len(candidates)} files:")
    total = 0
    for path in sorted(candidates):
        rel = path.relative_to(args.root)
        if args.dry_run:
            text = path.read_text(encoding="utf-8")
            count = text.count(PLACEHOLDER)
            print(f"  would replace {count} in {rel}")
            total += count
            continue
        count = replace_in_file(path, args.arxiv_id)
        print(f"  replaced {count} in {rel}")
        total += count

    verb = "Would replace" if args.dry_run else "Replaced"
    print(f"\n{verb} {total} occurrence(s) of {PLACEHOLDER} with {args.arxiv_id}.")
    if not args.dry_run:
        print("Suggested next step:")
        print(f"  git add -A && git commit -m 'docs(arxiv): wire arxiv id {args.arxiv_id}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
