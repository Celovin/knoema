function activate(context) {
  const vscode = require("vscode");
  context.subscriptions.push(
    vscode.commands.registerCommand("luvoire.validateScenario", () => {
      const editor = vscode.window.activeTextEditor;
      const text = editor ? editor.document.getText() : "";
      const result = validateScenarioText(text);
      const message = result.valid
        ? `Luvoire scenario looks valid (${result.checks.length} checks).`
        : `Luvoire scenario has ${result.issues.length} issue(s): ${result.issues.join("; ")}`;
      vscode.window.showInformationMessage(message);
    }),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("luvoire.runScenario", () => {
      vscode.window.showInformationMessage(
        "Run `luvoire run <scenario.yaml>` in a terminal to execute this scenario.",
      );
    }),
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("luvoire.previewTimeline", () => {
      const panel = vscode.window.createWebviewPanel(
        "luvoireTimeline",
        "Luvoire Timeline Preview",
        vscode.ViewColumn.Beside,
        {},
      );
      const editor = vscode.window.activeTextEditor;
      panel.webview.html = renderTimelinePreview(editor ? editor.document.getText() : "");
    }),
  );
}

function deactivate() {}

function validateScenarioText(text) {
  const required = [
    "schema_version:",
    "scenario_id:",
    "title:",
    "domain:",
    "environment:",
    "agents:",
    "ethics:",
  ];
  const checks = [];
  const issues = [];
  for (const token of required) {
    if (text.includes(token)) {
      checks.push(token.replace(":", ""));
    } else {
      issues.push(`missing ${token}`);
    }
  }
  for (const phrase of ["predict crime", "rank suspects", "identify suspect"]) {
    if (text.toLowerCase().includes(phrase)) {
      issues.push(`disallowed purpose: ${phrase}`);
    }
  }
  return { valid: issues.length === 0, checks, issues };
}

function renderTimelinePreview(text) {
  const eventLines = text
    .split(/\r?\n/)
    .filter((line) => line.trim().startsWith("description:"))
    .map((line) => line.replace("description:", "").trim());
  const items = eventLines.length ? eventLines : ["No events detected."];
  return `<!doctype html>
<html>
  <body>
    <h1>Luvoire Timeline Preview</h1>
    <ol>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol>
  </body>
</html>`;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

module.exports = {
  activate,
  deactivate,
  escapeHtml,
  renderTimelinePreview,
  validateScenarioText,
};
