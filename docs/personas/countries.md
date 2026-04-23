# Nemotron-Personas Countries

Luvoire supports seven CC-BY-4.0 Nemotron-Personas countries through
`luvoire.personas.loaders`.

## Attribution Text

Downstream artifacts should cite:

> NVIDIA Nemotron-Personas, CC-BY-4.0. Country-specific dataset source:
> `nvidia/Nemotron-Personas-{Country}`. Luvoire maps source rows into LPI v1 and
> preserves unmapped country-specific fields in `extras`.

## Country Notes

### USA

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-USA>
- Loader ISO: `USA`
- Caveat: US geography maps `state` to `region_l1` and city/zipcode detail to
  `region_l2`/`extras`.

### Japan

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-Japan>
- Loader ISO: `JPN`
- Caveat: prefecture and city fields map to `region_l1` and `region_l2`.

### India

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-India>
- Loader ISO: `IND`
- Caveat: religion and script variants are not part of the LPI core; they remain
  in `extras`.

### Brazil

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-Brazil>
- Loader ISO: `BRA`
- Caveat: CBO occupation expansion is preserved in `extras` when present.

### Singapore

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore>
- Loader ISO: `SGP`
- Caveat: ethnicity and industry axes remain in `extras`.

### France

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-France>
- Loader ISO: `FRA`
- Caveat: the upstream dataset is adult-focused; department codes remain in
  `extras`.

### Korea

- Dataset: <https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea>
- Loader ISO: `KOR`
- Caveat: Korea-specific honorific and military-status fields remain in `extras`.
  The legacy Korea-only replay seeding path remains callable through
  `luvoire.persona.nemotron_loader.NemotronPersonaSource`.

## CLI

```bash
python -m luvoire.cli personas list
python -m luvoire.cli personas sample --country USA --n 10 --seed 42
python -m luvoire.cli personas schema --out lpi_schema.json
```
