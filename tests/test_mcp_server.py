from __future__ import annotations

import json
import warnings
from pathlib import Path

import luvoire.config as config
import luvoire_mcp.server as mcp_server
from luvoire_mcp.server import LuvoireMcpService, handle_jsonrpc_line


def test_batch_o_mcp_lists_five_luvoire_tools() -> None:
    service = LuvoireMcpService()
    payload = service.list_tools()
    tool_names = {tool["name"] for tool in payload["tools"]}

    assert tool_names == {
        "list_scenarios",
        "run_scenario",
        "inspect_trait_vector",
        "generate_report",
        "suggest_scenario",
    }
    for tool in payload["tools"]:
        assert tool["inputSchema"]["type"] == "object"


def test_batch_o_mcp_tools_run_replay_and_report() -> None:
    service = LuvoireMcpService()

    scenarios = service.list_scenarios()
    assert scenarios["count"] == 30
    assert scenarios["scenarios"][0]["name"] == "Dorm: two agents"
    assert scenarios["scenarios"][0]["agent_count"] == 2

    run = service.run_scenario(name="Dorm: two agents", provider="replay", ticks=2)
    assert run["scenario"] == "Dorm: two agents"
    assert run["ticks"] == 2
    assert run["agent_count"] == 2
    assert run["log_count"] == 4

    traits = service.inspect_trait_vector(agent_id="mina", run_id=str(run["run_id"]))
    assert traits["name"] == "Mina"
    assert traits["traits"]["openness"] == 0.74

    report = service.generate_report(run_id=str(run["run_id"]))
    assert "# Luvoire MCP Run Report: Dorm: two agents" in report["markdown"]
    assert "Actions: 4" in report["markdown"]


def test_batch_o_mcp_suggests_scenarios_from_description() -> None:
    service = LuvoireMcpService()
    payload = service.suggest_scenario(description="students coordinate chores in a dorm kitchen")

    assert payload["suggestions"][0]["name"] == "Dorm: two agents"
    assert payload["suggestions"][0]["score"] > 0


def test_batch_o_jsonrpc_initialize_and_tool_call_schema() -> None:
    service = LuvoireMcpService()
    initialize = handle_jsonrpc_line(
        service,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
            }
        ),
    )
    assert initialize is not None
    assert initialize["result"]["protocolVersion"] == "2025-06-18"
    assert initialize["result"]["capabilities"]["tools"]["listChanged"] is False

    tool_call = handle_jsonrpc_line(
        service,
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "list_scenarios", "arguments": {}},
            }
        ),
    )
    assert tool_call is not None
    assert tool_call["result"]["structuredContent"]["count"] == 30
    assert tool_call["result"]["content"][0]["type"] == "text"


def test_batch_o_mcp_scenario_dir_prefers_luvoire_env(monkeypatch) -> None:
    monkeypatch.setenv("LUVOIRE_SCENARIO_DIR", "playground/scenarios")
    monkeypatch.setenv("KNOEMA_SCENARIO_DIR", "legacy/scenarios")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = mcp_server._env_scenario_dir()

    assert value == Path("playground/scenarios")
    assert caught == []


def test_batch_o_mcp_scenario_dir_accepts_legacy_env(monkeypatch) -> None:
    config._WARNED_LEGACY_ENV_VARS.clear()
    monkeypatch.delenv("LUVOIRE_SCENARIO_DIR", raising=False)
    monkeypatch.setenv("KNOEMA_SCENARIO_DIR", "legacy/scenarios")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = mcp_server._env_scenario_dir()

    assert value == Path("legacy/scenarios")
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert "KNOEMA_SCENARIO_DIR is deprecated" in str(caught[0].message)
