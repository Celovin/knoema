from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_phase59_cloud_template_files_exist() -> None:
    expected = [
        "deploy/cloud/README.md",
        "deploy/cloud/validate_templates.py",
        "deploy/cloud/aws/README.md",
        "deploy/cloud/aws/terraform/main.tf",
        "deploy/cloud/aws/cloudformation/knoema-stack.yaml",
        "deploy/cloud/gcp/README.md",
        "deploy/cloud/gcp/terraform/main.tf",
        "deploy/cloud/azure/README.md",
        "deploy/cloud/azure/bicep/main.bicep",
        "docs/deployment/cloud-comparison.md",
    ]

    for path in expected:
        assert Path(path).exists()


def test_phase59_static_validator_passes_for_required_resources() -> None:
    result = subprocess.run(
        [sys.executable, "deploy/cloud/validate_templates.py"],
        check=True,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["ok"] is True
    assert len(payload["checked"]) == 4
    assert payload["missing"] == {}


def test_phase59_aws_templates_cover_runtime_database_cache_and_load_balancer() -> None:
    terraform = Path("deploy/cloud/aws/terraform/main.tf").read_text(encoding="utf-8")
    cloudformation = Path("deploy/cloud/aws/cloudformation/knoema-stack.yaml").read_text(
        encoding="utf-8"
    )

    for token in ["aws_ecs_service", "aws_lb", "aws_db_instance", "aws_elasticache_cluster"]:
        assert token in terraform
    for token in [
        "AWS::ECS::Service",
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "AWS::RDS::DBInstance",
        "AWS::ElastiCache::CacheCluster",
    ]:
        assert token in cloudformation


def test_phase59_gcp_and_azure_templates_cover_required_services() -> None:
    gcp = Path("deploy/cloud/gcp/terraform/main.tf").read_text(encoding="utf-8")
    azure = Path("deploy/cloud/azure/bicep/main.bicep").read_text(encoding="utf-8")

    assert "google_cloud_run_v2_service" in gcp
    assert "google_sql_database_instance" in gcp
    assert "google_redis_instance" in gcp
    assert "Microsoft.App/containerApps" in azure
    assert "Microsoft.DBforPostgreSQL/flexibleServers" in azure


def test_phase59_cost_docs_and_navigation_are_linked() -> None:
    docs = Path("docs/deployment/cloud-comparison.md").read_text(encoding="utf-8")
    root_readme = Path("deploy/cloud/README.md").read_text(encoding="utf-8")

    for request_band in ["10k", "100k", "1M"]:
        assert request_band in docs
        assert request_band in root_readme

    assert "Cloud Deployment Comparison: deployment/cloud-comparison.md" in Path(
        "mkdocs.yml"
    ).read_text(encoding="utf-8")
    assert "Phase 59 cloud deployment templates" in Path("CHANGELOG.md").read_text(
        encoding="utf-8"
    )
