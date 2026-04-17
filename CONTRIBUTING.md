# Contributing to Knoema Engine

Thanks for your interest in Knoema. This is an early-stage project under active R&D. Contributions of all sizes are welcome: bug reports, docs fixes, example notebooks, and feature PRs.

## Development Setup

```bash
git clone https://github.com/Celovin/knoema.git
cd knoema
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

Dashboard work also needs:

```bash
pip install -e ".[dashboard]"
```

## Running Tests

```bash
pytest
ruff check .
mypy src
```

## Branch and Commit Conventions

- `main` is protected; work should land through pull requests once the repository is public.
- Use Conventional Commits:
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation only
  - `test:` tests only
  - `refactor:` code change that neither adds a feature nor fixes a bug
  - `chore:` housekeeping

## Code Style

- Python 3.11+.
- Strict type hints for source modules under `src/`.
- `ruff` for linting.
- Prefer small pure functions where practical.
- Add comments only when they explain why a non-obvious decision exists.

## Safety Boundary

Public-safety examples must stay fictional, synthetic, and non-identifying. Do not submit real incident data, victim names, suspect names, operational records, or predictive claims.

## Licensing

By contributing you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions

Open a discussion or reach out: hello@celovin.com
