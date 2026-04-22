"""Zenodo deposit helpers for playground research exports."""

from __future__ import annotations

import json
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import requests  # type: ignore[import-untyped]

DepositMode = Literal["local_draft", "remote_draft", "published"]


@dataclass(frozen=True)
class ZenodoDepositResult:
    """Outcome of packaging or uploading a run bundle to Zenodo."""

    mode: DepositMode
    bundle_path: Path
    deposition_id: int | None
    doi: str | None
    html_url: str | None
    api_base: str
    message: str


def parse_creators(creators_text: str) -> list[dict[str, str]]:
    """Parse newline-delimited creators in `Name | Affiliation` format."""

    creators: list[dict[str, str]] = []
    for raw_line in creators_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split("|", maxsplit=1)]
        creator: dict[str, str] = {"name": parts[0]}
        if len(parts) > 1 and parts[1]:
            creator["affiliation"] = parts[1]
        creators.append(creator)
    return creators or [{"name": "Celovin"}]


def parse_keywords(keywords_text: str) -> list[str]:
    """Parse comma-separated keywords."""

    return [item.strip() for item in keywords_text.split(",") if item.strip()]


def build_zenodo_metadata(
    *,
    title: str,
    creators_text: str,
    description: str,
    keywords_text: str,
) -> dict[str, Any]:
    """Build a minimal metadata payload for the Zenodo deposition API."""

    return {
        "metadata": {
            "title": title.strip() or "Luvoire playground run dataset",
            "upload_type": "dataset",
            "description": description.strip() or "Luvoire playground run export.",
            "creators": parse_creators(creators_text),
            "keywords": parse_keywords(keywords_text),
            "prereserve_doi": True,
            "license": "mit",
            "access_right": "open",
        }
    }


def build_arxiv_packet(
    *,
    title: str,
    creators_text: str,
    description: str,
    summary: str,
    keywords_text: str,
) -> dict[str, Any]:
    """Build a lightweight arXiv companion packet for manual submission."""

    creators = parse_creators(creators_text)
    return {
        "schema_version": "luvoire.arxiv.deposit.v1",
        "title": title.strip() or "Luvoire playground run dataset",
        "authors": [creator["name"] for creator in creators],
        "affiliations": [creator.get("affiliation", "") for creator in creators],
        "abstract": description.strip() or "Luvoire playground run export.",
        "categories": ["cs.AI", "cs.MA"],
        "keywords": parse_keywords(keywords_text),
        "comments": "Companion dataset packet generated from the Luvoire playground.",
        "summary": summary.strip(),
    }


def write_deposit_bundle(
    *,
    title: str,
    creators_text: str,
    description: str,
    keywords_text: str,
    summary: str,
    jsonl_text: str,
    preregistration_markdown: str,
) -> Path:
    """Create a bundle that can be uploaded to Zenodo or attached to arXiv."""

    zenodo_metadata = build_zenodo_metadata(
        title=title,
        creators_text=creators_text,
        description=description,
        keywords_text=keywords_text,
    )
    arxiv_packet = build_arxiv_packet(
        title=title,
        creators_text=creators_text,
        description=description,
        summary=summary,
        keywords_text=keywords_text,
    )
    bundle_path = Path(tempfile.gettempdir()) / f"luvoire_zenodo_deposit_{uuid.uuid4().hex}.zip"
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "README.md",
            "\n".join(
                [
                    "# Luvoire deposit bundle",
                    "",
                    "This archive contains the run log, the current pre-registration draft,",
                    "a Zenodo metadata payload, and an arXiv companion packet.",
                ]
            ),
        )
        archive.writestr("data/run.jsonl", jsonl_text)
        archive.writestr("docs/preregistration.md", preregistration_markdown)
        archive.writestr(
            "metadata/zenodo_metadata.json",
            json.dumps(zenodo_metadata, ensure_ascii=False, indent=2),
        )
        archive.writestr(
            "metadata/arxiv_submission.json",
            json.dumps(arxiv_packet, ensure_ascii=False, indent=2),
        )
    return bundle_path


def submit_zenodo_bundle(
    *,
    title: str,
    creators_text: str,
    description: str,
    keywords_text: str,
    summary: str,
    jsonl_text: str,
    preregistration_markdown: str,
    access_token: str,
    sandbox: bool = True,
    publish: bool = False,
    session: requests.Session | None = None,
) -> ZenodoDepositResult:
    """Create a bundle and optionally upload it to Zenodo."""

    bundle_path = write_deposit_bundle(
        title=title,
        creators_text=creators_text,
        description=description,
        keywords_text=keywords_text,
        summary=summary,
        jsonl_text=jsonl_text,
        preregistration_markdown=preregistration_markdown,
    )
    api_base = "https://sandbox.zenodo.org" if sandbox else "https://zenodo.org"
    token = access_token.strip()
    if not token:
        return ZenodoDepositResult(
            mode="local_draft",
            bundle_path=bundle_path,
            deposition_id=None,
            doi=None,
            html_url=None,
            api_base=api_base,
            message="Bundle created locally. Provide a Zenodo access token to create a remote draft.",
        )

    http = session or requests.Session()
    auth_headers = {"Authorization": f"Bearer {token}"}
    json_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    create_response = http.post(
        f"{api_base}/api/deposit/depositions",
        json={},
        headers=json_headers,
        timeout=60,
    )
    create_response.raise_for_status()
    create_payload = create_response.json()
    deposition_id = int(create_payload["id"])

    metadata_response = http.put(
        f"{api_base}/api/deposit/depositions/{deposition_id}",
        json=build_zenodo_metadata(
            title=title,
            creators_text=creators_text,
            description=description,
            keywords_text=keywords_text,
        ),
        headers=json_headers,
        timeout=60,
    )
    metadata_response.raise_for_status()
    metadata_payload = metadata_response.json()

    with bundle_path.open("rb") as handle:
        upload_response = http.post(
            f"{api_base}/api/deposit/depositions/{deposition_id}/files",
            headers=auth_headers,
            data={"name": bundle_path.name},
            files={"file": (bundle_path.name, handle, "application/zip")},
            timeout=300,
        )
    upload_response.raise_for_status()

    published_payload = metadata_payload
    mode: DepositMode = "remote_draft"
    if publish:
        publish_response = http.post(
            f"{api_base}/api/deposit/depositions/{deposition_id}/actions/publish",
            headers=auth_headers,
            timeout=60,
        )
        publish_response.raise_for_status()
        published_payload = publish_response.json()
        mode = "published"

    doi_block = published_payload.get("metadata", {}).get("prereserve_doi", {})
    doi = str(doi_block.get("doi") or published_payload.get("doi") or "").strip() or None
    links = published_payload.get("links", {})
    html_url = str(links.get("html") or links.get("latest_draft_html") or "").strip() or None
    return ZenodoDepositResult(
        mode=mode,
        bundle_path=bundle_path,
        deposition_id=deposition_id,
        doi=doi,
        html_url=html_url,
        api_base=api_base,
        message="Zenodo deposition created successfully.",
    )
