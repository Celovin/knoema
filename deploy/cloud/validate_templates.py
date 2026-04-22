from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EXPECTED = {
    "aws/terraform/main.tf": [
        "aws_vpc",
        "aws_ecs_cluster",
        "aws_ecs_service",
        "aws_lb",
        "aws_db_instance",
        "aws_elasticache_cluster",
    ],
    "aws/cloudformation/luvoire-stack.yaml": [
        "AWS::ECS::Cluster",
        "AWS::ECS::Service",
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "AWS::RDS::DBInstance",
        "AWS::ElastiCache::CacheCluster",
    ],
    "gcp/terraform/main.tf": [
        "google_cloud_run_v2_service",
        "google_sql_database_instance",
        "google_redis_instance",
    ],
    "azure/bicep/main.bicep": [
        "Microsoft.App/containerApps",
        "Microsoft.DBforPostgreSQL/flexibleServers",
        "Microsoft.App/managedEnvironments",
    ],
}


def validate() -> dict[str, object]:
    checked: list[str] = []
    missing: dict[str, list[str]] = {}
    for relative_path, tokens in EXPECTED.items():
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        checked.append(relative_path)
        absent = [token for token in tokens if token not in text]
        if absent:
            missing[relative_path] = absent

    return {
        "checked": checked,
        "ok": not missing,
        "missing": missing,
    }


def main() -> None:
    result = validate()
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
