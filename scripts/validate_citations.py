"""Validate research-note citation appendices for DOI and ISBN identifiers."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)
ISBN_PATTERN = re.compile(r"\b(?:97[89][-\s]?)?(?:\d[-\s]?){9,12}[\dX]\b", re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_dir", type=Path)
    args = parser.parse_args()

    failures: list[str] = []
    markdown_paths = sorted(args.research_dir.rglob("*_research.md"))
    if not markdown_paths:
        raise SystemExit(f"No research markdown files found under {args.research_dir}")
    for path in markdown_paths:
        text = path.read_text(encoding="utf-8")
        if "## Citation appendix" not in text:
            failures.append(f"{path}: missing Citation appendix section")
            continue
        appendix = text.split("## Citation appendix", 1)[1]
        identifiers = _identifiers(appendix)
        if len(identifiers) < 5:
            failures.append(f"{path}: expected at least 5 DOI/ISBN identifiers, found {len(identifiers)}")
        for identifier in identifiers:
            if identifier.lower().startswith("10."):
                continue
            if not _valid_isbn(identifier):
                failures.append(f"{path}: invalid ISBN checksum {identifier}")
        if "wikipedia.org" in appendix.lower():
            failures.append(f"{path}: Wikipedia URL appears in Citation appendix")
    if failures:
        raise SystemExit("\n".join(failures))


def _identifiers(text: str) -> list[str]:
    values = [match.group(0).rstrip(".,);]") for match in DOI_PATTERN.finditer(text)]
    values.extend(match.group(0).rstrip(".,);]") for match in ISBN_PATTERN.finditer(text))
    return values


def _valid_isbn(value: str) -> bool:
    digits = re.sub(r"[-\s]", "", value).upper()
    if len(digits) == 10:
        total = 0
        for index, char in enumerate(digits, start=1):
            if char == "X":
                if index != 10:
                    return False
                number = 10
            else:
                number = int(char)
            total += index * number
        return total % 11 == 0
    if len(digits) == 13:
        total = sum((1 if index % 2 == 0 else 3) * int(char) for index, char in enumerate(digits[:12]))
        check = (10 - (total % 10)) % 10
        return check == int(digits[-1])
    return False


if __name__ == "__main__":
    main()
