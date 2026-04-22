# Persona Seeding

## Overview

Knoema can seed replay agents from Nemotron-Personas-Korea as an optional alternative to the deterministic stub demographics used by the existing 100, 1K, 5K, and 10K replay files. The integration is limited to synthetic demographic seeding for local replay demos.

The committed fixture at `src/knoema/persona/fixtures/nemotron_sample_512.jsonl` contains 512 rows sampled from `nvidia/Nemotron-Personas-Korea` at revision `0381f03a403df78a7998000f8b11705635b654fd`, filtered to Seoul Gangnam district rows. Tests use this fixture so CI does not need live Hugging Face network access.

## License

License: `cc-by-4.0`

Knoema records the Nemotron-Personas-Korea license in `LICENSE-NEMOTRON.md`. The license gate was run against the canonical Hugging Face dataset repo `nvidia/Nemotron-Personas-Korea` and dataset card revision `0381f03a403df78a7998000f8b11705635b654fd`.

## Citation

Recommended attribution:

```text
Nemotron-Personas-Korea. NVIDIA and Naver Cloud. Hugging Face dataset:
https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea
License: CC BY 4.0.
```

The dataset card describes the personas as synthetic Korean personas grounded in public statistical distributions, including KOSIS, Korean court, National Health Insurance Service, Korea Rural Economic Institute, and Naver Cloud sources. Cite those upstream public-statistics sources when using the seeded replay in reports.

## How to Regenerate

Regenerate the committed Nemotron-seeded local replay:

```bash
python demo/replay/generate_replay.py --scenario 10k --persona-source nemotron
```

Verify the committed artifact:

```bash
python demo/replay/generate_replay.py --scenario 10k --persona-source nemotron --verify-existing
```

The replay file is `demo/replay/replay_10000agents_nemotron_gangnam_7pm.msgpack`. Existing stub replay files remain byte-identical and are checked separately with:

```bash
python demo/replay/generate_replay.py --scenario 10k --persona-source stub --verify-existing
```

## Scope and Limits

- Nemotron-Personas-Korea is used only for synthetic demographic seeding in local replay artifacts.
- Knoema does not use Nemotron-Personas-Korea for LLM fine-tuning or downstream model training in this repository.
- The default replay path remains `--persona-source stub`, preserving the committed 100, 1K, 5K, and 10K baseline msgpack hashes.
- The loader streams live Hugging Face rows when used without a fixture and never loads the full dataset into memory.
- Missing fields, including income, map to existing safe defaults instead of invented values.
