"""Korea mapping tables.

source: UNESCO ISCED-2011 level descriptions, ILO ISCO-08 major groups, and
OECD income-quintile convention.
"""

from __future__ import annotations

from luvoire.personas.loaders.nemotron_base import CountryConfig

EDUCATION_ISCED = {
    "고등학교": 3,
    "전문대학": 5,
    "4년제 대학교": 6,
    "대학원": 7,
    "high_school": 3,
    "bachelors": 6,
    "graduate": 7,
}
OCCUPATION_ISCO08 = {
    "관리자": "1",
    "전문가": "2",
    "사무 종사자": "4",
    "서비스 종사자": "5",
    "경영 컨설턴트": "2",
    "정보 시스템 운영자": "3",
    "소규모 상점 경영자": "1",
}
INCOME_BRACKET = {"q1": "q1", "q2": "q2", "q3": "q3", "q4": "q4", "q5": "q5"}
MARITAL_STATUS = {
    "미혼": "single",
    "배우자있음": "married",
    "이혼": "divorced",
    "사별": "widowed",
    "single": "single",
    "married": "married",
}

CONFIG = CountryConfig(
    iso="KOR",
    hf_id="nvidia/Nemotron-Personas-Korea",
    local_dir_name="nemotron-personas-korea",
    language_locale="ko-KR",
    population_source="KOSIS and Korean public-statistics grounded distributions",
    record_count="6M upstream; fixture 100 rows",
    grounding_version="0381f03a403df78a7998000f8b11705635b654fd",
    region_l1_fields=("province",),
    region_l2_fields=("district",),
    education_isced=EDUCATION_ISCED,
    occupation_isco08=OCCUPATION_ISCO08,
    income_bracket=INCOME_BRACKET,
    marital_status=MARITAL_STATUS,
    country_specific_fields=("honorific_style", "military_status"),
)
