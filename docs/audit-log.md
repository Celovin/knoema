# Audit Log

Knoema writes commercial audit records as JSONL so customer-provisioning and billing events can be reviewed without querying application state. The log is append-only during normal operation. Administrative cleanup is limited to the documented retention purge.

## Event Types

| Event type | Meaning | Metadata |
| --- | --- | --- |
| `commercial.key_issued` | A tenant API key was issued. | `api_key_id`, `tier`, `issuer` |
| `commercial.key_rotated` | An existing API key was rotated. | `old_api_key_id`, `new_api_key_id`, `tier`, `grace_expires_at` |
| `commercial.key_revoked` | An API key was revoked. | `api_key_id`, `reason` |
| `commercial.webhook_dispatched` | A webhook delivery attempt started. | `delivery_id`, `event_type`, `url_hash` |
| `commercial.webhook_failed` | A webhook delivery attempt failed. | `delivery_id`, `event_type`, `attempt`, `last_status`, `url_hash` |
| `commercial.webhook_exhausted` | The webhook retry budget was used. | `delivery_id`, `event_type`, `attempts`, `last_status`, `url_hash` |
| `commercial.tier_limit_exceeded` | A tier attempted a disallowed model or key source. | `tier`, `model`, `api_key_source`, `error_code` |
| `commercial.cap_exhausted_output_tokens` | A monthly output-token cap blocked a request. | `tier`, `model`, `cap`, `observed` |

Plaintext API key secrets and webhook URLs are not written to metadata. Webhook URLs are recorded as SHA-256 hashes.

## Retention

The default retention window is 90 days. Operators can purge older records with `AuditLog.purge_older_than(days=90)`. Longer retention needs legal review before it becomes a production default.

## Queries

Use the read-only helper to inspect one tenant:

```bash
python scripts/audit_log_show.py tenant_123 --since 2026-04-01
```

For a non-default path:

```bash
python scripts/audit_log_show.py tenant_123 --path var/audit/commercial.jsonl
```

For live operational metrics, use the observability guide once that optional module is enabled. For forensic records, this audit log remains the source of truth.
