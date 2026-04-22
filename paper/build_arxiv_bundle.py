"""Build and verify the Luvoire arXiv v2 submission bundle.

The preferred path uses a local TeX engine. If ``pdflatex`` is unavailable,
the script emits the existing ReportLab preview as the PDF artifact and still
packages the LaTeX sources and generated ``main.bbl`` for arXiv upload.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import re
import shutil
import subprocess
import sys
import tarfile
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

from PIL import Image
from pypdf import PdfReader

PAPER_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PAPER_ROOT.parent
DIST_ROOT = PROJECT_ROOT / "dist"
BUILD_ROOT = PROJECT_ROOT / "tmp" / "arxiv_build"
SOURCE_ROOT = BUILD_ROOT / "source"
RENDER_ROOT = PROJECT_ROOT / "tmp" / "arxiv_render"
PDF_OUTPUT = DIST_ROOT / "luvoire_arxiv_v2.pdf"
TARBALL_OUTPUT = DIST_ROOT / "luvoire_arxiv_v2.tar.gz"
MIN_PAGE_COUNT = 12


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Skip pdftoppm render verification. Intended only for diagnosing PDF build failures.",
    )
    args = parser.parse_args(argv)

    DIST_ROOT.mkdir(parents=True, exist_ok=True)
    clean_project_dir(BUILD_ROOT)
    SOURCE_ROOT.mkdir(parents=True, exist_ok=True)

    prepare_source_tree(SOURCE_ROOT)
    write_generated_bbl(SOURCE_ROOT / "references.bib", SOURCE_ROOT / "main.bbl")
    build_mode = build_pdf(SOURCE_ROOT, PDF_OUTPUT)
    page_count = verify_pdf(PDF_OUTPUT)
    if not args.no_render:
        render_and_check_pdf(PDF_OUTPUT, page_count)
    create_tarball(SOURCE_ROOT, TARBALL_OUTPUT)
    verify_tarball(TARBALL_OUTPUT)

    print(f"pdf={PDF_OUTPUT}")
    print(f"tarball={TARBALL_OUTPUT}")
    print(f"page_count={page_count}")
    print(f"build_mode={build_mode}")
    if not args.no_render:
        print(f"render_dir={RENDER_ROOT}")
    return 0


def clean_project_dir(path: Path) -> None:
    resolved = path.resolve()
    project = PROJECT_ROOT.resolve()
    if resolved == project or project not in resolved.parents:
        msg = f"refusing to clean path outside project tmp: {resolved}"
        raise RuntimeError(msg)
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def prepare_source_tree(destination: Path) -> None:
    copy_file(PAPER_ROOT / "abstract.tex", destination / "abstract.tex")
    copy_file(PAPER_ROOT / "appendix.tex", destination / "appendix.tex")
    copy_file(PAPER_ROOT / "references.bib", destination / "references.bib")
    for folder in ("sections", "tables", "figures"):
        shutil.copytree(PAPER_ROOT / folder, destination / folder)

    main_text = (PAPER_ROOT / "main.tex").read_text(encoding="utf-8")
    appendix_text = (PAPER_ROOT / "appendix.tex").read_text(encoding="utf-8")
    marker = r"\input{appendix}"
    if marker not in main_text:
        msg = "paper/main.tex no longer contains the appendix input marker"
        raise RuntimeError(msg)
    inlined_main = main_text.replace(
        marker,
        "% Begin inlined appendix.tex for arXiv source portability\n"
        f"{appendix_text}\n"
        "% End inlined appendix.tex\n",
        1,
    )
    (destination / "main.tex").write_text(inlined_main, encoding="utf-8")


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_generated_bbl(bib_path: Path, bbl_path: Path) -> None:
    entries = parse_bibtex_entries(bib_path.read_text(encoding="utf-8"))
    if not entries:
        msg = f"no BibTeX entries found in {bib_path}"
        raise RuntimeError(msg)

    lines = [r"\begin{thebibliography}{99}"]
    for entry in entries:
        key = entry["key"]
        author = entry.get("author") or entry.get("editor") or key
        title = entry.get("title") or "Untitled"
        venue = entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""
        year = entry.get("year") or "n.d."
        suffix = f" {venue}, {year}." if venue else f" {year}."
        lines.extend(
            [
                rf"\bibitem{{{key}}}",
                rf"{compact_tex(author)}.",
                rf"\newblock {compact_tex(title)}.",
                rf"\newblock{compact_tex(suffix)}",
            ]
        )
    lines.append(r"\end{thebibliography}")
    bbl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_bibtex_entries(text: str) -> list[dict[str, str]]:
    parsed: list[dict[str, str]] = []
    for match in re.finditer(r"@\w+\{([^,]+),(.*?)(?=\n@|\Z)", text, flags=re.DOTALL):
        body = match.group(2)
        entry: dict[str, str] = {"key": match.group(1).strip()}
        for field in ("author", "editor", "title", "journal", "booktitle", "publisher", "year"):
            value = extract_braced_field(body, field)
            if value is not None:
                entry[field] = value
        parsed.append(entry)
    return parsed


def extract_braced_field(body: str, field: str) -> str | None:
    match = re.search(rf"\b{field}\s*=\s*\{{", body)
    if match is None:
        return None
    index = match.end()
    depth = 1
    value: list[str] = []
    while index < len(body):
        char = body[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(value)
        value.append(char)
        index += 1
    return None


def compact_tex(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_pdf(source_root: Path, output_path: Path) -> str:
    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        build_reportlab_preview(output_path)
        return "reportlab_fallback_no_pdflatex"

    bibtex = shutil.which("bibtex")
    log_path = BUILD_ROOT / "tex_build.log"
    commands = [[pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"]]
    if bibtex is not None:
        commands.append([bibtex, "main"])
    commands.extend(
        [
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
        ]
    )

    log_parts: list[str] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=source_root,
            capture_output=True,
            text=True,
            check=False,
        )
        log_parts.extend(
            [
                f"$ {' '.join(command)}",
                completed.stdout,
                completed.stderr,
                f"exit={completed.returncode}",
            ]
        )
        if completed.returncode != 0:
            log_path.write_text("\n".join(log_parts), encoding="utf-8")
            msg = f"TeX build failed; see {log_path}"
            raise RuntimeError(msg)

    log_path.write_text("\n".join(log_parts), encoding="utf-8")
    built_pdf = source_root / "main.pdf"
    if not built_pdf.exists():
        msg = f"TeX build completed but {built_pdf} was not produced"
        raise RuntimeError(msg)
    shutil.copy2(built_pdf, output_path)
    if (source_root / "main.bbl").exists():
        return "pdflatex_with_bibtex" if bibtex is not None else "pdflatex_with_generated_bbl"
    return "pdflatex"


def build_reportlab_preview(output_path: Path) -> None:
    module = load_build_pdf_module()
    module.OUTPUT = output_path
    module.build_pdf()


def load_build_pdf_module() -> ModuleType:
    module_path = PAPER_ROOT / "build_pdf.py"
    spec = importlib.util.spec_from_file_location("luvoire_arxiv_preview_builder", module_path)
    if spec is None or spec.loader is None:
        msg = f"could not load {module_path}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_pdf(pdf_path: Path) -> int:
    reader = PdfReader(pdf_path)
    page_count = len(reader.pages)
    if page_count < MIN_PAGE_COUNT:
        msg = f"{pdf_path} has {page_count} pages; expected at least {MIN_PAGE_COUNT}"
        raise RuntimeError(msg)
    return page_count


def render_and_check_pdf(pdf_path: Path, page_count: int) -> None:
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        msg = "pdftoppm is required for visual proof but was not found"
        raise RuntimeError(msg)

    clean_project_dir(RENDER_ROOT)
    run_pdftoppm(pdftoppm, pdf_path, RENDER_ROOT / "first_page", first=1, last=1, dpi=96)
    run_pdftoppm(
        pdftoppm,
        pdf_path,
        RENDER_ROOT / "last_page",
        first=page_count,
        last=page_count,
        dpi=96,
    )
    run_pdftoppm(pdftoppm, pdf_path, RENDER_ROOT / "page", first=1, last=page_count, dpi=24)
    pngs = sorted(RENDER_ROOT.glob("page-*.png"))
    if len(pngs) != page_count:
        msg = f"rendered {len(pngs)} pages but expected {page_count}"
        raise RuntimeError(msg)
    blank_pages = [path.name for path in pngs if image_looks_blank(path)]
    if blank_pages:
        msg = f"blank-looking pages detected by histogram: {', '.join(blank_pages)}"
        raise RuntimeError(msg)


def run_pdftoppm(
    executable: str,
    pdf_path: Path,
    prefix: Path,
    *,
    first: int,
    last: int,
    dpi: int,
) -> None:
    subprocess.run(
        [
            executable,
            "-f",
            str(first),
            "-l",
            str(last),
            "-r",
            str(dpi),
            "-png",
            str(pdf_path),
            str(prefix),
        ],
        check=True,
    )


def image_looks_blank(path: Path) -> bool:
    with Image.open(path) as image:
        gray = image.convert("L")
        width, height = gray.size
        content_region = gray.crop((0, 0, width, int(height * 0.88)))
        histogram = content_region.histogram()
        total = sum(histogram)
        non_white = sum(count for value, count in enumerate(histogram) if value < 248)
        return total == 0 or (non_white / total) < 0.001


def create_tarball(source_root: Path, tarball_path: Path) -> None:
    files = sorted(path for path in source_root.rglob("*") if path.is_file())
    with (
        tarball_path.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gzip_file,
        tarfile.open(fileobj=gzip_file, mode="w") as archive,
    ):
        for path in files:
            archive.add(
                path,
                arcname=path.relative_to(source_root).as_posix(),
                filter=normalize_tar_info,
            )


def normalize_tar_info(info: tarfile.TarInfo) -> tarfile.TarInfo:
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    info.mtime = 0
    return info


def verify_tarball(tarball_path: Path) -> None:
    with tarfile.open(tarball_path, "r:gz") as archive:
        names = set(archive.getnames())

    required = {"main.tex", "appendix.tex", "references.bib", "main.bbl"}
    required.update(includegraphics_paths(SOURCE_ROOT))
    missing = sorted(required - names)
    if missing:
        msg = f"{tarball_path} is missing required entries: {', '.join(missing)}"
        raise RuntimeError(msg)


def includegraphics_paths(source_root: Path) -> set[str]:
    required: set[str] = set()
    for tex_path in source_root.rglob("*.tex"):
        text = tex_path.read_text(encoding="utf-8")
        for raw_ref in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
            required.update(resolve_graphic_reference(source_root, tex_path.parent, raw_ref))
    return required


def resolve_graphic_reference(source_root: Path, base: Path, raw_ref: str) -> set[str]:
    candidates = [base / raw_ref, source_root / raw_ref]
    suffixes = ("", ".pdf", ".png", ".jpg", ".jpeg", ".eps")
    resolved: set[str] = set()
    for candidate in candidates:
        for suffix in suffixes:
            path = candidate if suffix == "" else candidate.with_suffix(suffix)
            if path.exists() and path.is_file():
                resolved.add(path.relative_to(source_root).as_posix())
    if not resolved:
        msg = f"could not resolve includegraphics reference {raw_ref!r}"
        raise RuntimeError(msg)
    return resolved


def iter_relative_names(paths: Iterable[Path], root: Path) -> list[str]:
    return [path.relative_to(root).as_posix() for path in paths]


if __name__ == "__main__":
    sys.exit(main())
