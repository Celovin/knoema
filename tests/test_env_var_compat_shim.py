from __future__ import annotations

import warnings

import luvoire.config as config
from luvoire.config import get_env


def test_get_env_prefers_new_var_without_warning() -> None:
    config._WARNED_LEGACY_ENV_VARS.clear()
    env = {"LUVOIRE_METRICS_ENABLED": "1", "KNOEMA_METRICS_ENABLED": "0"}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = get_env(
            "LUVOIRE_METRICS_ENABLED",
            "KNOEMA_METRICS_ENABLED",
            environ=env,
        )

    assert value == "1"
    assert caught == []


def test_get_env_reads_old_var_with_deprecation_warning() -> None:
    config._WARNED_LEGACY_ENV_VARS.clear()
    env = {"KNOEMA_METRICS_ENABLED": "1"}

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = get_env(
            "LUVOIRE_METRICS_ENABLED",
            "KNOEMA_METRICS_ENABLED",
            environ=env,
        )

    assert value == "1"
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert "KNOEMA_METRICS_ENABLED is deprecated" in str(caught[0].message)


def test_get_env_defaults_when_both_missing() -> None:
    config._WARNED_LEGACY_ENV_VARS.clear()
    value = get_env(
        "LUVOIRE_METRICS_ENABLED",
        "KNOEMA_METRICS_ENABLED",
        "0",
        environ={},
    )

    assert value == "0"
