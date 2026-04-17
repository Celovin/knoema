# Release Playbook

This playbook prepares Knoema Engine releases without publishing anything accidentally.

## Local Build

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\pip install -e ".[release]"
.venv\Scripts\python -m build
.venv\Scripts\twine check dist\*
```

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

The workflow at `.github\workflows\release.yml` runs when a version tag is pushed.

```powershell
git tag v0.1.0
git push origin v0.1.0
```

It builds wheel/sdist artifacts, runs `twine check`, uploads workflow artifacts, and creates a GitHub Release for the tag.

## PyPI

Do not upload to PyPI until the package name and public release timing are final.

Preferred future path:

1. Create the `knoema-engine` PyPI project under the Celovin account.
2. Configure PyPI Trusted Publisher for `Celovin/knoema` and `.github/workflows/release.yml`.
3. Add a separate publishing job with `pypa/gh-action-pypi-publish@release/v1`.
4. Require an approval environment before production PyPI publication.

Manual fallback after approval:

```powershell
.venv\Scripts\twine upload dist\*
```
