#!/usr/bin/env python3
"""extract_pdf_text.py — extract text + structure from a PDF.

Uses PyMuPDF (fitz) when available. Writes extraction.txt into the version dir with
page anchors (=== PAGE n ===), and emits a small JSON sidecar of detected structure
(title candidate, abstract, section headings, figure/table captions, references span).

Usage:
    extract_pdf_text.py library/<slug>/v1            # writes v1/extraction.txt
    extract_pdf_text.py path/to.pdf --out out.txt
    extract_pdf_text.py library/<slug>/v1 --json     # print structure JSON
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import paperlib as pl

try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False


HEADING_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)*\.?\s+[A-Z][^\n]{2,60}|"
    r"(?:Abstract|Introduction|Related Work|Background|Method(?:s|ology)?|"
    r"Approach|Experiments?|Evaluation|Results?|Discussion|Limitations?|"
    r"Conclusions?|References|Appendix)\b[^\n]*)$",
    re.MULTILINE)
CAPTION_RE = re.compile(r"^\s*(Figure|Fig\.|Table)\s*\d+[:.]\s*(.{0,200})", re.MULTILINE)


def extract(pdf_path: Path) -> tuple[str, dict]:
    if not HAVE_FITZ:
        raise RuntimeError("PyMuPDF (fitz) not installed: pip install pymupdf")
    doc = fitz.open(pdf_path)
    pages_text: list[str] = []
    for i, page in enumerate(doc):
        pages_text.append(f"=== PAGE {i + 1} ===\n" + page.get_text("text"))
    full = "\n".join(pages_text)
    doc.close()

    structure = _structure(full, pages_text)
    return full, structure


def _structure(full: str, pages_text: list[str]) -> dict:
    first_page = pages_text[0] if pages_text else ""
    # title candidate: first non-empty line of page 1 with reasonable length
    title = None
    for line in first_page.splitlines()[1:]:  # skip the PAGE marker
        s = line.strip()
        if 8 <= len(s) <= 200 and not s.lower().startswith(("arxiv", "preprint")):
            title = s
            break
    # abstract: between 'Abstract' and 'Introduction'/'1'
    abstract = None
    m = re.search(r"\bAbstract\b(.*?)(?:\n\s*(?:1\.?\s+)?Introduction\b|\n\s*Keywords\b)",
                  full, re.IGNORECASE | re.DOTALL)
    if m:
        abstract = re.sub(r"\s+", " ", m.group(1)).strip()[:3000]
    headings = []
    for hm in HEADING_RE.finditer(full):
        h = hm.group(1).strip()
        if h not in headings:
            headings.append(h)
    captions = [f"{c.group(1)} {c.group(2).strip()}" for c in CAPTION_RE.finditer(full)]
    refs_idx = full.rfind("References")
    return {
        "title_candidate": title,
        "abstract": abstract,
        "section_headings": headings[:60],
        "captions": captions[:80],
        "references_present": refs_idx > 0,
        "num_pages": len(pages_text),
        "num_chars": len(full),
    }


def _main() -> int:
    ap = argparse.ArgumentParser(description="Extract text/structure from a PDF.")
    ap.add_argument("target", help="version dir (library/<slug>/vN) or a .pdf path")
    ap.add_argument("--out", help="output text path (default: <vdir>/extraction.txt)")
    ap.add_argument("--json", action="store_true", help="print structure JSON")
    args = ap.parse_args()

    target = pl.resolve_path(args.target)

    if target.is_dir():
        pdf = target / "paper.pdf"
        out = Path(args.out) if args.out else target / "extraction.txt"
        vdir = target
    else:
        pdf = target
        out = Path(args.out) if args.out else target.with_suffix(".extraction.txt")
        vdir = None

    if not pdf.exists():
        print(f"PDF not found: {pdf}")
        return 1

    try:
        text, structure = extract(pdf)
    except Exception as e:  # noqa: BLE001
        pl.log_error("extract_pdf", str(e), pdf=str(pdf))
        print(f"extraction failed: {e}")
        # mark failed if in a version dir
        if vdir:
            mf = vdir / "metadata.yaml"
            if mf.exists():
                meta = pl.load_yaml(mf)
                meta.setdefault("status", {})["extracted"] = False
                pl.dump_yaml(mf, meta)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    side = out.with_suffix(".structure.json")
    side.write_text(json.dumps(structure, indent=2, ensure_ascii=False), encoding="utf-8")

    if vdir:
        mf = vdir / "metadata.yaml"
        if mf.exists():
            meta = pl.load_yaml(mf)
            meta.setdefault("artifacts", {})["extraction"] = pl.rel(out)
            st = meta.setdefault("status", {})
            st["extracted"] = True
            pl.dump_yaml(mf, meta)

    if args.json:
        print(json.dumps(structure, indent=2, ensure_ascii=False))
    else:
        print(f"extracted {structure['num_pages']} pages, {structure['num_chars']} chars -> {pl.rel(out)}")
        if structure["title_candidate"]:
            print(f"title candidate: {structure['title_candidate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
