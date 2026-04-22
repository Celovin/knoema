# Luvoire Scenario Tools

VS Code authoring support for Luvoire Scenario DSL files.

## Features

- Syntax highlighting for `.luvoire.yaml` and `.luvoire.yml`.
- JSON Schema validation and autocomplete for Scenario DSL root fields.
- Commands:
  - `Luvoire: Validate Scenario`
  - `Luvoire: Run Scenario`
  - `Luvoire: Preview Timeline`

## Build

```powershell
cd C:\Users\admin\Projects\luvoire
npm --prefix extensions\vscode run compile
npx @vscode/vsce package --no-dependencies --packagePath extensions\vscode\luvoire-scenario-tools-0.3.0.vsix extensions\vscode
```

Marketplace publication requires a VS Code publisher account and is tracked as an external blocker.
