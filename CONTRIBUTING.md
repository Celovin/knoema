# Contributing to Knoema Engine

Thanks for your interest in Knoema! This is an early-stage project under active R&D; contributions of all sizes are welcome — bug reports, docs fixes, example notebooks, and feature PRs.

## Development Setup

```bash
git clone https://github.com/Celovin/knoema.git
cd knoema
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## Running Tests

```bash
pytest                 # unit tests
ruff check .           # lint
mypy src               # type check
```

## Branch & Commit Conventions

- `main` is protected; all work lands via PRs.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for messages:
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation only
  - `test:` tests only
  - `refactor:` code change that neither adds a feature nor fixes a bug
  - `chore:` housekeeping

## Code Style

- Python 3.11+, strict type hints (see `tool.mypy` in `pyproject.toml`).
- `ruff` for lint & formatting.
- Keep functions small; prefer pure functions over mutation.
- No comments explaining *what* the code does — prefer expressive names. Comments are for *why* only.

## Licensing

By contributing you agree that your contributions will be licensed under the [MIT License](LICENSE).

## Questions

Open a discussion or reach out: hello@celovin.com
