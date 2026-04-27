"""Tests for luvoire.demography.byod — aggregate-only BYOD validator."""

from __future__ import annotations

import pytest

from luvoire.demography.byod import (
    MIN_AGGREGATION_FLOOR,
    REQUIRED_COLUMNS,
    ByodValidationIssue,
    assert_aggregate_byod,
    validate_aggregate_byod,
)


def _valid_record(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "admin_code": "11680",
        "year": 2024,
        "population": 540_000,
    }
    base.update(overrides)
    return base


# --- Schema requirements -------------------------------------------------


def test_missing_admin_code_column_is_rejected() -> None:
    record = {"year": 2024, "population": 100_000}
    issues = validate_aggregate_byod([record])
    assert any(i.code == "missing_required_column" and i.column == "admin_code" for i in issues)


def test_missing_population_column_is_rejected() -> None:
    record = {"admin_code": "11680", "year": 2024}
    issues = validate_aggregate_byod([record])
    assert any(i.code == "missing_required_column" and i.column == "population" for i in issues)


def test_required_columns_set_is_minimal() -> None:
    """Sanity check — required schema is admin_code / year / population."""

    assert frozenset({"admin_code", "year", "population"}) == REQUIRED_COLUMNS


def test_required_column_check_is_case_insensitive() -> None:
    record = {"Admin_Code": "11680", "Year": 2024, "Population": 100_000}
    issues = validate_aggregate_byod([record])
    schema_issues = [i for i in issues if i.code == "missing_required_column"]
    assert schema_issues == []


# --- Forbidden columns ---------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_col",
    [
        "rrn",
        "ssn",
        "phone",
        "email",
        "passport_number",
        "license_plate",
        "imei",
        "fname",
        "firstname",
    ],
)
def test_individual_identifier_column_is_rejected(forbidden_col: str) -> None:
    record = _valid_record()
    record[forbidden_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_individual_column" and forbidden_col in (i.column or "")
        for i in issues
    )


@pytest.mark.parametrize(
    "forbidden_col",
    [
        "lat",
        "lon",
        "latitude",
        "longitude",
        "epsg",
        "geometry",
        "polygon",
        "wkt",
        "h3",
        "geohash",
        "zip",
        "zipcode",
        "postal_code",
        "jibun",
    ],
)
def test_geometry_column_is_rejected(forbidden_col: str) -> None:
    record = _valid_record()
    record[forbidden_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_geometry_column" and forbidden_col in (i.column or "")
        for i in issues
    )


def test_safe_aggregate_columns_are_allowed() -> None:
    record = _valid_record(
        sigungu_label="강남구",
        male_count=270_000,
        female_count=270_000,
        median_age=42.5,
    )
    issues = validate_aggregate_byod([record])
    forbidden_codes = {
        "forbidden_individual_column",
        "forbidden_geometry_column",
    }
    assert all(i.code not in forbidden_codes for i in issues)


# --- Aggregation floor ---------------------------------------------------


def test_population_below_aggregation_floor_is_rejected() -> None:
    record = _valid_record(population=500)
    issues = validate_aggregate_byod([record])
    assert any(i.code == "below_aggregation_floor" for i in issues)


def test_population_at_aggregation_floor_is_allowed() -> None:
    record = _valid_record(population=MIN_AGGREGATION_FLOOR)
    issues = validate_aggregate_byod([record])
    assert all(i.code != "below_aggregation_floor" for i in issues)


def test_aggregation_floor_overridable() -> None:
    record = _valid_record(population=5_000)
    issues = validate_aggregate_byod([record], min_aggregation_floor=1_000)
    assert all(i.code != "below_aggregation_floor" for i in issues)


def test_aggregation_floor_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        validate_aggregate_byod([_valid_record()], min_aggregation_floor=0)


def test_non_numeric_population_is_rejected() -> None:
    record = _valid_record(population="lots")
    issues = validate_aggregate_byod([record])
    assert any(i.code == "invalid_population" for i in issues)


# --- Admin code validation -----------------------------------------------


