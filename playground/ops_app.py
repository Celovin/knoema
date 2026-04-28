"""Standalone launcher for the Luvoire Operations panel.

Run with::

    python -m playground.ops_app

The launcher constructs default ``TenantRegistry`` / ``RateLimiter`` /
``StripeWebhookHandler`` instances and binds them into the Gradio app
so an operator running this on the same host as the API server sees
file-backed state (registry) plus live in-process state when the same
Python process also hosts the API.
"""

from __future__ import annotations

import os
from pathlib import Path

from luvoire.api.rate_limit import RateLimiter
from luvoire.api.routes.stripe_webhook import StripeWebhookHandler
from luvoire.billing.tenant_registry import TenantRegistry
from playground.ops_panel import build_ops_app


def _default_tenant_registry() -> TenantRegistry:
    """Resolve the registry path the API server uses by default.

    Operators who relocate the registry via env should mirror that env
    when running the ops panel.
    """

    raw = os.environ.get("LUVOIRE_TENANT_REGISTRY_PATH", "").strip()
    path = Path(raw) if raw else Path("var/billing/tenants.json")
    return TenantRegistry(path)


def main() -> None:
    registry = _default_tenant_registry()
    limiter = RateLimiter.from_env()
    stripe_handler = StripeWebhookHandler()
    app = build_ops_app(
        tenant_registry=registry,
        rate_limiter=limiter,
        stripe_handler=stripe_handler,
    )
    # ``server_name`` defaults to localhost; operators wanting LAN
    # access should set ``GRADIO_SERVER_NAME=0.0.0.0`` in env. Sharing
    # is OFF by default — this is an admin surface, never a public URL.
    app.launch(
        server_name=os.environ.get("LUVOIRE_OPS_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.environ.get("LUVOIRE_OPS_SERVER_PORT", "7861")),
        share=False,
    )


if __name__ == "__main__":
    main()
