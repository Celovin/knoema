# Knoema Technical Report

This folder contains the Phase 12 technical report draft.

## Files

- `main.tex`: arXiv-oriented LaTeX source.
- `sections/`: paper sections included by `main.tex`.
- `references.bib`: BibTeX references.
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

The current Windows environment used for this draft did not include a LaTeX engine, so the committed PDF is generated from the same report content with ReportLab.
