# Addendum to Handoff v4 - Nemotron Local Cache Available

Date: 2026-04-22 (issued before Slot B starts)
Target handoff: `planning/codex_handoff_sequential_2026-04-22d.md` §2 Slot B.

The user has downloaded the Nemotron-Personas-Korea dataset locally. This addendum supersedes the network-assumption parts of Slot B §2.1 and §2.2.

## Local cache path

`D:\datasets\nemotron-personas-korea\`

Contents observed at issue time:

- `README.md` (dataset card, ~35 KB)
- `.gitattributes`
- `data/train-00000-of-00009.parquet` through `train-00008-of-00009.parquet` (9 shards, ~220 MB each, ~1.98 GB total)
- `images/` (dataset card images)
- `.cache/huggingface/` (snapshot metadata from HF Hub)

## How Codex must use it

1. **Primary data source:** load parquet shards directly from the local path.

   ```python
   from datasets import load_dataset
   ds = load_dataset(
       "parquet",
       data_files="D:/datasets/nemotron-personas-korea/data/train-*.parquet",
       split="train",
       streaming=True,
   )
   ```

   Do NOT issue a live `load_dataset("nvidia/Nemotron-Personas-Korea")` call that would re-download 1.98 GB.

2. **Dataset revision pinning:** still required per Slot B §2.2 item 4. Obtain the canonical revision via a metadata-only HF API call:

   ```python
   from huggingface_hub import HfApi
   revision = HfApi().dataset_info("nvidia/Nemotron-Personas-Korea").sha
   ```

   This call does NOT download the dataset; it only fetches the small JSON describing the repo. If the metadata call fails (offline), record `revision = "local-cache-unverified"` and log a warning in the replay `metadata` block.

3. **Fixture subset (`src/knoema/persona/fixtures/nemotron_sample_512.jsonl`):** produced from the local parquet directly. Take the first 512 rows after a deterministic sort (sort by `uuid` ascending) and dump as jsonl. Do not shuffle before sampling; determinism is the acceptance gate.

4. **License gate (§2.0):** still required. Read `D:\datasets\nemotron-personas-korea\README.md` and extract the license identifier. It should be `CC-BY-4.0` (already confirmed by user-side WebFetch on 2026-04-22). Record that string verbatim in `docs/persona_seeding.md` §License and write the verbatim license text into `LICENSE-NEMOTRON.md`.

5. **Fallback to live HF:** if the local path is unreadable for any reason, fall back to `load_dataset("nvidia/Nemotron-Personas-Korea", streaming=True)` and proceed. Do not halt on a missing local cache alone.

## Rationale

- Saves 1.98 GB of network download at Slot B runtime.
- Makes the 10K Nemotron-variant replay generation fully offline (higher determinism margin).
- Allows airgapped demo reproducibility.
- Keeps the HF API only for revision pinning (small metadata call).

## Scope

This addendum changes only how Slot B sources the data. Every other requirement in §2 of the v4 handoff (license gate, field mapping, deterministic sampling, forbidden-entity scan, 25 MB size bound, acceptance criteria, git paths) stays exactly as written.
