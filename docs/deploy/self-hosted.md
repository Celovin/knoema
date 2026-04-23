# Self-hosted CLI and Docker

Luvoire can run fully local simulations from a source checkout, a wheel install, or a Docker container. The self-hosted path is intended for studio VPCs, classroom labs, and reproducibility checks where the run artifacts stay on the operator machine.

## CLI

Install the package and run a YAML config:

```bash
python -m pip install luvoire-engine
luvoire run examples/cli_dorm.yaml --json
```

On Windows PowerShell, use the native path separator when referring to local
files:

```powershell
python -m pip install luvoire-engine
luvoire run examples\cli_dorm.yaml --json
```

List the packaged Playground scenarios:

```powershell
luvoire list-scenarios
luvoire list-scenarios --json
```

Verify a reproducibility certificate exported by the Playground:

```powershell
luvoire verify run_fingerprint.json --result-jsonl run.jsonl --json
```

Start the local Playground:

```powershell
luvoire playground --host 127.0.0.1 --port 7860
```

Use `--dry-run --json` to check the launch plan without binding a port.

## Docker Compose

From the repository root:

```bash
docker compose up --build
```

The Playground is served at `http://localhost:7860`. The compose file mounts
`./runs` into `/app/runs` so JSONL exports and reproducibility artifacts survive
container restarts.

Build and run the image directly on a Linux host:

```bash
docker build -t luvoire-engine:0.3.0 .
docker run --rm -p 7860:7860 -v "$PWD/runs:/app/runs" luvoire-engine:0.3.0
```

## Environment

Set provider keys only when a live provider mode is needed:

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
```

On Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "..."
$env:ANTHROPIC_API_KEY = "..."
```

Local replay, scenario validation, scoring, and certificate verification do not require API keys.

## VPC Notes

- Bind the container to an internal load balancer when exposing it inside a private studio or university network.
- Keep `GRADIO_ANALYTICS_ENABLED=False` for private deployments.
- Mount a persistent volume for `/app/runs` and back it up with the rest of the study artifacts.
- Store `run_fingerprint.json`, the source YAML, and the result JSONL together for audit replay.
