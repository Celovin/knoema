# Customer Onboarding

This guide provisions a commercial PoC tenant, issues a tenant API key, and verifies that the key can call the API server.

The tenant registry is `var/billing/tenants.json`. It is a file-backed PoC registry for v6. A production database migration is out of scope for this handoff.

## 7-Step Quickstart

1. Install the package from a source checkout:

```bash
python -m pip install -e ".[api]"
```

2. Create a Pro tenant and first API key:

```bash
knoema customer create \
  --tenant-id tenant_pro_demo \
  --tier pro \
  --display-name "Pro Demo"
```

The command prints a boxed secret once. Store the `Bearer knoema_...` value immediately. The registry stores only the key hash.

3. Start the API server after the tenant exists:

```bash
uvicorn knoema.api.server:app --host 127.0.0.1 --port 8000
```

If the server was already running, restart it so it reloads `var/billing/tenants.json`.

4. Export the token for local curl calls:

```bash
export KNOEMA_BEARER="knoema_<api-key-id>_<secret>"
```

5. Check that the server is reachable:

```bash
curl -s http://127.0.0.1:8000/healthz
```

6. Call `/simulations/run` as the Pro tenant:

```bash
curl -s \
  -X POST "http://127.0.0.1:8000/simulations/run?model=gpt-4o" \
  -H "Authorization: Bearer ${KNOEMA_BEARER}" \
  -H "Content-Type: application/json" \
  -d '{
    "runtime": {
      "duration_days": 1,
      "tick_duration_minutes": 1440,
      "prompt_language": "en"
    },
    "environment": {
      "start_time": "2026-04-19T09:00:00",
      "location_path": ["Korea", "Seoul", "Campus"],
      "conditions": {"weather": "clear"}
    },
    "agents": [
      {
        "agent_id": "agent-0",
        "name": "Agent 0",
        "age": 24,
        "background": "Synthetic participant.",
        "personality": {
          "openness": 0.5,
          "conscientiousness": 0.6,
          "extraversion": 0.4,
          "agreeableness": 0.7,
          "neuroticism": 0.3
        },
        "values": ["clarity"],
        "goals": ["cooperate"]
      }
    ],
    "local_response": "{\"action_type\":\"wait\",\"target\":null,\"content\":\"waits.\"}"
  }'
```

The response includes a `simulation_id`. Authenticated responses include `X-Knoema-Tenant-Tier: pro`.

7. Review usage, then rotate or revoke keys as needed:

```bash
knoema customer show-usage --tenant-id tenant_pro_demo --month 2026-04
knoema customer rotate-key --tenant-id tenant_pro_demo --api-key-id ak...
knoema customer revoke-key --tenant-id tenant_pro_demo --api-key-id ak... --reason operator-request
```

## Commands

| Command | Purpose |
| --- | --- |
| `knoema customer create` | Create a tenant and first API key. |
| `knoema customer issue-key` | Issue an additional key for an existing tenant. |
| `knoema customer rotate-key` | Issue a replacement key and leave the old key on a 24-hour grace window. |
| `knoema customer revoke-key` | Revoke a key immediately with an operator reason. |
| `knoema customer show-usage` | Aggregate JSONL usage rows by model for a tenant and optional month. |
| `knoema customer list` | List tenants with tier and key count. Secrets are excluded. |

## Files Written

| Path | Contents |
| --- | --- |
| `var/billing/tenants.json` | Tenant metadata and hashed API key records. |
| `var/billing/usage_YYYYMMDD.jsonl` | Metered usage rows from API and gateway calls. |
| `var/audit/commercial.jsonl` | Commercial audit events for issue, rotate, and revoke actions. |

Plaintext key secrets are printed only during create, issue, or rotate commands. They are not written to the registry, usage spool, audit log, or tenant list output.
