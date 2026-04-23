"""USA mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "less_than_high_school": 2,
    "high_school": 3,
    "some_college": 4,
    "associates": 5,
    "bachelors": 6,
    "masters": 7,
    "doctorate": 8,
}
OCCUPATION_ISCO08 = {
    "manager": "1",
    "fast_food_or_counter_worker": "5",
    "computer_or_information_research_scientist": "2",
    "community_finance_volunteer": "4",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "never_married": "single",
    "single": "single",
    "married": "married",
    "divorced": "divorced",
    "widowed": "widowed",
}

CONFIG = CountryConfig(
    iso="USA",
    hf_id="nvidia/Nemotron-Personas-USA",
    local_dir_name="nemotron-personas-usa",
    language_locale="en-US",
    population_source="US Census ACS/PUMS-derived public distributions",
    record_count="6M upstream; fixture 100 rows",
    grounding_version="hf-main",
    region_l1_fields=("state",),
    region_l2_fields=("city", "zipcode"),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
)
