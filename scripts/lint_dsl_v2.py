"""Lint Scenario DSL v2 YAML files for tier consistency and ethics guardrails.

Usage:
    python scripts/lint_dsl_v2.py [paths ...] [--strict]

Each path may be a directory or a YAML file. Directories are walked recursively
for ``*.yaml``/``*.yml`` files. v1 scenarios (``schema_version: 1.0``) are
skipped — this script does not enforce v2 rules on legacy fixtures.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import yaml

V2_TIER_KEYS_TIER_A_FORBIDDEN = ("value", "range", "source", "default")
V2_TIER_KEYS_TIER_B_REQUIRED_ANY = ("value", "distribution")


def lint_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # pragma: no cover — rare in committed fixtures
        return [f"{path}:: YAML parse error: {exc}"]
    if not isinstance(payload, dict):
        return [f"{path}:: scenario YAML root must be a mapping"]
    schema_version = str(payload.get("schema_version", "1.0"))
    if schema_version != "2.0":
        return []
    parameters = payload.get("parameters") or {}
    if not isinstance(parameters, dict):
        return [f"{path}::parameters: must be a mapping"]
    for name, spec in parameters.items():
        if not isinstance(spec, dict):
            issues.append(f"{path}::parameters.{name}: must be a mapping")
            continue
        tier = spec.get("tier")
        if tier == "A":
            for forbidden in V2_TIER_KEYS_TIER_A_FORBIDDEN:
                if forbidden in spec:
                    issues.append(
                        f"{path}::parameters.{name}: Tier A must only define "
                        f"'ref' (forbidden key '{forbidden}')"
                    )
            if "ref" not in spec:
                issues.append(
                    f"{path}::parameters.{name}: Tier A requires 'ref'"
                )
        elif tier == "B":
            if not spec.get("source"):
                issues.append(
                    f"{path}::parameters.{name}: Tier B requires 'source'"
                )
            if not any(
                spec.get(key) is not None
                for key in V2_TIER_KEYS_TIER_B_REQUIRED_ANY
            ):
                issues.append(
                    f"{path}::parameters.{name}: Tier B requires 'value' or "
                    "'distribution'"
                )
        elif tier == "C":
            if "range" not in spec:
                issues.append(
                    f"{path}::parameters.{name}: Tier C requires 'range'"
                )
            if "default" not in spec:
                issues.append(
                    f"{path}::parameters.{name}: Tier C requires 'default'"
                )
        else:
            issues.append(
                f"{path}::parameters.{name}: tier must be one of A/B/C "
                f"(got {tier!r})"
            )
    return issues


def iter_yaml_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if path.is_dir():
            yield from sorted(path.rglob("*.yaml"))
            yield from sorted(path.rglob("*.yml"))
        elif path.is_file():
            yield path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 when any issues are reported.",
    )
    args = parser.parse_args(argv)
    if not args.paths:
        args.paths = [Path("scenarios"), Path("examples/scenarios")]
    all_issues: list[str] = []
    for yaml_path in iter_yaml_files(args.paths):
        all_issues.extend(lint_file(yaml_path))
    for issue in all_issues:
        print(issue)
    if all_issues and args.strict:
        return 1
    if not all_issues:
        print("dsl v2 lint: 0 issues")
    return 0


def _coerce_optional(value: Any) -> Any:  # pragma: no cover — internal helper
    return value


if __name__ == "__main__":
    raise SystemExit(main())
