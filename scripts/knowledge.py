#!/usr/bin/env python3
"""knowledge.py — global, paper-agnostic knowledge base engine.

Concepts learned while discussing any paper live in knowledge/concepts/<slug>.md as
markdown notes with YAML front-matter. They are GLOBAL: a concept created while reading
paper A can be extended and reused when reading paper B. Links between concepts and
papers are bidirectional (concept.related_papers <-> paper.yaml knowledge_concepts).

Claude (the paper-tutor skill) writes the prose; this script owns the deterministic
parts: front-matter, slugs, bidirectional linking, search, and index regeneration.

Subcommands:
    ensure-concept --title "Agent-Computer Interface" [--aliases ACI] [--tags ...]
                   [--paper <key>] [--related <slug,...>]
    link --concept <slug> [--paper <key>] [--related <slug,...>]
    search "<query>"
    list
    session --paper <key> [--title "..."] [--concepts a,b]   # create a chat-session note
    index
    validate
"""
from __future__ import annotations

import argparse
import json
import re
import sys

import paperlib as pl

CONCEPT_SKELETON = """# {title}

## Intuition
_Write the intuitive, colleague-style explanation here._

## Details
_Mechanics, definitions, where it shows up._

## Q&A
_Questions I asked and the distilled answers._

## See also
"""

SESSION_SKELETON = """# Tutoring session — {title}

- Date: {date}
- Paper: {paper}
- Concepts touched: {concepts}

## What I asked / what I learned
_Chronological notes from the conversation._

## Distilled takeaways
_The reusable points (promote these into knowledge/concepts/ notes)._
"""


def _slug(title: str) -> str:
    return pl.slugify(title, max_words=8)


def _concept_path(slug: str):
    # Concepts are .mdx (ADR-0005); keep reading a legacy .md if that's all that exists.
    mdx = pl.CONCEPTS / f"{slug}.mdx"
    md = pl.CONCEPTS / f"{slug}.md"
    return md if (md.exists() and not mdx.exists()) else mdx


def _concept_files():
    seen = {p.stem: p for p in pl.CONCEPTS.glob("*.md")}
    seen.update({p.stem: p for p in pl.CONCEPTS.glob("*.mdx")})  # prefer .mdx on collision
    return sorted(seen.values())


def _split(s: str | None) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


# --------------------------------------------------------------------------- #
# concepts
# --------------------------------------------------------------------------- #

def ensure_concept(title: str, *, aliases=None, tags=None, paper=None, related=None) -> dict:
    slug = _slug(title)
    path = _concept_path(slug)
    meta, body = pl.load_md_frontmatter(path)
    existed = bool(meta)
    if not existed:
        cur = pl.resolve_curator()
        meta = {
            "name": slug, "title": title.strip(),
            "aliases": [], "tags": [], "related_papers": [],
            "related_concepts": [], "created": pl.now_iso(), "updated": pl.now_iso(),
            "curated_by": cur["id"], "contributors": [cur["id"]],
        }
        body = CONCEPT_SKELETON.format(title=title.strip())

    def merge(key, values):
        cur = meta.get(key) or []
        for v in values or []:
            if v and v not in cur:
                cur.append(v)
        meta[key] = cur

    merge("aliases", aliases)
    merge("tags", tags)
    merge("related_papers", [paper] if paper else [])
    merge("related_concepts", related)
    meta["updated"] = pl.now_iso()
    pl.dump_md_frontmatter(path, meta, body)

    if paper:
        _link_paper(slug, paper)
    for r in related or []:
        _link_concepts(slug, r)

    return {"slug": slug, "path": pl.rel(path), "existed": existed,
            "title": meta["title"], "related_papers": meta["related_papers"]}


def _link_paper(slug: str, canonical_key: str) -> bool:
    """Bidirectional: concept.related_papers <-> paper.yaml knowledge_concepts."""
    pdir = pl.find_paper_by_key(canonical_key)
    if not pdir:
        pl.log_error("knowledge.link", f"paper not found: {canonical_key}", concept=slug)
        return False
    pf = pdir / "paper.yaml"
    paper = pl.load_yaml(pf) or {}
    kc = paper.get("knowledge_concepts") or []
    if slug not in kc:
        kc.append(slug)
        paper["knowledge_concepts"] = kc
        pl.dump_yaml(pf, paper)
    # ensure reverse link present on concept
    path = _concept_path(slug)
    meta, body = pl.load_md_frontmatter(path)
    if meta:
        rp = meta.get("related_papers") or []
        if canonical_key not in rp:
            rp.append(canonical_key)
            meta["related_papers"] = rp
            meta["updated"] = pl.now_iso()
            pl.dump_md_frontmatter(path, meta, body)
    return True


