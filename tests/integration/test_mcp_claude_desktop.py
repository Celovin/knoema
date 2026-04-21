from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _send(process: subprocess.Popen[str], payload: dict[str, Any]) -> dict[str, Any]:
    assert process.stdin is not None
    assert process.stdout is not None
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()
    line = process.stdout.readline()
    assert line
    response = json.loads(line)
    assert response["jsonrpc"] == "2.0"
    return response


def test_batch_o_stdio_server_handles_claude_desktop_mcp_lifecycle() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    env["KNOEMA_SCENARIO_DIR"] = str(Path("playground/scenarios").resolve())
    process = subprocess.Popen(
        [sys.executable, "scripts/knoema_mcp_serve.py", "--stdio"],
        cwd=Path.cwd(),
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        initialize = _send(
            process,
            {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "claude-desktop", "version": "test"},
                },
            },
        )
        assert initialize["result"]["serverInfo"]["name"] == "knoema-engine"

        tools = _send(process, {"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        names = {tool["name"] for tool in tools["result"]["tools"]}
        assert "run_scenario" in names

        scenarios = _send(
            process,
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "list_scenarios", "arguments": {}},
            },
        )
        assert scenarios["result"]["structuredContent"]["count"] == 30
    finally:
        process.terminate()
        process.wait(timeout=10)