def test_admin_code_must_be_five_digits() -> None:
    record = _valid_record(admin_code="123")
    issues = validate_aggregate_byod([record])
    assert any(i.code == "invalid_admin_code" for i in issues)


def test_admin_code_must_be_string_not_int() -> None:
    record = _valid_record(admin_code=11680)
    issues = validate_aggregate_byod([record])
    assert any(i.code == "invalid_admin_code" for i in issues)


def test_admin_code_alphabetic_is_rejected() -> None:
    record = _valid_record(admin_code="ABCDE")
    issues = validate_aggregate_byod([record])
    assert any(i.code == "invalid_admin_code" for i in issues)


# --- Empty input + assert helper -----------------------------------------


def test_empty_input_yields_empty_input_issue() -> None:
    issues = validate_aggregate_byod([])
    assert len(issues) == 1
    assert issues[0].code == "empty_input"


def test_assert_aggregate_byod_raises_on_failure() -> None:
    record = _valid_record()
    record["rrn"] = "123456-1234567"
    with pytest.raises(ValueError, match="BYOD aggregate validation"):
        assert_aggregate_byod([record])


def test_assert_aggregate_byod_returns_silently_on_clean_records() -> None:
    record = _valid_record()
    # Should not raise.
    assert_aggregate_byod([record])


# --- Issue dataclass shape -----------------------------------------------


def test_byod_validation_issue_is_frozen() -> None:
    issue = ByodValidationIssue(
        code="x", column="y", row_index=0, message="z"
    )
    with pytest.raises(AttributeError):
        issue.code = "other"  # type: ignore[misc]


# --- Audit-1 hardening: camelCase + Korean + NaN/Inf ---------------------


@pytest.mark.parametrize(
    "camel_col",
    [
        "RRNumber",
        "passportNumber",
        "phoneNumber",
        "emailAddress",
        "homeAddress",
        "firstName",
        "lastName",
        "fullName",
        "macAddress",
    ],
)
def test_camelcase_individual_identifiers_are_rejected(camel_col: str) -> None:
    record = _valid_record()
    record[camel_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_individual_column" and i.column == camel_col
        for i in issues
    ), f"camelCase column {camel_col!r} must be rejected"


@pytest.mark.parametrize(
    "camel_col",
    [
        "latLng",
        "latLong",
        "roadAddress",
        "buildingNo",
        "buildingNumber",
        "zipCode",
        "postalCode",
    ],
)
def test_camelcase_geometry_columns_are_rejected(camel_col: str) -> None:
    record = _valid_record()
    record[camel_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_geometry_column" and i.column == camel_col
        for i in issues
    ), f"camelCase column {camel_col!r} must be rejected"


@pytest.mark.parametrize(
    "korean_col",
    [
        "주민등록번호",
        "주민번호",
        "전화번호",
        "휴대전화",
        "이메일",
        "주소",
        "성명",
        "이름",
        "여권번호",
        "생년월일",
    ],
)
def test_korean_individual_identifiers_are_rejected(korean_col: str) -> None:
    record = _valid_record()
    record[korean_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_individual_column" and i.column == korean_col
        for i in issues
    ), f"Korean column {korean_col!r} must be rejected"


@pytest.mark.parametrize(
    "korean_col",
    [
        "위도",
        "경도",
        "좌표",
        "도로명주소",
        "지번",
        "법정동",
        "행정동",
        "건물번호",
        "우편번호",
    ],
)
def test_korean_geometry_columns_are_rejected(korean_col: str) -> None:
    record = _valid_record()
    record[korean_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_geometry_column" and i.column == korean_col
        for i in issues
    ), f"Korean column {korean_col!r} must be rejected"


def test_population_nan_is_rejected() -> None:
    record = _valid_record(population=float("nan"))
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "invalid_population" and "finite" in i.message
        for i in issues
    )


def test_population_positive_inf_is_rejected() -> None:
    record = _valid_record(population=float("inf"))
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "invalid_population" and "finite" in i.message
        for i in issues
    )


def test_population_negative_inf_is_rejected() -> None:
    record = _valid_record(population=float("-inf"))
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "invalid_population" and "finite" in i.message
        for i in issues
    )


