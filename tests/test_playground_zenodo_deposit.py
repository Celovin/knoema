from __future__ import annotations

import importlib
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd()))

playground_app = importlib.import_module("playground.app")
deposit_module = importlib.import_module("luvoire.research.deposit")


def _walk_components(component: object) -> list[object]:
    components = [component]
    for child in getattr(component, "children", []) or []:
        components.extend(_walk_components(child))
    return components


def test_subtask51_build_app_exposes_deposit_controls() -> None:
    app = playground_app.build_app()
    components = _walk_components(app)

    panel = next(
        component
        for component in components
        if type(component).__name__ == "Accordion"
        and getattr(component, "elem_id", None) == "deposit-panel"
    )
    button = next(
        component
        for component in components
        if type(component).__name__ == "Button"
        and getattr(component, "elem_id", None) == "deposit-button"
    )

    assert panel.label == playground_app.LABELS["ko"]["deposit_panel"]
    assert button.value == playground_app.LABELS["ko"]["deposit_button"]


def test_subtask51_export_deposit_bundle_writes_local_packet_without_token() -> None:
    status, bundle_path = playground_app._export_deposit_bundle(
        "Mode: Replay only | Agents: 2",
        '{"tick": 1, "agent_id": "agent_1"}\n',
        "## OSF-format pre-registration\n\nSample",
        "English",
        "Dormitory cooperation study",
        "Celovin",
        "Dataset export for a replay run.",
        "luvoire, simulation",
        "",
        True,
        False,
    )

    path = Path(bundle_path)
    try:
        assert path.suffix == ".zip"
        assert "local_draft" in status
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            assert "README.md" in names
            assert "data/run.jsonl" in names
            assert "docs/preregistration.md" in names
            assert "metadata/zenodo_metadata.json" in names
            assert "metadata/arxiv_submission.json" in names
    finally:
        path.unlink(missing_ok=True)


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self._payload


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append(("POST", url))
        if url.endswith("/api/deposit/depositions"):
            return _FakeResponse(
                {
                    "id": 542201,
                    "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.542201"}},
                    "links": {"html": "https://sandbox.zenodo.org/deposit/542201"},
                }
            )
        if url.endswith("/files"):
            assert kwargs["files"] is not None
            return _FakeResponse({"id": "file-1"})
        if url.endswith("/actions/publish"):
            return _FakeResponse(
                {
                    "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.542201"}},
                    "links": {"html": "https://sandbox.zenodo.org/records/542201"},
                }
            )
        raise AssertionError(f"unexpected POST {url}")

    def put(self, url: str, **kwargs: object) -> _FakeResponse:
        self.calls.append(("PUT", url))
        return _FakeResponse(
            {
                "metadata": {"prereserve_doi": {"doi": "10.5072/zenodo.542201"}},
                "links": {"html": "https://sandbox.zenodo.org/deposit/542201"},
            }
        )


def test_subtask51_submit_zenodo_bundle_uses_deposition_api_flow() -> None:
    session = _FakeSession()

    result = deposit_module.submit_zenodo_bundle(
        title="Dormitory cooperation study",
        creators_text="Celovin",
        description="Dataset export for a replay run.",
        keywords_text="luvoire, simulation",
        summary="Mode: Replay only | Agents: 2",
        jsonl_text='{"tick": 1, "agent_id": "agent_1"}\n',
        preregistration_markdown="## OSF-format pre-registration\n\nSample",
        access_token="secret-token",
        sandbox=True,
        publish=False,
        session=session,
    )

    try:
        assert result.mode == "remote_draft"
        assert result.deposition_id == 542201
        assert result.doi == "10.5072/zenodo.542201"
        assert result.html_url == "https://sandbox.zenodo.org/deposit/542201"
        assert ("POST", "https://sandbox.zenodo.org/api/deposit/depositions") in session.calls
        assert ("PUT", "https://sandbox.zenodo.org/api/deposit/depositions/542201") in session.calls
        assert ("POST", "https://sandbox.zenodo.org/api/deposit/depositions/542201/files") in session.calls
    finally:
        result.bundle_path.unlink(missing_ok=True)
