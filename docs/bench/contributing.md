# Contributing to Luvoire Bench

External framework contributors can add a row by submitting a YAML file under
`bench/submissions/`.

## Steps

1. Copy `bench/submissions/TEMPLATE.yaml`.
2. Rename it to `bench/submissions/<framework>-<version>.yaml`.
3. Fill all seven axes with measured scores, targets, source paths, and caveats.
4. Run:

```bash
python scripts/validate_submission.py bench/submissions/<framework>-<version>.yaml
python scripts/build_leaderboard.py
```

5. Commit the submission and regenerated `docs/bench/leaderboard.md`.

## Review Expectations

- Source links must be public or included in the pull request.
- Caveats must disclose synthetic, deterministic, and published-envelope status.
- Do not add unmeasured external baseline numbers.
- If a framework cannot run an axis, say that directly in the caveat.
