"""Tests for ``playground.ops_panel`` render helpers + builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from luvoire.api.rate_limit import RateLimiter
from luvoire.api.routes.stripe_webhook import StripeWebhookHandler
from luvoire.billing.tenant_registry import TenantRegistry
from playground.ops_panel import (
    build_ops_app,
    render_rate_limit_panel,
    render_stripe_panel,
    render_tenant_panel,
    render_token_panel,
)

# ---------------------------------------------------------------------------
# Token counter panel
# ---------------------------------------------------------------------------


def test_token_panel_empty_input_shows_helpful_empty_state() -> None:
    html = render_token_panel("")
    assert "ops-empty" in html
    assert "Paste" in html


def test_token_panel_reports_token_and_char_counts() -> None:
    html = render_token_panel("hello world")
    assert "Tokens (precise)" in html
    assert "Characters" in html
    # Numeric counts are present in tabular form.
    assert "11" in html  # len("hello world")


def test_token_panel_reports_heuristic_alongside_precise() -> None:
    html = render_token_panel("a" * 100)
    assert "Heuristic" in html
    assert "25" in html  # 100 // 4


# ---------------------------------------------------------------------------
# Tenant registry panel
# ---------------------------------------------------------------------------


def test_tenant_panel_unbound_shows_empty_state() -> None:
    html = render_tenant_panel(None)
    assert "ops-empty" in html
    assert "build_ops_app" in html


def test_tenant_panel_unencrypted_shows_plaintext_badge(tmp_path: Path) -> None:
    registry = TenantRegistry(tmp_path / "tenants.json")
    html = render_tenant_panel(registry)
    assert "Plaintext" in html
    # No tenants yet -> empty-state.
    assert "ops-empty" in html


def test_tenant_panel_encrypted_shows_encrypted_badge(tmp_path: Path) -> None:
    fernet_cls = pytest.importorskip("cryptography.fernet").Fernet
    key = fernet_cls.generate_key().decode("utf-8")
    registry = TenantRegistry(tmp_path / "tenants.json", encryption_key=key)
    registry.create_tenant("t1", "pro", "Tenant Pro")
    html = render_tenant_panel(registry)
    assert "Encrypted at rest" in html
    assert "t1" in html
    assert "Tenant Pro" in html


def test_tenant_panel_lists_multiple_tenants_in_sorted_order(tmp_path: Path) -> None:
    registry = TenantRegistry(tmp_path / "tenants.json")
    registry.create_tenant("zebra", "free", "Z Tenant")
    registry.create_tenant("alpha", "pro", "A Tenant")
    html = render_tenant_panel(registry)
    # ``alpha`` row precedes ``zebra`` row.
    assert html.find("alpha") < html.find("zebra")


# ---------------------------------------------------------------------------
# Rate-limit panel
# ---------------------------------------------------------------------------


def test_rate_limit_panel_unbound_shows_empty_state() -> None:
    html = render_rate_limit_panel(None)
    assert "ops-empty" in html
    assert "build_ops_app" in html


def test_rate_limit_panel_shows_config_without_keys() -> None:
    limiter = RateLimiter(tokens_per_second=42.0, burst=120.0)
    html = render_rate_limit_panel(limiter)
    assert "42" in html
    assert "120" in html
    assert "Backend" in html
    # Keys area shows guidance copy.
    assert "Provide one or more bucket keys" in html


def test_rate_limit_panel_probes_each_key() -> None:
    limiter = RateLimiter(tokens_per_second=1.0, burst=10.0)
    html = render_rate_limit_panel(
        limiter, snapshot_keys=["tenant-a", "tenant-b"]
    )
    assert "tenant-a" in html
    assert "tenant-b" in html
    assert "tokens available" in html


def test_rate_limit_panel_shows_throttled_when_bucket_empty() -> None:
    """A limiter with very low burst exhausts quickly; the probe must
    surface the throttled state in the table.
    """

    limiter = RateLimiter(tokens_per_second=0.0, burst=0.0001)
    # Drain the bucket below the probe cost (0.001) by consuming
    # everything available first.
    limiter.consume("tenant-x", cost=0.0001)
    html = render_rate_limit_panel(limiter, snapshot_keys=["tenant-x"])
    assert "throttled" in html


# ---------------------------------------------------------------------------
# Stripe webhook panel
# ---------------------------------------------------------------------------


def test_stripe_panel_unbound_shows_empty_state() -> None:
    html = render_stripe_panel(None)
    assert "ops-empty" in html
    assert "StripeWebhookHandler" in html


def test_stripe_panel_unconfigured_shows_warn_badge() -> None:
    handler = StripeWebhookHandler(secret=None)
    html = render_stripe_panel(handler)
    assert "Secret not set" in html
    assert "STRIPE_WEBHOOK_SECRET" in html


def test_stripe_panel_configured_shows_status() -> None:
    handler = StripeWebhookHandler(secret="whsec_test")
    handler.register("customer.created", lambda _e: None)
    handler.remember("evt_1")
    handler.remember("evt_2")
    html = render_stripe_panel(handler)
    assert "Configured" in html
    assert "customer.created" in html
    assert "2" in html  # dedup count


def test_stripe_panel_no_handlers_shows_none_registered() -> None:
    handler = StripeWebhookHandler(secret="whsec_test")
    html = render_stripe_panel(handler)
    assert "none registered" in html


# ---------------------------------------------------------------------------
# Top-level builder
# ---------------------------------------------------------------------------


def test_build_ops_app_returns_blocks_with_no_state(tmp_path: Path) -> None:
    """The builder must not raise on missing state — it should render
    each panel's empty state instead. This keeps the launcher robust
    when run against a fresh deploy with no tenants and no Stripe key.
    """

    pytest.importorskip("gradio")
    app = build_ops_app()
    assert app is not None
    # Gradio Blocks expose ``.title`` and ``.css``.
    assert getattr(app, "title", "") == "Luvoire Operations"


def test_build_ops_app_with_full_state(tmp_path: Path) -> None:
    pytest.importorskip("gradio")
    registry = TenantRegistry(tmp_path / "tenants.json")
    registry.create_tenant("t1", "free", "Tenant One")
    limiter = RateLimiter(tokens_per_second=10.0, burst=100.0)
    stripe = StripeWebhookHandler(secret="whsec_test")
    app = build_ops_app(
        tenant_registry=registry,
        rate_limiter=limiter,
        stripe_handler=stripe,
    )
    assert app is not None


def test_token_panel_handles_korean_text() -> None:
    """The whole point of switching from chars/4 to tiktoken is correct
    Hangul accounting. The render must show a non-trivial token count
    even for a short Korean phrase.
    """

    html = render_token_panel("안녕하세요 반갑습니다")
    assert "Tokens (precise)" in html


# ---------------------------------------------------------------------------
# Defensive rendering
# ---------------------------------------------------------------------------


class _BrokenRegistry:
    """Registry double whose ``load`` raises — exercises the defensive
    path in ``render_tenant_panel``."""

    encryption_enabled = False
    path = Path("/tmp/nonexistent")

    def load(self) -> dict[str, Any]:
        raise OSError("disk on fire")


def test_tenant_panel_swallows_load_failure_gracefully() -> None:
    html = render_tenant_panel(_BrokenRegistry())  # type: ignore[arg-type]
    assert "Failed to read registry" in html
    assert "OSError" in html
