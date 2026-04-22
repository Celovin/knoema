from __future__ import annotations

from pathlib import Path

from luvoire.cli import main
from luvoire.telemetry import (
    NullTelemetryClient,
    TelemetryClient,
    TelemetrySettings,
    build_env_telemetry_client,
)


class RecordingTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object], float]] = []

    def post(self, endpoint: str, payload: dict[str, object], *, timeout_seconds: float) -> None:
        self.calls.append((endpoint, payload, timeout_seconds))


def _write_run_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "runtime:",
                "  duration_days: 1",
                "  tick_duration_minutes: 720",
                "  output_path: cli_logs.jsonl",
                "  prompt_language: en",
                "environment:",
                '  start_time: "2026-03-02T09:00:00"',
                "  location_path: [Korea, Seoul, Dormitory]",
                "agents:",
                "  - agent_id: alice",
                "    name: Alice",
                "    age: 17",
                "    background: Dormitory student.",
                "    personality:",
                "      openness: 0.8",
                "      conscientiousness: 0.6",
                "      extraversion: 0.2",
                "      agreeableness: 0.7",
                "      neuroticism: 0.4",
                "local_response: '{\"action_type\": \"observe\", \"target\": null, \"content\": \"keeps the prompt private.\"}'",
            ]
        ),
        encoding="utf-8",
    )


def test_phase39_telemetry_is_off_by_default(tmp_path: Path) -> None:
    id_path = tmp_path / "telemetry_id"

    client = build_env_telemetry_client(env={}, id_path=id_path)

    assert isinstance(client, NullTelemetryClient)
    assert not id_path.exists()


def test_phase39_env_opt_in_creates_anonymous_uuid_only(tmp_path: Path) -> None:
    id_path = tmp_path / "telemetry_id"
    transport = RecordingTransport()

    client = build_env_telemetry_client(
        env={
            "LUVOIRE_TELEMETRY": "1",
            "LUVOIRE_TELEMETRY_ENDPOINT": "https://telemetry.invalid/capture",
        },
        transport=transport,
        id_path=id_path,
    )

    assert isinstance(client, TelemetryClient)
    assert id_path.exists()
    assert client.capture("cli_run_requested", properties={"surface": "cli"}) is True
    assert len(transport.calls) == 1
    assert transport.calls[0][1]["distinct_id"] == id_path.read_text(encoding="utf-8").strip()


def test_phase39_cli_opt_in_flag_emits_three_safe_events(
    tmp_path: Path,
    capsys,  # type: ignore[no-untyped-def]
) -> None:
    config_path = tmp_path / "run.yaml"
    _write_run_config(config_path)
    transport = RecordingTransport()
    telemetry_client = TelemetryClient(
        TelemetrySettings(
            enabled=True,
            endpoint="https://telemetry.invalid/capture",
            distinct_id="anonymous-test-id",
        ),
        transport=transport,
    )

    exit_code = main(
        ["run", str(config_path), "--json", "--telemetry"],
        telemetry_client=telemetry_client,
    )

    assert exit_code == 0
    assert [call[1]["event"] for call in transport.calls] == [
        "cli_run_requested",
        "cli_run_completed",
        "cli_summary_emitted",
    ]
    for _, payload, _ in transport.calls:
        properties = payload["properties"]
        assert isinstance(properties, dict)
        assert payload["distinct_id"] == "anonymous-test-id"
        assert "local_response" not in properties
        assert "config_path" not in properties
        assert "output_path" not in properties
    assert "keeps the prompt private" not in capsys.readouterr().out


def test_phase39_privacy_doc_describes_opt_in_contract() -> None:
    privacy = Path("docs/PRIVACY.md").read_text(encoding="utf-8")

    assert "Telemetry is off by default." in privacy
    assert "LUVOIRE_TELEMETRY=1" in privacy
    assert "anonymous UUID" in privacy
    assert "Prompt content" in privacy
