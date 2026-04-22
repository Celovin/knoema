"""Auditable reproducibility fingerprints for Luvoire runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "luvoire.run_fingerprint.v1"
EMPTY_MERKLE_ROOT = hashlib.sha256(b"luvoire-empty-jsonl").hexdigest()
KEY_DEPENDENCIES = (
    "luvoire-engine",
    "pydantic",
    "PyYAML",
    "networkx",
    "sqlalchemy",
    "gradio",
    "plotly",
)


@dataclass(frozen=True, slots=True)
class VerificationReport:
    verified: bool
    checked: tuple[str, ...]
    mismatches: tuple[str, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "checked": list(self.checked),
            "mismatches": list(self.mismatches),
        }


def generate_run_fingerprint(
    run_config: Mapping[str, Any] | Sequence[Any] | str,
    result: Mapping[str, Any] | Sequence[Any] | str,
    *,
    metadata: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Generate a deterministic audit fingerprint for a run config and result."""

    input_hash = canonical_sha256(run_config)
    output_merkle_root = result_merkle_root(result)
    environment = environment_fingerprint()
    stable_payload = {
        "schema_version": SCHEMA_VERSION,
        "input_hash": input_hash,
        "output_merkle_root": output_merkle_root,
        "environment": environment,
    }
    return {
        **stable_payload,
        "fingerprint": canonical_sha256(stable_payload),
        "hash_algorithm": "sha256",
        "merkle_algorithm": "sha256-pairwise-duplicate-last",
        "generated_at": generated_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        "metadata": dict(metadata or {}),
    }


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def result_merkle_root(result: Mapping[str, Any] | Sequence[Any] | str) -> str:
    records = result_records(result)
    if not records:
        return EMPTY_MERKLE_ROOT
    leaves = [hashlib.sha256(canonical_json_bytes(record)).digest() for record in records]
    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        leaves = [
            hashlib.sha256(leaves[index] + leaves[index + 1]).digest()
            for index in range(0, len(leaves), 2)
        ]
    return leaves[0].hex()


def result_records(result: Mapping[str, Any] | Sequence[Any] | str) -> list[Any]:
    if isinstance(result, str):
        lines = [line for line in result.splitlines() if line.strip()]
        if not lines:
            return []
        records: list[Any] = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append(line)
        return records
    if isinstance(result, Mapping):
        return [dict(result)]
    return list(result)


def environment_fingerprint() -> dict[str, Any]:
    dependencies: dict[str, str] = {}
    for dependency in KEY_DEPENDENCIES:
        version = _package_version(dependency)
        if version is not None:
            dependencies[dependency] = version
    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "dependencies": dependencies,
    }


def verify_run_fingerprint(
    certificate: Mapping[str, Any],
    *,
    run_config: Mapping[str, Any] | Sequence[Any] | str | None = None,
    result: Mapping[str, Any] | Sequence[Any] | str | None = None,
) -> VerificationReport:
    checked: list[str] = ["schema_version", "fingerprint"]
    mismatches: list[str] = []

    if certificate.get("schema_version") != SCHEMA_VERSION:
        mismatches.append("schema_version")

    stable_payload = {
        "schema_version": certificate.get("schema_version"),
        "input_hash": certificate.get("input_hash"),
        "output_merkle_root": certificate.get("output_merkle_root"),
        "environment": certificate.get("environment"),
    }
    if canonical_sha256(stable_payload) != certificate.get("fingerprint"):
        mismatches.append("fingerprint")

    if run_config is not None:
        checked.append("input_hash")
        if canonical_sha256(run_config) != certificate.get("input_hash"):
            mismatches.append("input_hash")

    if result is not None:
        checked.append("output_merkle_root")
        if result_merkle_root(result) != certificate.get("output_merkle_root"):
            mismatches.append("output_merkle_root")

    return VerificationReport(
        verified=not mismatches,
        checked=tuple(checked),
        mismatches=tuple(mismatches),
    )


def verification_guide_markdown(certificate: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Luvoire Reproducibility Certificate",
            "",
            f"- Fingerprint: `{certificate.get('fingerprint', '')}`",
            f"- Input hash: `{certificate.get('input_hash', '')}`",
            f"- Output Merkle root: `{certificate.get('output_merkle_root', '')}`",
            f"- Generated at: `{certificate.get('generated_at', '')}`",
            "",
            "## Verify",
            "",
            "```powershell",
            "python scripts/luvoire_verify.py run_fingerprint.json --result-jsonl run.jsonl",
            "```",
            "",
            "The verifier recomputes the JSONL Merkle root and fails if any line changes.",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="luvoire-verify",
        description="Verify a Luvoire reproducibility certificate.",
    )
    parser.add_argument("certificate", type=Path, help="Path to run_fingerprint.json.")
    parser.add_argument("--run-config", type=Path, default=None, help="Optional JSON config to hash.")
    parser.add_argument("--result-jsonl", type=Path, default=None, help="Optional result JSONL to verify.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable verification JSON.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    certificate = json.loads(args.certificate.read_text(encoding="utf-8"))
    run_config = _load_optional_json_or_text(args.run_config)
    result = args.result_jsonl.read_text(encoding="utf-8") if args.result_jsonl else None
    report = verify_run_fingerprint(certificate, run_config=run_config, result=result)
    if args.json:
        print(json.dumps(report.to_json_dict(), ensure_ascii=False, sort_keys=True))
    elif report.verified:
        print("Luvoire reproducibility certificate verified.")
    else:
        print("Luvoire reproducibility certificate verification failed:")
        for mismatch in report.mismatches:
            print(f"- {mismatch}")
    return 0 if report.verified else 1


def _load_optional_json_or_text(path: Path | None) -> Any | None:
    if path is None:
        return None
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _package_version(distribution_name: str) -> str | None:
    try:
        return importlib_metadata.version(distribution_name)
    except importlib_metadata.PackageNotFoundError:
        if distribution_name == "luvoire-engine":
            module = sys.modules.get("luvoire")
            version = getattr(module, "__version__", None)
            return str(version) if version is not None else None
        return None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
