# VS Code Extension

Phase 56 adds `extensions/vscode`, a local VS Code extension for Scenario DSL authoring.

## Commands

```powershell
npm --prefix extensions\vscode run compile
npx @vscode/vsce package --no-dependencies --packagePath extensions\vscode\luvoire-scenario-tools-0.3.0.vsix extensions\vscode
```

The extension contributes syntax highlighting, JSON Schema validation, three command-palette actions, and a lightweight timeline preview webview.
