# Knoema Scenario Tools

VS Code authoring support for Knoema Scenario DSL files.

## Features

- Syntax highlighting for `.knoema.yaml` and `.knoema.yml`.
- JSON Schema validation and autocomplete for Scenario DSL root fields.
- Commands:
  - `Knoema: Validate Scenario`
  - `Knoema: Run Scenario`
  - `Knoema: Preview Timeline`

## Build

```powershell
cd C:\Users\admin\Projects\knoema
npm --prefix extensions\vscode run compile
npx @vscode/vsce package --no-dependencies --packagePath extensions\vscode\knoema-scenario-tools-0.2.0.vsix extensions\vscode
```

Marketplace publication requires a VS Code publisher account and is tracked as an external blocker.
