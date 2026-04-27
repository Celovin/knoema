"""KOSIS demographic statistics metadata registry (no microdata).

This module is intentionally a thin metadata-only registry mirroring the
``luvoire.timeuse.kostat`` pattern. It exists so that Tier B parameter
declarations such as ``source: "KOSIS 출생통계", table_id: "1B36E27"`` can
be cross-referenced against a known table id by future tooling. The engine
never bundles, downloads, or parses the underlying microdata; that
pipeline lives outside this repository.

Civilian Use Policy alignment
-----------------------------
This registry covers **aggregate population statistics only** (fertility,
mortality, migration, age-sex pyramids, projected populations) at 시군구
or higher administrative aggregation level. It does not include any
individual-level data, any per-person identifiers, or any sub-시군구
geometry. Outputs informed by these tables are projections / counterfactual
scenarios, not predictions of individual outcomes.

License note: every registered table is a public statistical product
distributed under the Korean public-data licence ``KOGL Type 1`` (출처
표시) and may be used commercially with attribution.
"""

from __future__ import annotations

from dataclasses import dataclass

KosisDataKind = str
"""Closed string set: ``fertility`` | ``mortality`` | ``migration``
   | ``population_pyramid`` | ``projection``.

We keep this as ``str`` rather than ``Literal`` so the registry can grow
without rippling into the type aliases of every consumer.
"""

_VALID_KINDS: frozenset[str] = frozenset(
    {
        "fertility",
        "mortality",
        "migration",
        "population_pyramid",
        "projection",
    }
)


@dataclass(frozen=True, slots=True)
class KosisTable:
    """A registered KOSIS demographic statistics table.

    Only metadata fields are kept — never the table contents. The canonical
    join key for downstream tooling is ``(publisher, table_id)``; KOSIS
    table identifiers (e.g. ``"1B36E27"``) are stable across releases for
    a given ``publisher`` (``KOSTAT`` for 통계청, ``MOIS`` for 행정안전부
    주민등록인구).

    Attributes:
        publisher: Issuing agency (``KOSTAT``, ``MOIS``, etc.).
        table_id: Stable KOSIS identifier (e.g. ``1B36E27``).
        kind: One of :data:`_VALID_KINDS`.
        description: Free-text description of the table content.
        aggregation_floor: Minimum administrative aggregation level
            (e.g. ``시군구``, ``시도``, ``전국``). Sub-시군구 granularity is
            never registered here — those tables would violate the
            aggregate-only floor of this registry.
        license: Korean public-data licence (typically ``KOGL Type 1``).
        url: Optional reference URL. KOSIS URLs are not always stable
            across waves; ``(publisher, table_id)`` is the canonical join.
    """

    publisher: str
    table_id: str
    kind: KosisDataKind
    description: str
    aggregation_floor: str
    license: str
    url: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.publisher, str) or not self.publisher:
            raise ValueError("publisher must be a non-empty string")
        if not isinstance(self.table_id, str) or not self.table_id:
            raise ValueError("table_id must be a non-empty string")
        if self.kind not in _VALID_KINDS:
            raise ValueError(
                f"unknown kind {self.kind!r}; expected one of {sorted(_VALID_KINDS)}"
            )
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("description must be a non-empty string")
        if not isinstance(self.aggregation_floor, str) or not self.aggregation_floor:
            raise ValueError("aggregation_floor must be a non-empty string")
        if self.aggregation_floor not in {"시군구", "시도", "전국"}:
            raise ValueError(
                f"aggregation_floor must be one of 시군구|시도|전국 "
                f"(got {self.aggregation_floor!r}); sub-시군구 levels are "
                "never registered here"
            )
        if not isinstance(self.license, str) or not self.license:
            raise ValueError("license must be a non-empty string")
        if self.url is not None and (not isinstance(self.url, str) or not self.url):
            raise ValueError("url must be a non-empty string when provided")


REGISTERED_KOSIS_TABLES: tuple[KosisTable, ...] = (
    KosisTable(
        publisher="KOSTAT",
        table_id="1B36E27",
        kind="fertility",
        description=(
            "출생통계. Annual live births and crude/age-specific fertility rates "
            "by sex of newborn and age of mother, aggregated to 시군구."
        ),
        aggregation_floor="시군구",
        license="KOGL Type 1",
    ),
    KosisTable(
        publisher="KOSTAT",
        table_id="1B40E04",
        kind="mortality",
        description=(
            "사망원인통계 / 생명표. Annual deaths, age-specific death rates, "
            "and life expectancy by sex, aggregated to 시군구 / 시도."
        ),
        aggregation_floor="시군구",
        license="KOGL Type 1",
    ),
    KosisTable(
        publisher="KOSTAT",
        table_id="1B26001",
        kind="migration",
        description=(
            "국내인구이동통계. Annual inter-시군구 net migration counts by "
            "sex and age band."
        ),
        aggregation_floor="시군구",
        license="KOGL Type 1",
    ),
    KosisTable(
        publisher="MOIS",
        table_id="1B040A3",
        kind="population_pyramid",
        description=(
            "주민등록인구현황. Resident registration population pyramid by "
            "single year of age and sex, aggregated to 시군구."
        ),
        aggregation_floor="시군구",
        license="KOGL Type 1",
    ),
    KosisTable(
        publisher="KOSTAT",
        table_id="1BPB003",
        kind="projection",
        description=(
            "장래인구추계 (시도편). KOSTAT canonical 30-year demographic "
            "projection in low / medium / high fertility scenarios. "
            "Reference for legitimate demographic projection methodology."
        ),
        aggregation_floor="시도",
        license="KOGL Type 1",
    ),
)
"""Snapshot of known KOSIS demographic-statistics tables relevant to the
:mod:`luvoire.demography` module. All entries are aggregate-floor 시군구
or above; sub-시군구 microdata are deliberately excluded.
"""


_TABLE_INDEX: dict[tuple[str, str], KosisTable] = {
    (table.publisher, table.table_id): table for table in REGISTERED_KOSIS_TABLES
}


def lookup_kosis_table(publisher: str, table_id: str) -> KosisTable | None:
    """Return the registered :class:`KosisTable` for ``(publisher, table_id)`` or ``None``.

    Lookup is exact-match on both fields. KOSIS table ids are short ASCII
    strings (e.g. ``"1B36E27"``); we do not normalise case.
    """

    if not isinstance(publisher, str):
        raise TypeError(f"publisher must be str (got {type(publisher).__name__})")
    if not isinstance(table_id, str):
        raise TypeError(f"table_id must be str (got {type(table_id).__name__})")
    return _TABLE_INDEX.get((publisher, table_id))


def tables_by_kind(kind: KosisDataKind) -> tuple[KosisTable, ...]:
    """Return all registered tables with the given :class:`KosisDataKind`."""

    if kind not in _VALID_KINDS:
        raise ValueError(
            f"unknown kind {kind!r}; expected one of {sorted(_VALID_KINDS)}"
        )
    return tuple(table for table in REGISTERED_KOSIS_TABLES if table.kind == kind)


__all__ = [
    "REGISTERED_KOSIS_TABLES",
    "KosisDataKind",
    "KosisTable",
    "lookup_kosis_table",
    "tables_by_kind",
]
