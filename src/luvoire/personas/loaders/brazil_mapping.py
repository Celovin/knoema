"""Brazil mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "fundamental": 2,
    "medio": 3,
    "tecnico": 4,
    "superior": 6,
    "pos_graduacao": 7,
}
OCCUPATION_ISCO08 = {
    "gerente": "1",
    "profissional": "2",
    "tecnico": "3",
    "servicos": "5",
    "agricultura": "6",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "solteiro": "single",
    "casado": "married",
    "divorciado": "divorced",
    "viuvo": "widowed",
    "single": "single",
    "married": "married",
}

CONFIG = CountryConfig(
    iso="BRA",
    hf_id="nvidia/Nemotron-Personas-Brazil",
    local_dir_name="nemotron-personas-brazil",
    language_locale="pt-BR",
    population_source="Brazil census-grounded public demographic distributions",
    record_count="6M upstream; fixture 100 rows",
    grounding_version="hf-main",
    region_l1_fields=("state",),
    region_l2_fields=("city", "municipality"),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
    country_specific_fields=("cbo_code",),
)
