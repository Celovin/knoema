from __future__ import annotations

import argparse
import json
from collections.abc import Callable

try:
    from scripts.external_activation_status import collect_external_activation_status
    from scripts.release_dry_run import run_release_dry_run
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from external_activation_status import collect_external_activation_status
    from release_dry_run import run_release_dry_run


ExternalStatusCollector = Callable[[], dict[str, object]]
ReleaseDryRun = Callable[[str, bool], dict[str, object]]


def run_pre_release_check(
    version: str,
    *,
    keep: bool = False,
    collect_status: ExternalStatusCollector = collect_external_activation_status,
    dry_run: ReleaseDryRun = run_release_dry_run,
) -> dict[str, object]:
    external_status = collect_status()
    dry_run_result = dry_run(version, keep)
    return {
        "version": version,
        "external_activation": external_status,
        "release_dry_run": dry_run_result,
        "ready_for_release_tag": external_status["ready_for_external_activation"]
        and dry_run_result.get("status") == "ok",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run external activation status checks and a local release dry run."
    )
    parser.add_argument("--version", required=True, help="Semantic version to test, for example 0.3.0.")
    parser.add_argument("--keep", action="store_true", help="Keep temporary dry-run build files.")
    parser.add_argument(
        "--fail-on-external-blockers",
        action="store_true",
        help="Exit with status 1 when external activation blockers are still present.",
    )
    args = parser.parse_args()

    result = run_pre_release_check(args.version, keep=args.keep)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    if args.fail_on_external_blockers and not result["external_activation"]["ready_for_external_activation"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
