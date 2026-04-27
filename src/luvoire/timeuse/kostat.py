"""KOSTAT 생활시간조사 metadata registry (no microdata).

This module is intentionally a thin metadata-only registry. It exists so that
Tier B parameter declarations such as ``source: "KOSTAT 2024 Time Use Survey",
table_id: "T-08"`` can be cross-referenced against a known table id by
future tooling. The engine never bundles, downloads, or parses the
underlying microdata; that pipeline lives outside this repository.

License note: every registered table is a public statistical product
distributed under the Korean public-data licence ``KOGL Type 1`` (출처표시).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KostatTable:
    """A registered KOSTAT 생활시간조사 statistical table.

    Only metadata fields are kept — never the table contents. ``url`` is
    optional because KOSTAT's published-table URLs are not always stable
    across survey waves; the canonical join key for downstream tooling is
    ``(survey_year, table_id)``.
    """

    survey_year: int
    table_id: str
    description: str
    license: str
    url: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.survey_year, int):
            raise TypeError(
                f"survey_year must be int (got {type(self.survey_year).__name__})"
            )
        if self.survey_year < 1999 or self.survey_year > 2100:
            raise ValueError(
                f"survey_year out of plausible range (got {self.survey_year})"
            )
        if not isinstance(self.table_id, str) or not self.table_id:
            raise ValueError("table_id must be a non-empty string")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("description must be a non-empty string")
        if not isinstance(self.license, str) or not self.license:
            raise ValueError("license must be a non-empty string")
        if self.url is not None and (not isinstance(self.url, str) or not self.url):
            raise ValueError("url must be a non-empty string when provided")


REGISTERED_KOSTAT_TABLES: tuple[KostatTable, ...] = (
    KostatTable(
        survey_year=2024,
        table_id="T-08",
        description=(
            "Average minutes per day spent on each major activity, broken down "
            "by sex, age band, and day type (weekday/weekend/holiday)."
        ),
        license="KOGL Type 1",
    ),
    KostatTable(
        survey_year=2024,
        table_id="T-12",
        description=(
            "Activity participation rate and mean participant duration by "
            "occupation category and day type."
        ),
        license="KOGL Type 1",
    ),
    KostatTable(
        survey_year=2024,
        table_id="T-15",
        description=(
            "Daily time-use sequence transitions: aggregate counts of "
            "consecutive activity-pair transitions across the survey diary."
        ),
        license="KOGL Type 1",
    ),
)
"""Snapshot of known KOSTAT 생활시간조사 tables relevant to time-use priors."""

_TABLE_INDEX: dict[str, KostatTable] = {table.table_id: table for table in REGISTERED_KOSTAT_TABLES}


def lookup_kostat_table(table_id: str) -> KostatTable | None:
    """Return the registered :class:`KostatTable` for ``table_id`` or ``None``.

    Lookup is exact-match on ``table_id``; KOSTAT table identifiers are
    short ASCII strings (e.g. ``"T-08"``) and we do not normalise case.
    """

    if not isinstance(table_id, str):
        raise TypeError(f"table_id must be str (got {type(table_id).__name__})")
    return _TABLE_INDEX.get(table_id)
