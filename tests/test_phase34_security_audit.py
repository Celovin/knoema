from __future__ import annotations

import json
from pathlib import Path


def test_phase34_security_policy_and_audit_artifacts_exist() -> None:
    expected = [
        ".github/dependabot.yml",
        "docs/SECURITY.md",
        "docs/security/audit_2026-04-18.md",
        "docs/security/knoema-sbom.cdx.json",
    ]

    missing = [path for path in expected if not Path(path).exists()]

    assert missing == []


def test_phase34_security_extra_declares_audit_tools() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    for package in ["bandit", "pip-audit", "safety", "cyclonedx-bom"]:
        assert package in pyproject


def test_phase34_audit_report_records_zero_high_or_critical_findings() -> None:
    report = Path("docs/security/audit_2026-04-18.md").read_text(encoding="utf-8")

    assert "No critical or high-severity vulnerabilities were found" in report
    assert "| Critical | None | Not found |" in report
    assert "| High | None | Not found |" in report
    assert "secret_scanning.status = disabled" in report
    assert "dependabot_security_updates.status = disabled" in report


def test_phase34_sbom_is_cyclonedx_json() -> None:
    sbom = json.loads(Path("docs/security/knoema-sbom.cdx.json").read_text(encoding="utf-8"))

    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.6"
    assert len(sbom["components"]) >= 50
