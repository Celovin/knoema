from __future__ import annotations

import json
from pathlib import Path


def test_phase35_default_ci_uses_fast_cached_quality_gate() -> None:
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "concurrency:" in workflow
    assert "PRE_COMMIT_HOME: /tmp/knoema-pre-commit-cache" in workflow
    assert "cache-dependency-path: pyproject.toml" in workflow
    assert "path: /tmp/knoema-pre-commit-cache" in workflow
    assert "actions/cache@v5" in workflow
    assert "path: .pytest_cache" in workflow
    assert 'python-version: "3.12"' in workflow
    assert "python -m pip install -e \".[dev,release]\"" in workflow
    assert "mypy src" in workflow
    assert "pytest --cov-fail-under=90" in workflow
    assert "python scripts/release_dry_run.py --version 0.1.1" in workflow


def test_phase35_compatibility_workflow_declares_cross_platform_matrix() -> None:
    workflow = Path(".github/workflows/compatibility.yml").read_text(encoding="utf-8")

    assert "workflow_dispatch:" in workflow
    assert "macos-latest" in workflow
    assert "windows-latest" in workflow
    assert "ubuntu-latest" in workflow
    assert "actions/cache@v5" in workflow
    assert 'python-version: ["3.11", "3.12"]' in workflow
    assert "pytest tests/test_version.py tests/test_phase1_types.py --no-cov -q" in workflow


def test_phase35_release_workflow_uses_oidc_pypi_publish() -> None:
    workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "tags:" in workflow
    assert '"v*.*.*"' in workflow
    assert "twine check dist/*" in workflow
    assert "actions/download-artifact@v7" in workflow
    assert "environment:" in workflow
    assert "name: pypi" in workflow
    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "twine upload" not in workflow
    assert "PYPI_TOKEN" not in workflow


def test_phase35_release_please_manifest_is_configured() -> None:
    config = json.loads(Path(".github/release-please-config.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path(".release-please-manifest.json").read_text(encoding="utf-8"))
    workflow = Path(".github/workflows/release-please.yml").read_text(encoding="utf-8")

    package = config["packages"]["."]
    assert package["release-type"] == "python"
    assert package["package-name"] == "knoema-engine"
    assert package["changelog-path"] == "CHANGELOG.md"
    assert "src/knoema/__init__.py" in package["extra-files"]
    assert manifest["."] == "0.1.0"
    assert "vars.ENABLE_RELEASE_PLEASE == '1'" in workflow


def test_phase35_release_dry_run_script_and_docs_exist() -> None:
    script = Path("scripts/release_dry_run.py").read_text(encoding="utf-8")
    docs = Path("docs/ci-release-automation.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")
    status_script = Path("scripts/external_activation_status.py").read_text(encoding="utf-8")
    pre_release_script = Path("scripts/pre_release_check.py").read_text(encoding="utf-8")
    deploy_playground_script = Path("scripts/deploy_playground_space.py").read_text(encoding="utf-8")

    assert '"-m", "build"' in script
    assert "twine" in script
    assert "--version 0.1.1" in docs
    assert "Trusted Publisher" in docs
    assert "external_activation_status.py" in docs
    assert "pre_release_check.py" in docs
    assert "deploy_playground_space.py" in docs
    assert "Suggested next actions" in docs
    assert "--fail-on-blockers" in docs
    assert "python scripts/external_activation_status.py" in readme
    assert "python scripts/pre_release_check.py --version 0.1.1" in readme
    assert "python scripts/deploy_playground_space.py" in readme
    assert "ENABLE_RELEASE_PLEASE" in status_script
    assert "suggested_actions" in status_script
    assert "ready_for_release_tag" in pre_release_script
    assert "knoema-playground" in deploy_playground_script
