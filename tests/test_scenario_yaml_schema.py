from __future__ import annotations

from knoema.community import seed_community_scenarios
from knoema.dsl import collect_validation_issues, loads_scenario


def test_batch_r_seed_community_scenarios_are_valid_dsl() -> None:
    for seed in seed_community_scenarios():
        scenario = loads_scenario(seed.yaml_text)
        assert scenario.scenario_id == seed.scenario_id
        assert collect_validation_issues(scenario) == []


def test_batch_r_gallery_docs_and_templates_exist() -> None:
    from pathlib import Path

    docs = Path("docs/community/scenario-gallery.md").read_text(encoding="utf-8")
    issue_template = Path(
        "docs/community/gallery_templates/issue_template_new_scenario.yaml"
    ).read_text(encoding="utf-8")
    workflow = Path("docs/community/gallery_templates/community_scenario_lint.yml").read_text(
        encoding="utf-8"
    )

    assert "manifest.json" in docs
    assert "knoema-scenarios" in docs
    assert "Scenario ID" in issue_template
    assert "knoema validate scenarios --json" in workflow
