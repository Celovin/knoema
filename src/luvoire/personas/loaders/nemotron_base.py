"""Shared helpers for Nemotron-Personas loaders."""

from __future__ import annotations

import hashlib
import importlib
import json
import logging
import os
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from luvoire.personas.lpi import BIG5_KEY, COUNTRY_ISO, SEX, LPIPersona

LOGGER = logging.getLogger(__name__)
_ATTRIBUTION_LOGGED: set[str] = set()
_BLUE_SHIFT_KEYWORDS = (
    "campaign",
    "election",
    "political",
    "party",
    "ideology",
    "policy",
    "voter",
    "vote",
)


@dataclass(frozen=True, slots=True)
class CountryConfig:
    iso: COUNTRY_ISO
    hf_id: str
    local_dir_name: str
    language_locale: str
    population_source: str
    record_count: str
    grounding_version: str
    region_l1_fields: tuple[str, ...]
    region_l2_fields: tuple[str, ...]
    education_isced: Mapping[str, int]
    occupation_isco08: Mapping[str, str]
    income_bracket: Mapping[str, str]
    marital_status: Mapping[str, str]
    country_specific_fields: tuple[str, ...] = ()
    license: str = "CC-BY-4.0"


def iter_country_personas(config: CountryConfig) -> Iterator[LPIPersona]:
    _log_attribution_once(config)
    for row in load_parquet_shards(_source_for_config(config)):
        yield row_to_lpi(row, config)


def load_parquet_shards(path_or_hf_id: str | Path) -> Iterator[Mapping[str, Any]]:
    source = Path(path_or_hf_id) if not isinstance(path_or_hf_id, Path) else path_or_hf_id
    if source.exists():
        files = [source] if source.is_file() else sorted(source.glob("*.parquet"))
        if files:
            for file_path in files:
                yield from _read_parquet(file_path)
            return
        jsonl_files = sorted(source.glob("*.jsonl"))
        for file_path in jsonl_files:
            yield from _read_jsonl(file_path)
        return

    datasets = _import_optional("datasets", "personas")
    loaded = datasets.load_dataset(str(path_or_hf_id), split="train", streaming=True)
    yield from loaded


def row_to_lpi(row: Mapping[str, Any], config: CountryConfig) -> LPIPersona:
    used = {
        "uuid",
        "persona_id",
        "age",
        "sex",
        "gender",
        "persona",
        "narrative_text",
        "marital_status",
        "education_level",
        "education",
        "occupation",
        "income",
        "income_bracket",
        "household_size",
        "family_type",
        "big5",
        *config.region_l1_fields,
        *config.region_l2_fields,
    }
    narrative = _first_text(row, ("persona", "narrative_text", "cultural_background"))
    return LPIPersona(
        persona_id=_persona_id(row),
        country_iso=config.iso,
        language_locale=_first_text(row, ("language_locale",), default=config.language_locale),
        age=_coerce_int(row.get("age")),
        sex=_map_sex(row.get("sex") or row.get("gender")),
        region_l1=_first_text_or_none(row, config.region_l1_fields),
        region_l2=_first_text_or_none(row, config.region_l2_fields),
        education_isced=_map_lookup(row, config.education_isced, ("education_level", "education")),
        occupation_isco08=_map_lookup(row, config.occupation_isco08, ("occupation",)),
        income_bracket_oecd=_map_lookup(row, config.income_bracket, ("income_bracket", "income")),
        household_size=_household_size(row),
        marital_status=_map_lookup(row, config.marital_status, ("marital_status",)),
        big5=_big5(row.get("big5")),
        narrative_text=narrative,
        grounding_source=f"{config.hf_id}@{config.grounding_version}",
        grounding_version=config.grounding_version,
        distortion_flags=_distortion_flags(narrative),
        extras={str(key): value for key, value in row.items() if key not in used},
    )


def _source_for_config(config: CountryConfig) -> str | Path:
    fixture_root = os.environ.get("LUVOIRE_PERSONAS_FIXTURE_ROOT")
    if fixture_root:
        root = Path(fixture_root)
        for candidate in (root / config.iso, root / config.iso.lower(), root / config.local_dir_name):
            if candidate.exists():
                return candidate
    data_root = Path(os.environ.get("LUVOIRE_PERSONAS_DATA_ROOT", r"D:\datasets"))
    local_candidate = data_root / config.local_dir_name
    return local_candidate if local_candidate.exists() else config.hf_id


def _log_attribution_once(config: CountryConfig) -> None:
    if config.iso in _ATTRIBUTION_LOGGED:
        return
    LOGGER.info(
        "Nemotron-Personas %s source %s license %s; cite NVIDIA Nemotron-Personas.",
        config.iso,
        config.hf_id,
        config.license,
    )
    _ATTRIBUTION_LOGGED.add(config.iso)


def _reset_attribution_log_for_tests() -> None:
    _ATTRIBUTION_LOGGED.clear()


def _read_parquet(path: Path) -> Iterator[Mapping[str, Any]]:
    parquet = _import_optional("pyarrow.parquet", "personas")
    table = parquet.read_table(path)
    yield from table.to_pylist()


def _read_jsonl(path: Path) -> Iterator[Mapping[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    yield payload


def _import_optional(module_name: str, extra_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise ImportError(f"Install luvoire[{extra_name}] to load persona datasets.") from exc


def _persona_id(row: Mapping[str, Any]) -> str:
    for key in ("uuid", "persona_id"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    encoded = json.dumps(dict(row), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:32]


def _first_text(
    row: Mapping[str, Any],
    keys: tuple[str, ...],
    *,
    default: str = "",
) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def _first_text_or_none(row: Mapping[str, Any], keys: tuple[str, ...]) -> str | None:
    value = _first_text(row, keys)
    return value or None


def _coerce_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _map_sex(value: Any) -> SEX | None:
    text = str(value or "").strip().lower()
    if text in {"f", "female", "woman", "\uc5ec\uc790", "femme", "feminino"}:
        return "F"
    if text in {"m", "male", "man", "\ub0a8\uc790", "homme", "masculino"}:
        return "M"
    if text in {"x", "other", "nonbinary", "non-binary"}:
        return "X"
    return None


def _map_lookup(
    row: Mapping[str, Any],
    mapping: Mapping[str, Any],
    keys: tuple[str, ...],
) -> Any | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip().lower()
        if text in mapping:
            return mapping[text]
    return None


def _household_size(row: Mapping[str, Any]) -> int | None:
    explicit = _coerce_int(row.get("household_size"))
    if explicit is not None:
        return explicit
    family = str(row.get("family_type") or "").lower()
    if any(token in family for token in ("alone", "solo", "\ud63c\uc790", "single-person")):
        return 1
    if family:
        return 2
    return None


def _big5(value: Any) -> Mapping[BIG5_KEY, float] | None:
    if not isinstance(value, Mapping):
        return None
    keys: tuple[BIG5_KEY, ...] = ("O", "C", "E", "A", "N")
    parsed: dict[BIG5_KEY, float] = {}
    for key in keys:
        if key in value:
            parsed[key] = float(value[key])
    return parsed if set(parsed) == set(keys) else None


def _distortion_flags(narrative: str) -> tuple[str, ...]:
    flags = ["llm_narrative_synthetic"]
    lowered = narrative.lower()
    if any(keyword in lowered for keyword in _BLUE_SHIFT_KEYWORDS):
        flags.append("blue_shift_risk")
    return tuple(flags)


__all__ = [
    "CountryConfig",
    "iter_country_personas",
    "load_parquet_shards",
    "row_to_lpi",
]
