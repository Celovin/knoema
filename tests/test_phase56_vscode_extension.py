from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

EXT_ROOT = Path("extensions/vscode")
NPM = "npm.cmd" if os.name == "nt" else "npm"


def test_phase56_vscode_extension_files_exist() -> None:
    expected = [
        "package.json",
        "compiled/extension.js",
        "syntaxes/knoema-scenario.tmLanguage.json",
        "schemas/scenario.schema.json",
        "examples/dorm.knoema.yaml",
        "examples/research.knoema.yaml",
        "examples/community.knoema.yaml",
        "media/screenshot-placeholder.svg",
        "knoema-scenario-tools-0.2.0.vsix",
    ]

    for relative_path in expected:
        assert (EXT_ROOT / relative_path).exists()


def test_phase56_vscode_manifest_declares_commands_language_and_schema() -> None:
    package = json.loads((EXT_ROOT / "package.json").read_text(encoding="utf-8"))
    commands = {
        command["command"]
        for command in package["contributes"]["commands"]
    }

    assert {
        "knoema.validateScenario",
        "knoema.runScenario",
        "knoema.previewTimeline",
    } <= commands
    assert package["contributes"]["languages"][0]["id"] == "knoema-scenario"
    assert package["contributes"]["jsonValidation"][0]["url"] == "./schemas/scenario.schema.json"


def test_phase56_vscode_compile_script_and_validator_helper_work() -> None:
    subprocess.run(
        [NPM, "--prefix", "extensions/vscode", "run", "compile"],
        check=True,
        cwd=Path.cwd(),
    )
    result = subprocess.run(
        [
            "node",
            "-e",
            (
                "const ext=require('./extensions/vscode/compiled/extension.js');"
                "const ok=ext.validateScenarioText("
                "'schema_version:\\nscenario_id:\\ntitle:\\ndomain:\\nenvironment:\\nagents:\\nethics:'"
                ");"
                "const bad=ext.validateScenarioText('predict crime');"
                "if(!ok.valid || bad.valid) process.exit(1);"
            ),
        ],
        check=True,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_phase56_vscode_schema_covers_required_scenario_roots() -> None:
    schema = json.loads((EXT_ROOT / "schemas/scenario.schema.json").read_text(encoding="utf-8"))

    assert "ethics" in schema["required"]
    assert schema["properties"]["domain"]["enum"] == [
        "game",
        "public_safety_research",
        "academic_research",
    ]


def test_phase56_docs_are_linked() -> None:
    assert "VS Code Extension: extensions/vscode.md" in Path("mkdocs.yml").read_text(
        encoding="utf-8"
    )
    assert "VS Code Scenario DSL extension" in Path("CHANGELOG.md").read_text(encoding="utf-8")
