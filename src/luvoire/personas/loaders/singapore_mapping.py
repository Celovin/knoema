"""Singapore mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "primary": 1,
    "secondary": 3,
    "polytechnic": 5,
    "university": 6,
    "postgraduate": 7,
}
OCCUPATION_ISCO08 = {
    "senior official or manager": "1",
    "professional": "2",
    "clerical worker": "4",
    "service worker": "5",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "single": "single",
    "married": "married",
    "divorced": "divorced",
    "widowed": "widowed",
}

CONFIG = CountryConfig(
    iso="SGP",
    hf_id="nvidia/Nemotron-Personas-Singapore",
    local_dir_name="nemotron-personas-singapore",
    language_locale="en-SG",
    population_source="Singapore planning-area public demographic distributions",
    record_count="888K upstream; fixture 100 rows",
    grounding_version="hf-main",
    region_l1_fields=("planning_area",),
    region_l2_fields=("subzone",),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
    country_specific_fields=("ethnicity", "industry"),
)
