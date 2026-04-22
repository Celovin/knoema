from __future__ import annotations

import importlib
import sys
import warnings


def test_import_knoema_warns_once_and_exposes_luvoire_version() -> None:
    sys.modules.pop("knoema", None)
    if hasattr(sys, "_luvoire_legacy_package_warned"):
        delattr(sys, "_luvoire_legacy_package_warned")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        legacy = importlib.import_module("knoema")

    import luvoire

    assert legacy.__version__ == luvoire.__version__
    assert len(caught) == 1
    assert caught[0].category is DeprecationWarning
    assert "deprecated" in str(caught[0].message)


def test_from_knoema_api_resolves_through_compat_package() -> None:
    sys.modules.pop("knoema", None)
    if hasattr(sys, "_luvoire_legacy_package_warned"):
        delattr(sys, "_luvoire_legacy_package_warned")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        legacy_api = importlib.import_module("knoema.api")

    import luvoire.api

    assert legacy_api.create_app is luvoire.api.create_app
