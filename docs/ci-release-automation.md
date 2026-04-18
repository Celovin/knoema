# CI and Release Automation

Knoema uses a fast default CI path and a broader compatibility workflow.

## Default CI

The `CI` workflow runs on every push to `main` and every pull request.

- Ubuntu + Python 3.12 quality gate.
- pip cache through `actions/setup-python`.
- pre-commit hook cache warmed through `PRE_COMMIT_HOME`.
- pytest cache restored between runs.
- hard gates: Ruff, mypy, pytest with 90% coverage, and the `v0.1.1` release dry run.

The previous default CI duplicated the full coverage suite on Python 3.11 and 3.12. The new default path runs the coverage gate once and moves cross-platform checks to the compatibility workflow, cutting duplicate full-suite work before cache effects.

## Compatibility Matrix

The `Compatibility` workflow is manual and weekly. It runs a smoke matrix across:

- Ubuntu, macOS, and Windows.
- Python 3.11 and 3.12.

The matrix installs the package and runs import plus focused type/config smoke tests without coverage instrumentation.

## Release Please

The `Release Please` workflow opens version bump and changelog pull requests from conventional commits on `main`.

Configuration lives in:

- `.github/release-please-config.json`
- `.release-please-manifest.json`

The Python release strategy updates `pyproject.toml`, `CHANGELOG.md`, and `src/knoema/__init__.py`.

## Tag Release

The `Release` workflow runs only for tags matching `v*.*.*`.

It builds wheel and source distributions, runs `twine check`, uploads artifacts, creates a GitHub Release, and then publishes to PyPI through Trusted Publishing.

PyPI publication requires this external setup before pushing a release tag:

1. Create or claim the `knoema-engine` PyPI project under the Celovin account.
2. Configure PyPI Trusted Publisher for owner `Celovin`, repository `knoema`, workflow `release.yml`, environment `pypi`.
3. Configure the GitHub `pypi` environment with protection rules appropriate for production publishing.

The workflow does not use a PyPI API token.

## Local Dry Run

Run the patch-release dry run before tagging:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python scripts\release_dry_run.py --version 0.1.1
```

The script copies the git-visible working tree to a temporary directory, patches the version in that copy, builds the distributions, and runs `twine check`.
