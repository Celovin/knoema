# Scenario Marketplace Beta

Luvoire's scenario marketplace beta is a repository-backed hub for sharing reproducible, validated YAML scenarios.

## Submission Flow

1. Open a GitHub Discussion to describe the scenario goal, audience, and category fit.
2. Copy `scenarios_hub/submissions/_template.yaml` and fill in a complete Scenario DSL file.
3. Run `python scripts/validate_scenarios.py` from the repository root.
4. Open a pull request with the `scenario_submission.md` PR template.

## Directory Layout

- `scenarios_hub/submissions/`: incoming community drafts.
- `scenarios_hub/curated/education/`: classroom, campus, and workshop scenarios.
- `scenarios_hub/curated/social/`: neighborhood, mobility, and group coordination scenarios.
- `scenarios_hub/curated/game_demo/`: fictional game-ready NPC and quest interaction seeds.
- `scenarios_hub/curated/research/`: synthetic public-safety and academic replay scenarios.

## Contribution Rules

- `scenario_id` must match the YAML filename.
- Every scenario must remain fictional and use synthetic agents only.
- Sensitive scenarios must explain the review boundary in `ethics.irb_notes`.
- Keep descriptions focused on simulation design, replay analysis, or game interaction. Do not submit real-person profiling, future harm prediction, or suspect ranking scenarios.

## Local Validation

```powershell
cd C:\Users\admin\Projects\luvoire
.venv\Scripts\python scripts\validate_scenarios.py
```

The validator loads each YAML file, applies the Scenario DSL ethics rules, and runs a small simulator smoke test.
