"""Tests for :mod:`luvoire.timeuse.kostat`."""

from __future__ import annotations

import pytest

from luvoire.timeuse.kostat import (
    REGISTERED_KOSTAT_TABLES,
    KostatTable,
    lookup_kostat_table,
)


def test_registry_has_at_least_three_tables() -> None:
    assert len(REGISTERED_KOSTAT_TABLES) >= 3


def test_registry_table_ids_unique() -> None:
    ids = [table.table_id for table in REGISTERED_KOSTAT_TABLES]
    assert len(set(ids)) == len(ids)


def test_registry_uses_kogl_type_1_license() -> None:
    for table in REGISTERED_KOSTAT_TABLES:
        assert table.license == "KOGL Type 1"


def test_lookup_known_table_returns_entry() -> None:
    found = lookup_kostat_table("T-08")
    assert found is not None
    assert found.table_id == "T-08"
    assert found.survey_year == 2024


def test_lookup_unknown_table_returns_none() -> None:
    assert lookup_kostat_table("T-9999") is None


def test_lookup_case_sensitive() -> None:
    # Lookups are exact-match; lower-case form should not resolve.
    assert lookup_kostat_table("t-08") is None


def test_lookup_rejects_non_string_arg() -> None:
    with pytest.raises(TypeError, match="str"):
        lookup_kostat_table(8)  # type: ignore[arg-type]


def test_kostat_table_rejects_empty_table_id() -> None:
    with pytest.raises(ValueError, match="table_id"):
        KostatTable(
            survey_year=2024,
            table_id="",
            description="x",
            license="KOGL Type 1",
        )


def test_kostat_table_rejects_year_out_of_range() -> None:
    with pytest.raises(ValueError, match="survey_year"):
        KostatTable(
            survey_year=1500,
            table_id="T-99",
            description="x",
            license="KOGL Type 1",
        )
