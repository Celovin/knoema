# Playground Deploy Runbook

The Playground Space is deployed from `playground/` with:

```powershell
python scripts/deploy_playground_space.py --ensure-fresh-install --factory-reboot-on-pyproject-change
```

## Why the fresh-install pin exists

Hugging Face build caches can reuse a previously resolved git dependency when the dependency line does not change. `--ensure-fresh-install` reads the current repository commit with `git rev-parse HEAD`, verifies it with `git cat-file -e`, and rewrites `playground/requirements.txt` so `luvoire-engine` installs from that exact commit during the Space build.

This removes the manual repin step after source changes that add new modules or dependency metadata.

## Flags

- `--ensure-fresh-install`: pins the `luvoire-engine` git dependency in `playground/requirements.txt` to the verified current HEAD before upload.
- `--factory-reboot-on-pyproject-change`: compares the outgoing `playground/requirements.txt` and source `pyproject.toml` against the previous Space snapshot/source pin. If either changed, it calls `HfApi().restart_space(..., factory_reboot=True)` after upload.
- `--dry-run`: validates HF CLI authentication and prints planned commands without uploading, rebooting, or warming the Space.

Every non-dry deploy ends by running:

```powershell
python scripts/warm_space.py --repo-id celovin/luvoire-playground
```

## Warmup behavior

`scripts/warm_space.py` polls `HfApi().space_info(repo_id).runtime.stage` every 10 seconds for up to 10 minutes.

- On `RUNNING`, it requests `https://huggingface.co/spaces/<repo-id>` and requires HTTP 200.
- On `RUNTIME_ERROR` or `BUILD_ERROR`, it prints the last 50 run-log lines from `/api/spaces/<repo-id>/logs/run` and exits non-zero.
- On timeout, it prints the last observed stage plus transition history and exits non-zero.

## Exit codes

- `0`: upload and warmup completed; the Space root returned HTTP 200.
- `1`: warmup failed, reached an error stage, or timed out. Inspect the printed run-log tail before retrying.
