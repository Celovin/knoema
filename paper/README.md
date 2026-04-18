# Knoema Technical Report

This folder contains the Phase 30 arXiv-oriented technical report draft. It keeps the earlier Phase 12 source files for continuity and adds the v2 preprint structure used by `main.tex`.

## Files

- `main.tex`: arXiv-oriented LaTeX source for the Phase 30 draft.
- `abstract.tex`: paper abstract included by `main.tex`.
- `sections/01_*.tex` through `sections/07_*.tex`: v2 paper sections.
- `figures/`: LaTeX figure blocks for architecture, DSL, SDK, benchmark, and safety diagrams.
- `tables/`: LaTeX tables for benchmark and release-artifact summaries.
- `appendix.tex`: artifact and reproducibility appendix.
- `references.bib`: expanded BibTeX references for the preprint.
- `build_pdf.py`: local PDF preview builder using ReportLab.
- `knoema_technical_report.pdf`: generated preview PDF for meetings.

## Build Preview PDF

```powershell
cd C:\Users\admin\Projects\knoema
.venv\Scripts\pip install reportlab pdfplumber pypdf
.venv\Scripts\python paper\build_pdf.py
```

## Build LaTeX PDF

Install a LaTeX engine such as TeX Live, MiKTeX, or Tectonic, then run:

```powershell
cd C:\Users\admin\Projects\knoema\paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The current Windows environment used for this draft did not include a LaTeX engine. The committed preview PDF is generated from the same report content with ReportLab and visually checked by rendering pages with Poppler.