# --- Audit-2 hardening: critical-prefix bypass + numpy scalar -----------


@pytest.mark.parametrize(
    "suffix_col",
    [
        "rrnx",
        "rrn0",
        "rrnno",
        "ssnno",
        "passportcode",
        "imeino",
        "imei0",
        "udid0",
    ],
)
def test_critical_prefix_individual_suffix_bypass_blocked(suffix_col: str) -> None:
    """1-character / digit suffix on rrn / ssn / imei / udid / passport
    must not bypass the forbidden-individual filter.
    """

    record = _valid_record()
    record[suffix_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_individual_column" and i.column == suffix_col
        for i in issues
    ), f"suffix-bypass column {suffix_col!r} must still be rejected"


@pytest.mark.parametrize(
    "suffix_col",
    [
        "wkt0",
        "wktline",
        "wkbblob",
        "epsg0",
        "geohashbin",
        "pluscodearea",
    ],
)
def test_critical_prefix_geometry_suffix_bypass_blocked(suffix_col: str) -> None:
    """1-character / suffix bypass on wkt / wkb / epsg / geohash / pluscode
    must not bypass the forbidden-geometry filter.
    """

    record = _valid_record()
    record[suffix_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "forbidden_geometry_column" and i.column == suffix_col
        for i in issues
    ), f"suffix-bypass column {suffix_col!r} must still be rejected"


def test_population_numpy_int64_is_accepted() -> None:
    """numpy.int64 scalars (common from pandas DataFrame.to_dict)
    must be accepted as numeric population values.
    """

    np = pytest.importorskip("numpy")
    record = _valid_record(population=np.int64(540_000))
    issues = validate_aggregate_byod([record])
    assert all(i.code != "invalid_population" for i in issues)
    assert all(i.code != "below_aggregation_floor" for i in issues)


def test_population_numpy_float64_is_accepted() -> None:
    np = pytest.importorskip("numpy")
    record = _valid_record(population=np.float64(540_000.0))
    issues = validate_aggregate_byod([record])
    assert all(i.code != "invalid_population" for i in issues)


def test_population_numpy_nan_is_rejected() -> None:
    np = pytest.importorskip("numpy")
    record = _valid_record(population=np.float64(float("nan")))
    issues = validate_aggregate_byod([record])
    assert any(
        i.code == "invalid_population" and "finite" in i.message
        for i in issues
    )


# --- Audit-3 hardening: NFC normalization for NFD Hangul bypass ---------


def _to_nfd(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFD", s)


@pytest.mark.parametrize(
    "korean_individual",
    [
        "이메일",
        "주민번호",
        "전화번호",
        "성명",
        "여권번호",
    ],
)
def test_nfd_decomposed_korean_individual_is_rejected(korean_individual: str) -> None:
    """NFD-decomposed Hangul Jamo column names must still match the
    NFC-stored forbidden token set. Without canonical normalisation the
    Jamo split form silently bypasses ``_FORBIDDEN_INDIVIDUAL_TOKENS``.
    """

    nfd_col = _to_nfd(korean_individual)
    assert nfd_col != korean_individual, "input must actually decompose under NFD"
    record = _valid_record()
    record[nfd_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(i.code == "forbidden_individual_column" for i in issues), (
        f"NFD-decomposed {korean_individual!r} must still be rejected"
    )


@pytest.mark.parametrize(
    "korean_geometry",
    [
        "위도",
        "경도",
        "도로명주소",
        "법정동",
        "우편번호",
    ],
)
def test_nfd_decomposed_korean_geometry_is_rejected(korean_geometry: str) -> None:
    nfd_col = _to_nfd(korean_geometry)
    assert nfd_col != korean_geometry, "input must actually decompose under NFD"
    record = _valid_record()
    record[nfd_col] = "blocked"
    issues = validate_aggregate_byod([record])
    assert any(i.code == "forbidden_geometry_column" for i in issues), (
        f"NFD-decomposed {korean_geometry!r} must still be rejected"
    )
