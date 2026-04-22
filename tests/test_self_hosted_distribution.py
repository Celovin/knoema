from __future__ import annotations

from pathlib import Path

import yaml


def test_dockerfile_runs_playground_cli() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.12-slim" in dockerfile
    assert 'org.opencontainers.image.title="Luvoire Playground"' in dockerfile
    assert 'org.opencontainers.image.source="https://github.com/Celovin/luvoire"' in dockerfile
    assert "COPY playground ./playground" in dockerfile
    assert "EXPOSE 7860" in dockerfile
    assert 'CMD ["luvoire", "playground", "--host", "0.0.0.0", "--port", "7860"]' in dockerfile


def test_docker_compose_exposes_persistent_playground() -> None:
    compose = yaml.safe_load(Path("docker-compose.yml").read_text(encoding="utf-8"))
    service = compose["services"]["playground"]

    assert service["build"]["dockerfile"] == "Dockerfile"
    assert service["ports"] == ["7860:7860"]
    assert "./runs:/app/runs" in service["volumes"]
    assert service["environment"]["GRADIO_ANALYTICS_ENABLED"] == "False"


def test_deploy_docker_compose_uses_luvoire_api_service() -> None:
    compose = yaml.safe_load(Path("deploy/docker/docker-compose.yml").read_text(encoding="utf-8"))
    dockerfile = Path("deploy/docker/Dockerfile.api").read_text(encoding="utf-8")

    assert "luvoire-api" in compose["services"]
    assert "engine-api" not in compose["services"]
    assert 'org.opencontainers.image.title="Luvoire API"' in dockerfile
    assert 'org.opencontainers.image.source="https://github.com/Celovin/luvoire"' in dockerfile


def test_self_hosted_docs_are_in_nav() -> None:
    docs = Path("docs/deploy/self-hosted.md").read_text(encoding="utf-8")
    mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")

    assert "luvoire run" in docs
    assert "luvoire list-scenarios" in docs
    assert "luvoire verify" in docs
    assert "docker compose up --build" in docs
    assert "deploy/self-hosted.md" in mkdocs
