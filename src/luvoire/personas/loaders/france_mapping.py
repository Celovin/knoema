"""France mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "college": 2,
    "lycee": 3,
    "bac": 3,
    "bts": 5,
    "licence": 6,
    "master": 7,
    "doctorat": 8,
}
OCCUPATION_ISCO08 = {
    "cadre": "1",
    "professionnel": "2",
    "technicien": "3",
    "employe": "4",
    "service": "5",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "celibataire": "single",
    "marie": "married",
    "divorce": "divorced",
    "veuf": "widowed",
    "single": "single",
    "married": "married",
}

CONFIG = CountryConfig(
    iso="FRA",
    hf_id="nvidia/Nemotron-Personas-France",
    local_dir_name="nemotron-personas-france",
    language_locale="fr-FR",
    population_source="France public demographic distributions, adult-only upstream rows",
    record_count="1M upstream; fixture 100 rows",
    grounding_version="hf-main",
    region_l1_fields=("region",),
    region_l2_fields=("department", "city"),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
    country_specific_fields=("department_code",),
)
