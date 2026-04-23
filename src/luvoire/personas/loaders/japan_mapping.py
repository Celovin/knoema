"""Japan mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "secondary": 3,
    "vocational": 4,
    "junior_college": 5,
    "university": 6,
    "graduate": 7,
}
OCCUPATION_ISCO08 = {
    "manager": "1",
    "professional": "2",
    "clerical": "4",
    "service": "5",
    "craft": "7",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "single": "single",
    "married": "married",
    "divorced": "divorced",
    "widowed": "widowed",
}

CONFIG = CountryConfig(
    iso="JPN",
    hf_id="nvidia/Nemotron-Personas-Japan",
    local_dir_name="nemotron-personas-japan",
    language_locale="ja-JP",
    population_source="Japan census-grounded public demographic distributions",
    record_count="6M upstream; fixture 100 rows",
    grounding_version="hf-main",
    region_l1_fields=("prefecture", "state"),
    region_l2_fields=("city", "ward"),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
)
