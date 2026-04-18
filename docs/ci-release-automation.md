# CI and Release Automation

Knoema uses a fast default CI path and a broader compatibility workflow.

## Default CI

The `CI` workflow runs on every push to `main` and every pull request.

- Ubuntu + Python 3.12 quality gate.
- pip cache through `actions/setup-python`.
- pre-commit hook cache warmed through `PRE_COMMIT_HOME`.
- pytest cache restored between runs.
- hard gates: Ruff, mypy, pytest with 90% coverage, and the `v0.2.0` release dry run.

The previous default CI duplicated the full coverage suite on Python 3.11 and 3.12. The new default path runs the coverage gate once and moves cross-platform checks to the compatibility workflow, cutting duplicate full-suite work before cache effects.

## Compatibility Matrix

The `Compatibility` workflow is manual and weekly. It runs a smoke matrix across:

- Ubuntu, macOS, and Windows.
- Python 3.11 and 3.12.

The matrix installs the package and runs import plus focused type/config smoke tests without coverage instrumentation.

## Release Please

The `Release Please` workflow opens version bump and changelog pull requests from conventional commits on `main`.

The workflow is gated by the repository variable `ENABLE_RELEASE_PLEASE=1`. On April 18, 2026, the repository owner enabled GitHub Actions `Read and write` workflow permissions, allowed Actions to approve pull requests, and set that variable for `Celovin/knoema`. Keep the external activation status check in the release checklist so configuration drift is caught before tagging.

Configuration lives in:

- `.github/release-please-config.json`
- `.release-please-manifest.json`

The Python release strategy updates `pyproject.toml`, `CHANGELOG.md`, and `src/knoema/__init__.py`.

## External Activation Status

Use the external activation status script before trying to un-gate release automation or production deployment flows:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python scripts\external_activation_status.py
```

The script prints a JSON snapshot covering:

- GitHub repository visibility and latest release
- Hugging Face local auth namespace for the Playground target
- Vercel project link presence for production deployment
- GitHub Actions workflow permission mode
- Repository variable state for `ENABLE_RELEASE_PLEASE`
- Suggested next actions when any blocker is still present

The local `website/.vercel/project.json` link file is machine-specific and is ignored by git.

Add `--fail-on-blockers` when you want a non-zero exit code if any activation blocker is still present.

When the only remaining blocker is Hugging Face authentication, deploy the Playground with:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python scripts\deploy_playground_space.py
```

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
.venv\Scripts\python scripts\release_dry_run.py --version 0.2.0
```

The script copies the git-visible working tree to a temporary directory, patches the version in that copy, builds the distributions, and runs `twine check`.

Recommended local sequence before a production tag:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python scripts\external_activation_status.py --fail-on-blockers
.venv\Scripts\python scripts\release_dry_run.py --version 0.2.0
```

Or run the combined checker:

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python scripts\pre_release_check.py --version 0.2.0
```
