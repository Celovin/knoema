"""Phase 49 tests for the web Scenario DSL editor."""

from __future__ import annotations

import json
from pathlib import Path

from knoema.dsl import collect_validation_issues, load_scenario


def test_phase49_editor_files_exist() -> None:
    expected = [
        "website/app/editor/page.tsx",
        "website/app/editor/EditorClient.tsx",
        "website/app/editor/editor.module.css",
        "website/app/editor/sample_export.yaml",
        "website/e2e/editor.spec.ts",
        "website/playwright.config.ts",
        "docs/website/scenario-editor.md",
    ]

    missing = [path for path in expected if not Path(path).exists()]
    assert missing == []


def test_phase49_editor_implements_required_surfaces() -> None:
    source = Path("website/app/editor/EditorClient.tsx").read_text(encoding="utf-8")

    for token in [
        "AgentPalette",
        "SceneCanvas",
        "EventTimeline",
        "PropertyInspector",
        "YamlPreview",
        "createContext",
        "onDrop",
        "download=\"knoema_scenario.yaml\"",
    ]:
        assert token in source


def test_phase49_sample_export_is_valid_scenario_dsl() -> None:
    scenario = load_scenario("website/app/editor/sample_export.yaml")

    assert scenario.scenario_id == "editor_school_lab"
    assert len(scenario.agents) == 2
    assert collect_validation_issues(scenario) == []


def test_phase49_playwright_e2e_and_package_scripts_are_declared() -> None:
    package = json.loads(Path("website/package.json").read_text(encoding="utf-8"))
    e2e = Path("website/e2e/editor.spec.ts").read_text(encoding="utf-8")
    docs = Path("docs/website/scenario-editor.md").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert package["scripts"]["e2e"] == "playwright test"
    assert "@playwright/test" in package["devDependencies"]
    assert e2e.count("test(") >= 3
    assert "dragTo" in e2e
    assert "npm run e2e" in docs
    assert "website/scenario-editor.md" in mkdocs
