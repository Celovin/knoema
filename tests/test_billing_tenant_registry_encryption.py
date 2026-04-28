"""Round-6: tenant_registry Fernet encryption-at-rest."""

from __future__ import annotations

from pathlib import Path

import pytest

from luvoire.billing.tenant_registry import TenantRegistry


@pytest.fixture
def fernet_key() -> str:
    fernet_cls = pytest.importorskip("cryptography.fernet").Fernet
    return fernet_cls.generate_key().decode("utf-8")


def test_plaintext_fallback_when_no_key_configured(tmp_path: Path) -> None:
    """Without an encryption key, the registry must continue to write
    plaintext JSON so existing deployments are not broken.
    """

    registry = TenantRegistry(tmp_path / "tenants.json")
    assert registry.encryption_enabled is False
    registry.create_tenant("t1", "free", "Tenant One")
    body = (tmp_path / "tenants.json").read_bytes()
    assert body.startswith(b"{"), "plaintext mode must emit JSON"


def test_encryption_round_trip_with_key(tmp_path: Path, fernet_key: str) -> None:
    """When a Fernet key is configured, on-disk file is opaque
    Fernet-token bytes prefixed by a magic header. Reading it back
    with the same key must yield the original payload.
    """

    registry = TenantRegistry(tmp_path / "tenants.json", encryption_key=fernet_key)
    assert registry.encryption_enabled is True
    registry.create_tenant("t1", "pro", "Tenant Pro")
    body = (tmp_path / "tenants.json").read_bytes()
    assert body.startswith(b"luvoire-tenants-v1\n"), (
        "encrypted mode must emit the magic prefix"
    )
    assert b"Tenant Pro" not in body, "tenant payload must NOT be plaintext on disk"

    # Round-trip: a new TenantRegistry with the same key reads it back.
    reader = TenantRegistry(tmp_path / "tenants.json", encryption_key=fernet_key)
    payload = reader.load()
    assert payload["tenants"]["t1"]["display_name"] == "Tenant Pro"


def test_decryption_with_wrong_key_raises(tmp_path: Path, fernet_key: str) -> None:
    other_cls = pytest.importorskip("cryptography.fernet").Fernet
    other_key = other_cls.generate_key().decode("utf-8")

    writer = TenantRegistry(tmp_path / "tenants.json", encryption_key=fernet_key)
    writer.create_tenant("t1", "free", "T1")

    reader = TenantRegistry(tmp_path / "tenants.json", encryption_key=other_key)
    with pytest.raises(ValueError, match="failed to decrypt"):
        reader.load()


def test_encrypted_file_loaded_without_key_raises(
    tmp_path: Path, fernet_key: str
) -> None:
    """An encrypted file with a missing runtime key must fail loudly
    rather than be silently treated as malformed JSON — the operator
    needs to know they forgot to set the env var.
    """

    writer = TenantRegistry(tmp_path / "tenants.json", encryption_key=fernet_key)
    writer.create_tenant("t1", "free", "T1")

    reader = TenantRegistry(tmp_path / "tenants.json")  # no key
    with pytest.raises(RuntimeError, match="LUVOIRE_TENANT_REGISTRY_KEY"):
        reader.load()


def test_format_autodetect_falls_through_for_plaintext_after_encrypted(
    tmp_path: Path, fernet_key: str
) -> None:
    """If a deploy rolls forward to encryption then a fallback writer
    overwrites with plaintext, the next encrypted-mode reader must
    still parse the plaintext (auto-detect via prefix), so a partial
    rollout doesn't wedge the registry.
    """

    plain = TenantRegistry(tmp_path / "tenants.json")
    plain.create_tenant("t1", "free", "T1")
    encrypted = TenantRegistry(
        tmp_path / "tenants.json", encryption_key=fernet_key
    )
    payload = encrypted.load()
    assert payload["tenants"]["t1"]["display_name"] == "T1"


def test_environment_variable_picks_up_key(
    tmp_path: Path,
    fernet_key: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LUVOIRE_TENANT_REGISTRY_KEY", fernet_key)
    registry = TenantRegistry(tmp_path / "tenants.json")
    assert registry.encryption_enabled is True


def test_blank_environment_value_treated_as_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``LUVOIRE_TENANT_REGISTRY_KEY=""`` must NOT silently switch
    encrypted mode on/off — empty / whitespace counts as unset.
    """

    monkeypatch.setenv("LUVOIRE_TENANT_REGISTRY_KEY", "   ")
    registry = TenantRegistry(tmp_path / "tenants.json")
    assert registry.encryption_enabled is False
