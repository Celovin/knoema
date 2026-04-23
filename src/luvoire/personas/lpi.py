"""Luvoire Persona Interface v1.

LPI v1 preserves country-specific Nemotron fields in ``extras`` while exposing
the shared demographic and narrative fields needed for deterministic simulation
and cross-country analysis.
"""

from __future__ import annotations

import json
import types
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Literal, TypeAlias, Union, get_args, get_origin, get_type_hints

COUNTRY_ISO: TypeAlias = Literal["USA", "JPN", "IND", "BRA", "SGP", "FRA", "KOR"]
SEX: TypeAlias = Literal["F", "M", "X"]
INCOME_BRACKET: TypeAlias = Literal["q1", "q2", "q3", "q4", "q5"]
MARITAL_STATUS: TypeAlias = Literal["single", "married", "divorced", "widowed", "other"]
BIG5_KEY: TypeAlias = Literal["O", "C", "E", "A", "N"]


@dataclass(frozen=True, slots=True)
class LPIPersona:
    persona_id: str
    country_iso: COUNTRY_ISO
    language_locale: str
    age: int | None
    sex: SEX | None
    region_l1: str | None
    region_l2: str | None
    education_isced: int | None
    occupation_isco08: str | None
    income_bracket_oecd: INCOME_BRACKET | None
    household_size: int | None
    marital_status: MARITAL_STATUS | None
    big5: Mapping[BIG5_KEY, float] | None
    narrative_text: str
    grounding_source: str
    grounding_version: str
    distortion_flags: tuple[str, ...] = ()
    extras: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["distortion_flags"] = list(self.distortion_flags)
        payload["extras"] = dict(self.extras)
        payload["big5"] = dict(self.big5) if self.big5 is not None else None
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> LPIPersona:
        values = dict(payload)
        flags = values.get("distortion_flags", ())
        values["distortion_flags"] = tuple(str(flag) for flag in flags)
        extras = values.get("extras", {})
        values["extras"] = dict(extras) if isinstance(extras, Mapping) else {}
        big5 = values.get("big5")
        values["big5"] = dict(big5) if isinstance(big5, Mapping) else None
        return cls(**values)


def lpi_json_schema() -> dict[str, Any]:
    properties: dict[str, Any] = {}
    type_hints = get_type_hints(LPIPersona)
    for dataclass_field in fields(LPIPersona):
        properties[dataclass_field.name] = _schema_for_type(type_hints[dataclass_field.name])
    required = [
        field_name
        for field_name in LPIPersona.__dataclass_fields__
        if field_name not in {"distortion_flags", "extras"}
    ]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://luvoire.celovin.com/schemas/lpi_v1.json",
        "title": "Luvoire Persona Interface v1",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def write_lpi_schema(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(lpi_json_schema(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def _schema_for_type(annotation: object) -> dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is Literal:
        return {"enum": list(args)}
    if origin in {Union, types.UnionType}:
        non_none = [arg for arg in args if arg is not type(None)]
        schema = _schema_for_type(non_none[0]) if len(non_none) == 1 else {"anyOf": [_schema_for_type(arg) for arg in non_none]}
        return {"anyOf": [schema, {"type": "null"}]}
    if origin in {tuple, list}:
        return {"type": "array", "items": {"type": "string"}}
    if origin in {Mapping, dict}:
        return {"type": "object"}
    if annotation is str:
        return {"type": "string"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    if annotation is Any:
        return {}
    return {"type": "object"}


__all__ = [
    "BIG5_KEY",
    "COUNTRY_ISO",
    "INCOME_BRACKET",
    "MARITAL_STATUS",
    "SEX",
    "LPIPersona",
    "lpi_json_schema",
    "write_lpi_schema",
]
