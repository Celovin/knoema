# Release Playbook

This playbook prepares Knoema Engine releases with tag-gated publishing.

## Local Build

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\pip install -e ".[release]"
.venv\Scripts\python -m build
.venv\Scripts\twine check dist\*
```

## Patch Release Dry Run

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\python scripts\release_dry_run.py --version 0.1.1
```

The dry run copies the git-visible working tree to a temporary directory, patches the version only in that copy, builds distributions, and runs `twine check`.

## Install Smoke Test

```powershell
cd C:\Users\admin\Projects\knoema
py -3 -m venv tmp\wheel-smoke
tmp\wheel-smoke\Scripts\python -m pip install --upgrade pip
tmp\wheel-smoke\Scripts\python -m pip install --no-deps dist\knoema_engine-0.1.0-py3-none-any.whl
tmp\wheel-smoke\Scripts\python -c "from importlib.metadata import version; print(version('knoema-engine'))"
```

Use `--no-deps` for the metadata smoke test when you only need to verify the wheel installs. Full runtime imports require the declared package dependencies.

## Docker Smoke Test

```powershell
cd C:\Users\admin\Projects\knoema
docker build -t knoema-engine:0.1.0 .
docker run --rm knoema-engine:0.1.0
```

## GitHub Release

Release Please opens version and changelog pull requests from conventional commits on `main`. The tag workflow at `.github\workflows\release.yml` runs when a version tag is pushed.

```powershell
git tag v0.1.0
git push origin v0.1.0
```

It builds wheel/sdist artifacts, runs `twine check`, uploads workflow artifacts, creates a GitHub Release for the tag, and then starts PyPI Trusted Publishing.

## PyPI

PyPI publishing is tag-gated and uses GitHub OIDC. No PyPI token should be stored in this repository.

Before pushing a release tag that should publish to PyPI:

1. Create the `knoema-engine` PyPI project under the Celovin account.
2. Configure PyPI Trusted Publisher for `Celovin/knoema`, workflow `release.yml`, and environment `pypi`.
3. Configure the GitHub `pypi` environment with production approval rules.
4. Run the `0.1.1` dry run and confirm CI is green.

Manual fallback after explicit approval:

```powershell
.venv\Scripts\twine upload dist\*
```
