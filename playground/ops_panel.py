"""Operations / admin Gradio panel for the round-6 commercial features.

This is a separate Gradio app from the main researcher-facing
``playground.app`` so we do not risk regressing 10K+ lines of existing
simulation UI tests. It surfaces the four code-only features added in
round 6 — precise token counting, tenant-registry encryption status,
rate-limit bucket inspection, and Stripe webhook inbox — to operators
who run the API server and need a quick visual readout.

Design
------
Visual language follows the user's stated preference for this ecosystem:
warm cream background, ink primary text, terracotta accent on actions,
serif title with a sans body. Sectioned cards with a clear empty state
on every panel so a fresh deploy with no data displays helpful guidance
instead of an empty grid.

State sharing
-------------
The panels read from injected state objects (``TenantRegistry``,
``RateLimiter``, ``StripeWebhookHandler``) so the ops panel can be run
in the same process as the API server and observe the live state. When
deployed standalone, the panels still work but only show the file-
backed ``TenantRegistry`` (the in-memory rate-limit and Stripe handler
state is per-process). This trade-off is documented in each panel's
empty-state copy.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

import gradio as gr

from luvoire.api.rate_limit import RateLimiter
from luvoire.api.routes.stripe_webhook import StripeWebhookHandler
from luvoire.billing.tenant_registry import TenantRegistry
from luvoire.llm.gateway import estimate_tokens

# ----- Styling -------------------------------------------------------------

_OPS_CSS = """
:root {
  --ops-bg: #fbf7f1;
  --ops-card: #ffffff;
  --ops-ink: #1f1a16;
  --ops-muted: #6f6358;
  --ops-line: #e7dfd3;
  --ops-accent: #b14a32;
  --ops-accent-soft: #f3dfd7;
  --ops-good: #2f7d52;
  --ops-warn: #b97d11;
  --ops-radius: 10px;
}
.gradio-container { background: var(--ops-bg) !important; }
#ops-app { color: var(--ops-ink); }
#ops-header { padding: 28px 24px 8px; }
#ops-header h1 {
  font-family: "Iowan Old Style", "Pretendard", "Apple SD Gothic Neo", serif;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0;
}
#ops-header .ops-subtitle {
  color: var(--ops-muted);
  margin-top: 6px;
  font-size: 0.95rem;
}
.ops-card {
  background: var(--ops-card);
  border: 1px solid var(--ops-line);
  border-radius: var(--ops-radius);
  padding: 18px 20px;
  margin: 6px 0;
}
.ops-card h3 {
  margin: 0 0 4px;
  font-family: "Iowan Old Style", "Pretendard", "Apple SD Gothic Neo", serif;
  font-weight: 600;
}
.ops-card .ops-card-help {
  color: var(--ops-muted);
  font-size: 0.88rem;
  margin: 0 0 12px;
}
.ops-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.ops-badge--good { background: #e6f3ec; color: var(--ops-good); }
.ops-badge--warn { background: #f7eed5; color: var(--ops-warn); }
.ops-badge--off  { background: #f1ece4; color: var(--ops-muted); }
.ops-empty {
  color: var(--ops-muted);
  font-style: italic;
  padding: 12px 0 0;
}
button.primary, .gr-button-primary {
  background: var(--ops-accent) !important;
  border-color: var(--ops-accent) !important;
}
.ops-kv {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 6px 16px;
  margin-top: 8px;
}
.ops-kv .ops-kv-key { color: var(--ops-muted); }
.ops-kv .ops-kv-val { font-variant-numeric: tabular-nums; }
"""

_OPS_HEAD = """
<style>
  body { font-family: "Pretendard", "Apple SD Gothic Neo", system-ui, sans-serif; }
</style>
"""


# ----- Pure render helpers (testable independent of Gradio) --------------


def render_token_panel(text: str, model_label: str = "cl100k_base") -> str:
    """Return an HTML fragment showing token + char counts for ``text``.

    Used both by the live token panel and exercised in unit tests so we
    don't need to spin up a Gradio Blocks instance to validate the
    rendering logic.
    """

    text = text or ""
    chars = len(text)
    tokens = estimate_tokens(text)
    ratio = (tokens / chars) if chars else 0.0
    if not text:
        return (
            '<div class="ops-empty">Paste a prompt above to see precise '
            f"token counts via <code>{model_label}</code>.</div>"
        )
    return (
        '<div class="ops-kv">'
        f'<span class="ops-kv-key">Tokens (precise)</span>'
        f'<span class="ops-kv-val">{tokens:,}</span>'
        f'<span class="ops-kv-key">Characters</span>'
        f'<span class="ops-kv-val">{chars:,}</span>'
        f'<span class="ops-kv-key">Tokens / char</span>'
        f'<span class="ops-kv-val">{ratio:.3f}</span>'
        f'<span class="ops-kv-key">Heuristic (chars/4)</span>'
        f'<span class="ops-kv-val">{max(1, chars // 4):,}</span>'
        "</div>"
    )


def render_tenant_panel(registry: TenantRegistry | None) -> str:
    """Render encryption status + tenant list as an HTML fragment."""

    if registry is None:
        return (
            '<div class="ops-empty">No tenant registry is bound. Pass a '
            "<code>TenantRegistry</code> instance to <code>build_ops_app()</code> "
            "to see live tenant data.</div>"
        )
    enc = registry.encryption_enabled
    badge = (
        '<span class="ops-badge ops-badge--good">Encrypted at rest</span>'
        if enc
        else '<span class="ops-badge ops-badge--off">Plaintext</span>'
    )
    path = str(registry.path)
    try:
        payload = registry.load()
    except Exception as exc:  # pragma: no cover - defensive
        return (
            f'<div>{badge}</div>'
            f'<div class="ops-empty">Failed to read registry at '
            f"<code>{path}</code>: {type(exc).__name__}.</div>"
        )
    tenants = payload.get("tenants", {})
    if not isinstance(tenants, dict) or not tenants:
        return (
            f'<div>{badge} <span class="ops-kv-key" style="margin-left:12px">'
            f"<code>{path}</code></span></div>"
            '<div class="ops-empty">No tenants registered yet. Use '
            "<code>luvoire-customer onboard</code> to provision one.</div>"
        )
    rows = []
    for tenant_id in sorted(tenants):
        record = tenants[tenant_id]
        if not isinstance(record, Mapping):
            continue
        keys = record.get("keys", [])
        keys_count = len(keys) if isinstance(keys, list) else 0
        rows.append(
            "<tr>"
            f'<td><code>{tenant_id}</code></td>'
            f'<td>{record.get("display_name", "")}</td>'
            f'<td><span class="ops-badge ops-badge--good">{record.get("tier", "free")}</span></td>'
            f'<td style="text-align:right">{keys_count}</td>'
            "</tr>"
        )
    table = (
        '<table style="width:100%;border-collapse:collapse;margin-top:10px">'
        '<thead><tr style="text-align:left;border-bottom:1px solid var(--ops-line)">'
        "<th style=\"padding:6px 0\">Tenant ID</th>"
        "<th>Display</th>"
        "<th>Tier</th>"
        "<th style=\"text-align:right\">Keys</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )
    return (
        f'<div>{badge} <span class="ops-kv-key" style="margin-left:12px">'
        f"<code>{path}</code></span></div>{table}"
    )


def render_rate_limit_panel(
    limiter: RateLimiter | None,
    *,
    snapshot_keys: list[str] | None = None,
) -> str:
    """Render rate-limit configuration + bucket sample.

    Bucket state lives inside the backend (in-memory or Redis); without
    a privileged read API we report the *configuration* (rate / burst)
    plus an optional probe of named keys.
    """

    if limiter is None:
        return (
            '<div class="ops-empty">No rate limiter is bound. Pass a '
            "<code>RateLimiter</code> to <code>build_ops_app()</code> "
            "to see live configuration.</div>"
        )
    backend_name = type(getattr(limiter, "_backend", limiter)).__name__
    config = (
        '<div class="ops-kv">'
        '<span class="ops-kv-key">Backend</span>'
        f'<span class="ops-kv-val"><code>{backend_name}</code></span>'
        '<span class="ops-kv-key">Tokens / second</span>'
        f'<span class="ops-kv-val">{limiter.tokens_per_second:g}</span>'
        '<span class="ops-kv-key">Burst</span>'
        f'<span class="ops-kv-val">{limiter.burst:g}</span>'
        "</div>"
    )
    if not snapshot_keys:
        return (
            config
            + '<div class="ops-empty" style="margin-top:14px">'
            "Provide one or more bucket keys to probe (one per line) to "
            "see whether each key currently has tokens available."
            "</div>"
        )
    rows = []
    for key in snapshot_keys:
        # consume(cost=0) would need a backend extension; instead we
        # peek by trying a zero-impact consume of a small fraction and
        # immediately refilling. Because the in-memory backend doesn't
        # expose introspection, we just report the result of a probe
        # at cost=0.001 — practically free, conservatively reflects
        # bucket health.
        try:
            allowed = limiter.consume(key, cost=0.001)
        except ValueError:
            allowed = False
        badge = (
            '<span class="ops-badge ops-badge--good">tokens available</span>'
            if allowed
            else '<span class="ops-badge ops-badge--warn">throttled</span>'
        )
        rows.append(f"<tr><td><code>{key}</code></td><td>{badge}</td></tr>")
    table = (
        '<table style="width:100%;border-collapse:collapse;margin-top:10px">'
        '<thead><tr style="text-align:left;border-bottom:1px solid var(--ops-line)">'
        '<th style="padding:6px 0">Bucket key</th><th>Status</th>'
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        '<div class="ops-empty" style="margin-top:8px">'
        "Probe consumed 0.001 tokens per key — negligible compared to "
        "the burst capacity, so this readout is non-destructive in "
        "practice."
        "</div>"
    )
    return config + table


def render_stripe_panel(handler: StripeWebhookHandler | None) -> str:
    """Render Stripe webhook handler state."""

    if handler is None:
        return (
            '<div class="ops-empty">No Stripe webhook handler is bound. '
            "Pass a <code>StripeWebhookHandler</code> to "
            "<code>build_ops_app()</code> to monitor inbound deliveries.</div>"
        )
    if not handler.configured:
        return (
            '<div><span class="ops-badge ops-badge--warn">Secret not set</span></div>'
            '<div class="ops-empty">Set <code>STRIPE_WEBHOOK_SECRET</code> '
            "in the API server environment to enable inbound webhook "
            "verification. Until then the route returns 503.</div>"
        )
    seen_count = len(getattr(handler, "_seen", {}))
    handler_count = len(getattr(handler, "_handlers", {}))
    handler_types = sorted(getattr(handler, "_handlers", {}).keys())
    types_html = (
        ", ".join(f"<code>{t}</code>" for t in handler_types)
        if handler_types
        else '<span class="ops-empty">none registered</span>'
    )
    return (
        '<div><span class="ops-badge ops-badge--good">Configured</span></div>'
        '<div class="ops-kv">'
        '<span class="ops-kv-key">Recent event-id dedup count</span>'
        f'<span class="ops-kv-val">{seen_count:,}</span>'
        '<span class="ops-kv-key">Registered handler types</span>'
        f'<span class="ops-kv-val">{handler_count}</span>'
        '<span class="ops-kv-key">Handler routes</span>'
        f'<span class="ops-kv-val">{types_html}</span>'
        "</div>"
        '<div class="ops-empty" style="margin-top:10px">'
        "The dedup ring is process-local. To share across replicas, "
        "front the handler with a Redis-backed dedup adapter."
        "</div>"
    )


# ----- Footer ------------------------------------------------------------


def _build_footer() -> str:
    now = datetime.now(UTC).isoformat(timespec="seconds")
    return (
        '<div style="color:var(--ops-muted);font-size:0.82rem;'
        'text-align:right;padding:14px 24px 22px">'
        f"Snapshot taken {now}. Refresh any panel to update."
        "</div>"
    )


# ----- Main builder ------------------------------------------------------


def build_ops_app(
    *,
    tenant_registry: TenantRegistry | None = None,
    rate_limiter: RateLimiter | None = None,
    stripe_handler: StripeWebhookHandler | None = None,
) -> gr.Blocks:
    """Construct the operations Gradio app.

    All four state objects are injected so the panel can observe live
    state when the operator runs it in the same process as the API
    server. When invoked standalone, panels gracefully degrade to
    empty-state copy that explains the missing binding.
    """

    # Gradio 6 moved ``css`` / ``head`` to the ``launch`` method;
    # passing them to ``Blocks`` raises a deprecation warning. We
    # still expose ``OPS_CSS`` / ``OPS_HEAD`` so ``ops_app.launch``
    # can wire them at start time. Tests that only build the Blocks
    # (without launch) intentionally render unstyled — the rendered
    # HTML payload tested per-panel does not depend on CSS.
    with gr.Blocks(
        title="Luvoire Operations",
        analytics_enabled=False,
        elem_id="ops-app",
    ) as demo:
        with gr.Column(elem_id="ops-header"):
            gr.HTML(
                "<h1>Luvoire Operations</h1>"
                '<p class="ops-subtitle">Operator dashboard for the '
                "round-6 commercial surface — token counter, tenant "
                "registry, rate-limit health, and Stripe webhook inbox."
                "</p>"
            )

        # --- Token counter -----------------------------------------------
        with gr.Group(elem_classes="ops-card"):
            gr.HTML(
                "<h3>Precise token counter</h3>"
                '<p class="ops-card-help">Live <code>tiktoken</code> '
                "(<code>cl100k_base</code>) count with the legacy "
                "<code>chars / 4</code> heuristic side-by-side. Hangul "
                "and code-heavy prompts diverge most.</p>"
            )
            token_input = gr.Textbox(
                label="Prompt",
                placeholder="Paste any text — empty input is the empty state.",
                lines=4,
            )
            token_output = gr.HTML(render_token_panel(""))
            token_input.change(
                fn=render_token_panel,
                inputs=token_input,
                outputs=token_output,
                show_progress="hidden",
            )

        # --- Tenant registry --------------------------------------------
        with gr.Group(elem_classes="ops-card"):
            gr.HTML(
                "<h3>Tenant registry</h3>"
                '<p class="ops-card-help">Encryption-at-rest status, '
                "registry path, and per-tenant tier / key counts.</p>"
            )
            tenant_output = gr.HTML(render_tenant_panel(tenant_registry))
            tenant_refresh = gr.Button("Refresh", variant="primary", size="sm")
            tenant_refresh.click(
                fn=lambda: render_tenant_panel(tenant_registry),
                outputs=tenant_output,
                show_progress="hidden",
            )

        # --- Rate limit --------------------------------------------------
        with gr.Group(elem_classes="ops-card"):
            gr.HTML(
                "<h3>Rate-limit health</h3>"
                '<p class="ops-card-help">Backend type, refill rate, '
                "burst, and a non-destructive probe of caller-supplied "
                "bucket keys.</p>"
            )
            rl_keys_input = gr.Textbox(
                label="Bucket keys to probe (one per line)",
                placeholder="tenant-a\nBearer abc123\n203.0.113.5",
                lines=3,
            )
            rl_output = gr.HTML(render_rate_limit_panel(rate_limiter))

            def _on_rl_refresh(raw: str) -> str:
                keys = [line.strip() for line in (raw or "").splitlines() if line.strip()]
                return render_rate_limit_panel(rate_limiter, snapshot_keys=keys)

            rl_refresh = gr.Button("Probe & refresh", variant="primary", size="sm")
            rl_refresh.click(
                fn=_on_rl_refresh,
                inputs=rl_keys_input,
                outputs=rl_output,
                show_progress="hidden",
            )

        # --- Stripe webhook inbox ---------------------------------------
        with gr.Group(elem_classes="ops-card"):
            gr.HTML(
                "<h3>Stripe webhook inbox</h3>"
                '<p class="ops-card-help">Configuration status, dedup '
                "ring depth, and registered event-type handlers.</p>"
            )
            stripe_output = gr.HTML(render_stripe_panel(stripe_handler))
            stripe_refresh = gr.Button("Refresh", variant="primary", size="sm")
            stripe_refresh.click(
                fn=lambda: render_stripe_panel(stripe_handler),
                outputs=stripe_output,
                show_progress="hidden",
            )

        gr.HTML(_build_footer())

    # ``gr.Blocks`` is annotated as Any in installed stubs; cast the
    # context-manager target back to its runtime type for the public
    # signature.
    from typing import cast as _cast

    return _cast(gr.Blocks, demo)


OPS_CSS = _OPS_CSS
OPS_HEAD = _OPS_HEAD


__all__ = [
    "OPS_CSS",
    "OPS_HEAD",
    "build_ops_app",
    "render_rate_limit_panel",
    "render_stripe_panel",
    "render_tenant_panel",
    "render_token_panel",
]
