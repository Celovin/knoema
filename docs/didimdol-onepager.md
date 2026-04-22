# Didimdol One-Pager

`scripts/build_grant_summary.py` rebuilds the bilingual Didimdol handout from committed repository sources.

```powershell
$env:SOURCE_DATE_EPOCH='0'
python scripts/build_grant_summary.py
```

Outputs:

- `dist/didimdol_onepager_ko.pdf`
- `dist/didimdol_onepager_en.pdf`

## Source Discipline

The three benchmark lines come from `benchmarks/memory_benchmark_integration/results/summary.json` rows `0..2`. The 1K-agent proof line comes from `benchmarks/city_scale_1k_report.md` and includes its source line references in the rendered PDF.

The script keeps `arXiv:<pending>` until the user has an assigned arXiv identifier. After assignment, update the placeholder in `scripts/grant_summary_templates/ko.md.j2` and `scripts/grant_summary_templates/en.md.j2`, then rebuild both PDFs.

## HF Space URL

The QR code encodes `https://huggingface.co/spaces/celovin/knoema-playground`. If the demo is re-hosted, update `HF_SPACE_URL` in `scripts/build_grant_summary.py` and rebuild.