def _link_concepts(a: str, b: str) -> None:
    for x, y in ((a, b), (b, a)):
        path = _concept_path(x)
        meta, body = pl.load_md_frontmatter(path)
        if not meta:
            continue
        rc = meta.get("related_concepts") or []
        if y not in rc:
            rc.append(y)
            meta["related_concepts"] = rc
            meta["updated"] = pl.now_iso()
            pl.dump_md_frontmatter(path, meta, body)


def iter_concepts():
    if not pl.CONCEPTS.exists():
        return
    for p in _concept_files():
        meta, body = pl.load_md_frontmatter(p)
        if meta:
            yield p, meta, body


def search(query: str) -> list[dict]:
    q = query.lower()
    hits = []
    for p, meta, body in iter_concepts():
        hay = " ".join([
            meta.get("title", ""), " ".join(meta.get("aliases") or []),
            " ".join(meta.get("tags") or []), body]).lower()
        if all(term in hay for term in q.split()):
            hits.append({"slug": meta["name"], "title": meta["title"],
                         "tags": meta.get("tags") or [],
                         "related_papers": meta.get("related_papers") or [],
                         "path": pl.rel(p)})
    return hits


# --------------------------------------------------------------------------- #
# sessions
# --------------------------------------------------------------------------- #

def new_session(paper: str | None, title: str | None, concepts=None) -> dict:
    label = title or (paper or "discussion")
    slug = pl.slugify(label, max_words=6)
    fname = f"{pl.today()}-{slug}.md"
    path = pl.SESSIONS / fname
    if not path.exists():
        body = SESSION_SKELETON.format(
            title=label, date=pl.now_iso(), paper=paper or "—",
            concepts=", ".join(concepts or []) or "—")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return {"path": pl.rel(path), "paper": paper, "concepts": concepts or []}


# --------------------------------------------------------------------------- #
# index
# --------------------------------------------------------------------------- #

GEN = "<!-- generated by scripts/knowledge.py — do not edit by hand -->"


def build_index(write: bool = True) -> dict:
    concepts = [(meta, body) for _, meta, body in iter_concepts()]
    concepts.sort(key=lambda mb: mb[0].get("title", "").lower())

    # paper title lookup
    titles = {p.get("canonical_key"): p.get("title") for p in pl.iter_papers()}

    def first_para(body: str) -> str:
        # the line under '## Intuition' if filled, else first non-heading line
        m = re.search(r"## Intuition\s*\n+([^\n#_].{0,200})", body)
        if m:
            return m.group(1).strip()
        for line in body.splitlines():
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("_"):
                return s[:200]
        return ""

    idx = ["# Knowledge base", "", GEN, "",
           f"_{len(concepts)} concept(s)._", "",
           "| Concept | Tags | Linked papers | Summary |", "|---|---|---|---|"]
    by_tag: dict[str, list] = {}
    by_paper: dict[str, list] = {}
    for meta, body in concepts:
        slug = meta["name"]
        rps = meta.get("related_papers") or []
        plinks = ", ".join(f"`{k}`" for k in rps) or "—"
        tags_txt = ", ".join(meta.get("tags") or []) or "—"
        summary_txt = first_para(body).replace("|", "\\|")
        idx.append(f"| [{meta['title']}](concepts/{slug}.md) "
                   f"| {tags_txt} | {plinks} | {summary_txt} |")
        for t in (meta.get("tags") or ["untagged"]):
            by_tag.setdefault(t, []).append((meta, body))
        for k in rps or ["(unlinked)"]:
            by_paper.setdefault(k, []).append((meta, body))

    tag_md = ["# Knowledge by tag", "", GEN, ""]
    for t in sorted(by_tag):
        tag_md.append(f"## {t} ({len(by_tag[t])})")
        for meta, _ in sorted(by_tag[t], key=lambda mb: mb[0]["title"].lower()):
            tag_md.append(f"- [{meta['title']}](concepts/{meta['name']}.md)")
        tag_md.append("")

    paper_md = ["# Knowledge by paper", "", GEN, "",
                "Concepts grouped by the paper(s) they were learned from / linked to.", ""]
    for k in sorted(by_paper):
        title = titles.get(k, k)
        paper_md.append(f"## {title}  (`{k}`)")
        for meta, _ in sorted(by_paper[k], key=lambda mb: mb[0]["title"].lower()):
            paper_md.append(f"- [{meta['title']}](concepts/{meta['name']}.md)")
        paper_md.append("")

    out = {
        pl.KNOWLEDGE / "INDEX.md": "\n".join(idx) + "\n",
        pl.KNOWLEDGE / "BY_TAG.md": "\n".join(tag_md) + "\n",
        pl.KNOWLEDGE / "BY_PAPER.md": "\n".join(paper_md) + "\n",
    }
    if write:
        for p, c in out.items():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(c, encoding="utf-8")
    return {"concepts": len(concepts), "tags": len(by_tag), "papers_linked": len(by_paper)}


