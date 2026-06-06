#!/usr/bin/env python3
"""summarize_paper.py — prepare + finalize summary scaffolding for a version dir.

Claude writes the actual English analysis (it reads extraction.txt and fills the
template). This script handles the deterministic parts so the skill stays simple:

  --prepare : ensure extraction exists (calls extract_pdf_text), then emit a
              pre-filled summary scaffold (template + known metadata + a context
              bundle of the extracted text for Claude to read). Preserves any
              existing "## Personal notes" block.
  --finalize: after Claude writes summary.md, mark status + wire artifact paths +
              update paper.yaml and trigger downstream (caller runs indexes).

Usage:
    summarize_paper.py library/<slug>/v2 --prepare
    summarize_paper.py library/<slug>/v2 --finalize --status full
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import paperlib as pl
import extract_pdf_text

NOTES_HEADER = "## Personal notes"


def _resolve_vdir(target: str) -> Path:
    return pl.resolve_path(target)


def _existing_notes(summary_path: Path) -> str | None:
    if not summary_path.exists():
        return None
    text = summary_path.read_text(encoding="utf-8")
    m = re.search(rf"{re.escape(NOTES_HEADER)}\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
    if m and m.group(1).strip():
        return m.group(1).strip()
    return None


def summary_filename(fmt: str) -> str:
    return {"html": "summary.html", "mdx": "summary.mdx"}.get(fmt, "summary.md")


def _existing_notes_mdx(path: Path) -> str | None:
    """Personal-notes preservation for MDX (JSX comments; MDX rejects HTML comments)."""
    if not path.exists():
        return None
    m = re.search(r"\{/\*\s*NOTES_START\s*\*/\}(.*?)\{/\*\s*NOTES_END\s*\*/\}",
                  path.read_text(encoding="utf-8"), re.DOTALL)
    if m and m.group(1).strip() and "Free-form notes for later" not in m.group(1):
        return m.group(1).strip()
    return None


def _existing_notes_html(path: Path) -> str | None:
    if not path.exists():
        return None
    m = re.search(r"<!--PERSONAL_NOTES_START-->(.*?)<!--PERSONAL_NOTES_END-->",
                  path.read_text(encoding="utf-8"), re.DOTALL)
    if m and m.group(1).strip() and "Free-form notes for later" not in m.group(1):
        return m.group(1).strip()
    return None


def _ensure_extraction(vdir: Path, meta: dict, mf: Path) -> bool:
    extraction = vdir / "extraction.txt"
    if extraction.exists():
        return True
    if (vdir / "paper.pdf").exists():
        try:
            text, _ = extract_pdf_text.extract(vdir / "paper.pdf")
            extraction.write_text(text, encoding="utf-8")
            meta.setdefault("artifacts", {})["extraction"] = pl.rel(extraction)
            meta.setdefault("status", {})["extracted"] = True
            pl.dump_yaml(mf, meta)
            return True
        except Exception as e:  # noqa: BLE001
            pl.log_error("summarize.prepare", str(e), vdir=pl.rel(vdir))
    return False


def _meta_fields(meta: dict) -> dict:
    return {
        "TITLE": meta.get("title", "Untitled"),
        "CANONICAL_KEY": meta.get("canonical_key", ""),
        "VERSION": meta.get("version_key", ""),
        "FETCH_DATE": meta.get("fetched_at", ""),
        "SOURCE": meta.get("source", "") or "",
        "PDF": (meta.get("artifacts") or {}).get("pdf") or "Not reported",
        "VENUE": meta.get("venue") or "Not reported",
        "YEAR": meta.get("year") or "Not reported",
        "AUTHORS": ", ".join(meta.get("authors") or []) or "Not reported",
        "TAGS": ", ".join(meta.get("tags") or []) or "—",
        "USER_STATUS": (meta.get("status") or {}).get("user_read_status", "unread"),
        "TRIAGE_LABEL": (meta.get("scoring") or {}).get("label") or "TBD",
        "TRIAGE_CONFIDENCE": (meta.get("scoring") or {}).get("confidence") or "TBD",
        "SOURCE_LINK": meta.get("source_url") or meta.get("pdf_url") or "",
        "SUMMARY_DATE": pl.today(),
        "ABSTRACT": (meta.get("abstract") or "").replace("\n", " ")[:600],
    }


def prepare(vdir: Path, fmt: str = "md") -> dict:
    mf = vdir / "metadata.yaml"
    meta = pl.load_yaml(mf) or {}
    extracted_ok = _ensure_extraction(vdir, meta, mf)
    extraction = vdir / "extraction.txt"
    f = _meta_fields(meta)

    if fmt == "html":
        template = (pl.CONFIG / "summary_template.html").read_text(encoding="utf-8")
        scaffold = template
        for k, v in f.items():
            scaffold = scaffold.replace("{{" + k + "}}", str(v))
        notes = _existing_notes_html(vdir / "summary.html")
        if notes:
            scaffold = re.sub(r"<!--PERSONAL_NOTES_START-->.*?<!--PERSONAL_NOTES_END-->",
                              f"<!--PERSONAL_NOTES_START-->\n{notes}\n<!--PERSONAL_NOTES_END-->",
                              scaffold, flags=re.DOTALL)
        scaffold_path = vdir / "summary.scaffold.html"
    elif fmt == "mdx":
        # Frontmatter is generated as proper YAML (correct escaping/typing), not via
        # string substitution; only the body comes from the template.
        import yaml as _yaml
        body = (pl.CONFIG / "summary_template.mdx").read_text(encoding="utf-8")
        for k, v in f.items():
            body = body.replace("{{" + k + "}}", str(v))
        fm = {
            "canonical_key": meta.get("canonical_key"),
            "version_key": meta.get("version_key"),
            "title": meta.get("title") or "Untitled",
            "authors": meta.get("authors") or [],
            "venue": meta.get("venue"),
            "year": meta.get("year"),
            "tags": meta.get("tags") or [],
            "topic_groups": meta.get("topic_groups") or [],
            "triage_label": (meta.get("scoring") or {}).get("label"),
            "triage_confidence": (meta.get("scoring") or {}).get("confidence"),
            "source_link": meta.get("source_url") or meta.get("pdf_url"),
            "summary_date": pl.today(),
        }
        fmblock = _yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=100).strip()
        scaffold = f"---\n{fmblock}\n---\n\n{body.lstrip()}"
        notes = _existing_notes_mdx(vdir / "summary.mdx")
        if notes:
            scaffold = re.sub(r"\{/\*\s*NOTES_START\s*\*/\}.*?\{/\*\s*NOTES_END\s*\*/\}",
                              "{/* NOTES_START */}\n" + notes + "\n{/* NOTES_END */}",
                              scaffold, flags=re.DOTALL)
        scaffold_path = vdir / "summary.scaffold.mdx"
    else:
        template = (pl.CONFIG / "summary_template.md").read_text(encoding="utf-8")
        repl = {
            "- Canonical key:": f"- Canonical key: {f['CANONICAL_KEY']}",
            "- Version:": f"- Version: {f['VERSION']}",
            "- Fetch date:": f"- Fetch date: {f['FETCH_DATE']}",
            "- Source:": f"- Source: {f['SOURCE']}",
            "- PDF:": f"- PDF: {f['PDF']}",
            "- Venue:": f"- Venue: {f['VENUE']}",
            "- Year:": f"- Year: {f['YEAR']}",
            "- Authors:": f"- Authors: {f['AUTHORS']}",
            "- Tags:": f"- Tags: {f['TAGS']}",
            "- User status:": f"- User status: {f['USER_STATUS']}",
            "- Triage label:": f"- Triage label: {f['TRIAGE_LABEL']}",
            "- Triage confidence:": f"- Triage confidence: {f['TRIAGE_CONFIDENCE']}",
        }
        scaffold = template.replace("# <Paper Title>", f"# {f['TITLE']}")
        for k, v in repl.items():
            scaffold = scaffold.replace(k, v, 1)
        notes = _existing_notes(vdir / "summary.md")
        if notes:
            scaffold = re.sub(rf"{re.escape(NOTES_HEADER)}\nFree-form notes for later\.",
                              f"{NOTES_HEADER}\n{notes}", scaffold)
        scaffold_path = vdir / "summary.scaffold.md"

    scaffold_path.write_text(scaffold, encoding="utf-8")
    out = summary_filename(fmt)
    return {
        "vdir": pl.rel(vdir),
        "format": fmt,
        "extraction": pl.rel(extraction) if extracted_ok else None,
        "extraction_chars": len(extraction.read_text(encoding="utf-8")) if extracted_ok else 0,
        "scaffold": pl.rel(scaffold_path),
        "abstract": meta.get("abstract"),
        "preserved_notes": bool(notes),
        "instructions": (
            f"Read extraction.txt fully, then write the analysis into {out} using "
            f"{scaffold_path.name} as the skeleton. Follow config/summary_template.{fmt}: "
            "three passes; keep Motivation separate from Novelty; be SELF-CONTAINED "
            "(define non-universal terms inline + in the Glossary); declarative English; "
            "'Not reported'/'Unclear' for gaps; anchors. Then run --finalize "
            f"--format {fmt}."),
    }


def finalize(vdir: Path, status: str = "full", fmt: str = "md") -> dict:
    mf = vdir / "metadata.yaml"
    meta = pl.load_yaml(mf) or {}
    out = summary_filename(fmt)
    summary = vdir / out
    if not summary.exists():
        return {"error": f"{out} not found; write it before --finalize"}
    meta.setdefault("artifacts", {})["summary"] = pl.rel(summary)
    meta.setdefault("status", {})["summarized"] = status in ("full", "triage_only")
    meta["status"]["summary_format"] = fmt
    pl.dump_yaml(mf, meta)
    for ext in ("md", "html", "mdx"):
        (vdir / f"summary.scaffold.{ext}").unlink(missing_ok=True)

    pdir = vdir.parent
    pf = pdir / "paper.yaml"
    paper = pl.load_yaml(pf) or {}
    for v in paper.get("versions", []):
        if v.get("version_key") == vdir.name:
            v["summary_path"] = pl.rel(summary)
            v["summary_status"] = status
            v["extraction_status"] = "full" if (vdir / "extraction.txt").exists() else "none"
            v["updated_at"] = pl.now_iso()
    sc = meta.get("scoring") or {}
    if sc.get("label"):
        paper.setdefault("user", {})["triage_label"] = sc["label"]
        paper["user"]["triage_confidence"] = sc.get("confidence")
    pl.dump_yaml(pf, paper)
    return {"vdir": pl.rel(vdir), "summary": pl.rel(summary),
            "summary_status": status, "format": fmt}


def _main() -> int:
    ap = argparse.ArgumentParser(description="Prepare/finalize a paper summary.")
    ap.add_argument("target", help="version dir (library/<slug>/vN)")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--status", default="full", choices=pl.SUMMARY_STATUSES)
    ap.add_argument("--format", default="md", choices=["md", "html", "mdx"],
                    help="summary representation (mdx = website default; md/html legacy)")
    args = ap.parse_args()
    vdir = _resolve_vdir(args.target)
    if not vdir.exists():
        print(f"version dir not found: {vdir}")
        return 1
    import json
    if args.finalize:
        print(json.dumps(finalize(vdir, args.status, args.format), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(prepare(vdir, args.format), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
