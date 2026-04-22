# Observability

Knoema observability is opt-in. By default, the API server does not expose `/metrics`, does not configure tracing, and does not export request or tenant data.

## Enable Prometheus Metrics

Install the optional dependencies:

```bash
python -m pip install -e ".[observability]"
```

Start the API server with metrics enabled:

```bash
KNOEMA_METRICS_ENABLED=1 uvicorn knoema.api.server:app --host 127.0.0.1 --port 8000
```

Scrape `/metrics` with Prometheus:

```yaml
scrape_configs:
  - job_name: knoema
    static_configs:
      - targets: ["127.0.0.1:8000"]
```

Metric families:

| Metric | Labels | Notes |
| --- | --- | --- |
| `knoema_requests_total` | `route`, `method`, `status`, `tier` | API request counts. |
| `knoema_request_duration_seconds_bucket` | `route` | Route-level latency histogram buckets. |
| `knoema_billing_tokens_total` | `tenant_id_hash`, `direction`, `tier` | Input and output token counts. Tenant IDs are hashed before labeling. |
| `knoema_webhook_dispatch_total` | `status` | Webhook delivery, failure, and exhaustion counts. |
| `knoema_rate_limit_hits_total` | `tier` | Tier rate-limit denials. |

Tenant labels use a 16-character SHA-256 prefix so plaintext tenant IDs do not appear in metric output. Keep route labels templated and avoid adding prompt, completion, API key, or raw customer identifiers as labels.

## Enable OpenTelemetry Tracing

Set the OTLP exporter endpoint and exporter mode:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318/v1/traces \
KNOEMA_OTEL_EXPORTER=otlp \
uvicorn knoema.api.server:app --host 127.0.0.1 --port 8000
```

The same OTLP endpoint format works with Grafana Tempo, Honeycomb OpenTelemetry ingest, and Jaeger OTLP HTTP receivers. Tracing instruments FastAPI requests and the billing LLM gateway span around LiteLLM calls.

## Audit Logs vs Metrics

Metrics are live operational counters and latency histograms. They are not forensic records and should not be used to answer who changed a key or when a webhook failed. For audit-grade commercial records, use the [audit log](audit-log.md).
