"""Configuration loading helpers for Luvoire."""

from __future__ import annotations

import os
import warnings
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

_WARNED_LEGACY_ENV_VARS: set[str] = set()


class LLMConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_provider: Literal["anthropic", "openai", "local"] = "anthropic"
    fallback_order: tuple[Literal["anthropic", "openai", "local"], ...] = ("openai", "local")
    anthropic_model: str = "claude-3-7-sonnet-latest"
    openai_model: str = "gpt-5"
    openai_base_url: str | None = None
    local_model: str = "llama3.1:8b"
    default_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=1024, gt=0)
    request_timeout_seconds: float = Field(default=60.0, gt=0.0)


class MemoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    short_term_capacity: int = Field(default=50, ge=1)
    retrieval_limit: int = Field(default=5, ge=1)
    recency_bias: float = Field(default=0.3, ge=0.0, le=1.0)
    summarization_interval: int = Field(default=50, ge=1)
    sqlite_path: str = "var/luvoire.sqlite3"


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tick_duration_minutes: int = Field(default=30, ge=1)
    timezone: str = "Asia/Seoul"
    locale: str = "ko-KR"


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    level: str = "INFO"
    json_output: bool = Field(default=False, alias="json")


class LuvoireConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def _load_yaml_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError(f"Config file must contain a mapping at the root: {path}")
    return dict(raw)


def _deep_set(target: dict[str, Any], path: list[str], value: Any) -> None:
    current = target
    for key in path[:-1]:
        nested = current.get(key)
        if not isinstance(nested, dict):
            nested = {}
            current[key] = nested
        current = nested
    current[path[-1]] = value


def _apply_env_overrides(
    payload: dict[str, Any],
    *,
    env_prefix: str,
    environ: Mapping[str, str],
    legacy_env_prefix: str | None = None,
) -> dict[str, Any]:
    merged = dict(payload)
    prefixes = ((legacy_env_prefix, True), (env_prefix, False))
    for prefix, legacy in prefixes:
        if prefix is None:
            continue
        for key, raw_value in environ.items():
            if not key.startswith(prefix):
                continue
            if legacy and f"{env_prefix}{key.removeprefix(prefix)}" in environ:
                continue
            if legacy:
                _warn_legacy_env(key, f"{env_prefix}{key.removeprefix(prefix)}")
            path = key.removeprefix(prefix).lower().split("__")
            normalized_path = [segment.replace("-", "_") for segment in path if segment]
            if not normalized_path:
                continue
            _deep_set(merged, normalized_path, yaml.safe_load(raw_value))
    return merged


def get_env(
    new_name: str,
    old_name: str | None = None,
    default: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str | None:
    env = os.environ if environ is None else environ
    value = env.get(new_name)
    if value is not None:
        return value
    if old_name is not None:
        legacy = env.get(old_name)
        if legacy is not None:
            _warn_legacy_env(old_name, new_name)
            return legacy
    return default


def _warn_legacy_env(old_name: str, new_name: str) -> None:
    if old_name in _WARNED_LEGACY_ENV_VARS:
        return
    warnings.warn(
        f"{old_name} is deprecated; use {new_name}",
        DeprecationWarning,
        stacklevel=3,
    )
    _WARNED_LEGACY_ENV_VARS.add(old_name)


def load_config(
    path: str | Path | None = None,
    *,
    env_prefix: str = "LUVOIRE_",
    environ: Mapping[str, str] | None = None,
) -> LuvoireConfig:
    """Load config from YAML first, then overlay environment variables."""

    config_path = Path(path) if path is not None else None
    payload = _load_yaml_payload(config_path)
    resolved_environ = os.environ if environ is None else environ
    merged = _apply_env_overrides(
        payload,
        env_prefix=env_prefix,
        environ=resolved_environ,
        legacy_env_prefix="KNOEMA_" if env_prefix == "LUVOIRE_" else None,
    )
    return LuvoireConfig.model_validate(merged)


__all__ = [
    "LLMConfig",
    "LoggingConfig",
    "LuvoireConfig",
    "MemoryConfig",
    "RuntimeConfig",
    "get_env",
    "load_config",
]
