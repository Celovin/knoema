# Luvoire Persona Interface v1

Luvoire Persona Interface v1 (LPI v1) is the stable cross-country persona shape
used by the multi-country Nemotron-Personas loader. It maps similar but divergent
country schemas onto one dataclass while preserving country-specific fields in
`extras`.

## Rationale

The NVIDIA Nemotron-Personas family publishes compatible synthetic persona
datasets for seven countries under CC-BY-4.0, but each country uses slightly
different geographic, education, occupation, household, and cultural fields.
LPI v1 gives simulations one typed interface without dropping those source
fields.

## Countries

| ISO | Locale | Upstream dataset | Notable divergence |
| --- | --- | --- | --- |
| USA | `en-US` | `nvidia/Nemotron-Personas-USA` | state/city/zipcode geography |
| JPN | `ja-JP` | `nvidia/Nemotron-Personas-Japan` | prefecture/city geography |
| IND | `hi-IN-Deva` | `nvidia/Nemotron-Personas-India` | religion and script variants stay in `extras` |
| BRA | `pt-BR` | `nvidia/Nemotron-Personas-Brazil` | CBO occupation detail stays in `extras` |
| SGP | `en-SG` | `nvidia/Nemotron-Personas-Singapore` | ethnicity and industry stay in `extras` |
| FRA | `fr-FR` | `nvidia/Nemotron-Personas-France` | adult-only upstream rows; department codes stay in `extras` |
| KOR | `ko-KR` | `nvidia/Nemotron-Personas-Korea` | honorific and Korea-specific fields stay in `extras` |

## Fields

LPI v1 exposes these harmonized fields:

`persona_id`, `country_iso`, `language_locale`, `age`, `sex`, `region_l1`,
`region_l2`, `education_isced`, `occupation_isco08`,
`income_bracket_oecd`, `household_size`, `marital_status`, `big5`,
`narrative_text`, `grounding_source`, `grounding_version`,
`distortion_flags`, and `extras`.

Education is mapped to ISCED-2011 levels where the source taxonomy permits it.
Occupation is mapped to the ISCO-08 major-group code when a safe coarse mapping
exists. Household income is normalized to OECD-style quintiles `q1` through `q5`
when source rows provide compatible brackets.

## Extras Contract

`extras` is mandatory for schema preservation. A loader must place every
country-specific source field that does not map cleanly into the LPI core into
`extras`; loaders must not silently drop those fields.

Examples:

- India: `religion`, `script_variant`.
- Singapore: `ethnicity`, `industry`.
- Korea: `honorific_style`, `military_status`.
- France: `department_code`.
- Brazil: `cbo_code`.

## Determinism

`load_country(iso, limit=n, seed=s)` uses stable hash-based sampling over the
source stream. Reproducibility requires a fixed source revision. If an upstream
Hugging Face branch moves, the `grounding_version` field must be pinned in the
downstream artifact before claiming replay equivalence.

## Distortion Flags

Every LPI persona carries `llm_narrative_synthetic`. The loader adds
`blue_shift_risk` when a narrative contains political-axis vocabulary. The flag
names follow the distortion taxonomy discussed in the Twin-2K-500 "Funhouse
Mirrors" paper (arXiv:2509.19088).

## Schema

The machine-readable schema lives at `src/luvoire/personas/lpi_schema.json`.
Regenerate it with:

```bash
python -m luvoire.cli personas schema --out src/luvoire/personas/lpi_schema.json
```