def validate() -> dict:
    errors, warnings = [], []
    keys = {p.get("canonical_key") for p in pl.iter_papers()}
    paper_concepts = {}
    for p in pl.iter_papers():
        for slug in p.get("knowledge_concepts") or []:
            paper_concepts.setdefault(slug, set()).add(p.get("canonical_key"))
    for path, meta, body in iter_concepts():
        if not meta.get("name") or not meta.get("title"):
            errors.append(f"{path.name}: missing name/title")
        for k in meta.get("related_papers") or []:
            if k not in keys:
                warnings.append(f"{meta.get('name')}: related_paper '{k}' not in registry")
            elif meta["name"] not in (pl.load_paper(pl.find_paper_by_key(k)) or {}).get("knowledge_concepts", []):
                warnings.append(f"{meta.get('name')}: link to '{k}' not reciprocated in paper.yaml")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _main() -> int:
    ap = argparse.ArgumentParser(description="Global knowledge base for paper learning.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("ensure-concept")
    e.add_argument("--title", required=True)
    e.add_argument("--aliases")
    e.add_argument("--tags")
    e.add_argument("--paper")
    e.add_argument("--related")

    l = sub.add_parser("link")
    l.add_argument("--concept", required=True)
    l.add_argument("--paper")
    l.add_argument("--related")

    s = sub.add_parser("search")
    s.add_argument("query")

    sub.add_parser("list")

    se = sub.add_parser("session")
    se.add_argument("--paper")
    se.add_argument("--title")
    se.add_argument("--concepts")

    sub.add_parser("index")
    sub.add_parser("validate")

    args = ap.parse_args()

    if args.cmd == "ensure-concept":
        res = ensure_concept(args.title, aliases=_split(args.aliases),
                             tags=_split(args.tags), paper=args.paper,
                             related=_split(args.related))
        build_index(write=True)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.cmd == "link":
        ok = True
        if args.paper:
            ok = _link_paper(args.concept, args.paper)
        for r in _split(args.related):
            _link_concepts(args.concept, r)
        build_index(write=True)
        print(json.dumps({"concept": args.concept, "linked_paper": args.paper,
                          "ok": ok}, ensure_ascii=False))
    elif args.cmd == "search":
        print(json.dumps(search(args.query), indent=2, ensure_ascii=False))
    elif args.cmd == "list":
        out = [{"slug": m["name"], "title": m["title"],
                "papers": m.get("related_papers") or []} for _, m, _ in iter_concepts()]
        print(json.dumps(out, indent=2, ensure_ascii=False))
    elif args.cmd == "session":
        print(json.dumps(new_session(args.paper, args.title, _split(args.concepts)),
                         indent=2, ensure_ascii=False))
    elif args.cmd == "index":
        print(json.dumps(build_index(write=True), ensure_ascii=False))
    elif args.cmd == "validate":
        res = validate()
        for w in res["warnings"]:
            print(f"WARN  {w}")
        for er in res["errors"]:
            print(f"ERROR {er}")
        print("knowledge OK" if res["ok"] else f"knowledge FAILED ({len(res['errors'])})")
        return 0 if res["ok"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
