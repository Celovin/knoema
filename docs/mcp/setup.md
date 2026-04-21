# MCP Setup

Knoema exposes a stdio Model Context Protocol server for local desktop clients.
The server provides deterministic replay tools only by default, so desktop LLMs
can inspect scenarios without receiving API keys.

## Install

```powershell
pip install "knoema-engine[mcp]"
```

From a source checkout:

```powershell
cd C:\Users\admin\Projects\knoema
$env:PYTHONPATH="src"
.\.venv\Scripts\python.exe scripts\knoema_mcp_serve.py --stdio
```

If the package is installed outside the repository, point the server at the
scenario directory:

```powershell
$env:KNOEMA_SCENARIO_DIR="C:\Users\admin\Projects\knoema\playground\scenarios"
```

## Claude Desktop

Add this entry to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "knoema": {
      "command": "python",
      "args": [
        "C:\\Users\\admin\\Projects\\knoema\\scripts\\knoema_mcp_serve.py",
        "--stdio"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\admin\\Projects\\knoema\\src",
        "KNOEMA_SCENARIO_DIR": "C:\\Users\\admin\\Projects\\knoema\\playground\\scenarios"
      }
    }
  }
}
```

## Claude Code

```powershell
claude mcp add knoema -- python C:\Users\admin\Projects\knoema\scripts\knoema_mcp_serve.py --stdio
```

Set `PYTHONPATH=C:\Users\admin\Projects\knoema\src` and
`KNOEMA_SCENARIO_DIR=C:\Users\admin\Projects\knoema\playground\scenarios` in
the shell that launches Claude Code.

## Cursor and Cline

Use the same command and environment values as Claude Desktop:

```text
python C:\Users\admin\Projects\knoema\scripts\knoema_mcp_serve.py --stdio
```

## Tools

- `list_scenarios`: returns the 30 built-in scenarios with file names and agent counts.
- `run_scenario`: runs deterministic replay for 1-12 ticks and returns JSON logs.
- `inspect_trait_vector`: returns the 30-trait vector for an agent.
- `generate_report`: returns a Markdown run report for a previous MCP run.
- `suggest_scenario`: matches a natural-language description to curated scenarios.

Live OpenAI and Anthropic execution is intentionally not enabled through MCP by
default. Use the Playground for live model runs where API keys stay in the
browser request path.
