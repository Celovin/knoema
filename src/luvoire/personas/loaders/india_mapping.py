"""India mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "primary": 1,
    "secondary": 3,
    "higher_secondary": 3,
    "diploma": 5,
    "bachelors": 6,
    "masters": 7,
    "doctorate": 8,
}
OCCUPATION_ISCO08 = {
    "manager": "1",
    "professional": "2",
    "technician": "3",
    "clerical": "4",
    "service": "5",
    "agriculture": "6",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "single": "single",
    "married": "married",
    "divorced": "divorced",
    "widowed": "widowed",
}

CONFIG = CountryConfig(
    iso="IND",
    hf_id="nvidia/Nemotron-Personas-India",
    local_dir_name="nemotron-personas-india",
    language_locale="hi-IN-Deva",
    population_source="India census-grounded public demographic distributions",
    record_count="21M upstream; fixture 100 rows",
    grounding_version="hf-main",
    region_l1_fields=("state",),
    region_l2_fields=("district", "city"),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
    country_specific_fields=("religion", "script_variant"),
)
