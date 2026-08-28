#!/usr/bin/env python3
"""One-off data fix (2026-08-28): set the accepted/published venue on papers that were
ingested straight from arXiv without enrichment (venue policy, CLAUDE.md rule 11).

Reads the table next to this file (`2026-08-28-venue-fix.yaml`: slug → venue/status/year/
evidence), and for each paper:
  - paper.yaml   → venue: {name, tier (from config/venues.yaml), status, year}
  - vN/metadata.yaml (every version) → venue: <name>; scoring re-computed with the new venue
The `user` block (read_status, triage_label, notes) is never touched. This is an in-place
correction of an ingest-time error, not a new version: the paper itself did not change,
only our record of it (see config/metadata_schema.md → "Venue policy").

Usage: python3 scripts/migrations/2026-08-28-venue-fix.py [--dry-run]
Then:  python3 scripts/update_indexes.py && python3 scripts/validate_registry.py
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import paperlib as pl  # noqa: E402
import score_paper  # noqa: E402
from ingest import _venue_tier  # noqa: E402

TABLE = Path(__file__).with_suffix(".yaml")

_FM_RE = re.compile(r"^(venue|year):[ \t]*(.*)$", re.M)


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    return text[4:end], text[end:]


def _frontmatter_ok(path: Path, venue: str, year) -> bool:
    parts = _split_frontmatter(path.read_text(encoding="utf-8"))
    if parts is None:
        return True
    vals = dict(_FM_RE.findall(parts[0]))
    return vals.get("venue", venue).strip() == venue and str(vals.get("year", year)).strip() == str(year)


def _fix_frontmatter(path: Path, venue: str, year) -> None:
    """Summary frontmatter mirrors metadata.yaml's venue/year (written by summarize_paper.py
    --finalize); only those two lines are touched, the prose is never rewritten."""
    text = path.read_text(encoding="utf-8")
    parts = _split_frontmatter(text)
    if parts is None:
        return
    fm, rest = parts

    def sub(m):
        return f"{m.group(1)}: {venue if m.group(1) == 'venue' else year}"

    new_fm = _FM_RE.sub(sub, fm)
    if new_fm != fm:
        path.write_text("---\n" + new_fm + rest, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    table = pl.load_yaml(TABLE) or {}
    rows = table.get("papers") or []
    changed = 0
    for row in rows:
        slug, name = row["slug"], row["venue"]
        pdir = ROOT / "library" / slug
        ppath = pdir / "paper.yaml"
        if not ppath.exists():
            print(f"SKIP {slug}: no paper.yaml", file=sys.stderr)
            continue
        paper = pl.load_yaml(ppath)
        old = dict(paper.get("venue") or {})
        new = {"name": name, "tier": _venue_tier(name),
               "status": row.get("status") or ("preprint" if name.lower() == "arxiv" else "accepted"),
               "year": row.get("year") or old.get("year") or paper.get("year")}
        # An accepted paper's top-level `year` is its publication year (= venue year); the
        # arXiv posting year stays recoverable from the arXiv id. The site card, indexes,
        # milestone ordering and recency scoring all read the top-level `year`.
        pub_year = new["year"] if new["status"] == "accepted" and new["year"] else paper.get("year")
        metas = sorted(pdir.glob("v*/metadata.yaml"))
        summaries = sorted(pdir.glob("v*/summary.mdx"))
        aligned = (old == new and paper.get("year") == pub_year
                   and all((pl.load_yaml(m) or {}).get("venue") == name and (pl.load_yaml(m) or {}).get("year") == pub_year for m in metas)
                   and all(_frontmatter_ok(sp, name, pub_year) for sp in summaries))
        if aligned:
            continue
        print(f"{slug}: {old.get('name')!r}/{old.get('status')}/{paper.get('year')} -> {name!r}/{new['status']}/{pub_year}")
        changed += 1
        if args.dry_run:
            continue
        paper["venue"] = new
        paper["year"] = pub_year
        pl.dump_yaml(ppath, paper)
        for mpath in metas:
            meta = pl.load_yaml(mpath) or {}
            meta["venue"] = name
            meta["year"] = pub_year
            score_input = {**meta, "venue": name, "scoring": meta.get("scoring", {})}
            meta["scoring"] = score_paper.score(score_input)
            pl.dump_yaml(mpath, meta)
        for spath in summaries:
            _fix_frontmatter(spath, name, pub_year)
    print(f"{'would change' if args.dry_run else 'changed'} {changed} paper(s) of {len(rows)} in table")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
