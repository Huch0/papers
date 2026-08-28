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
import argparse, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import paperlib as pl  # noqa: E402
import score_paper  # noqa: E402
from ingest import _venue_tier  # noqa: E402

TABLE = Path(__file__).with_suffix(".yaml")


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
        if old == new and all(
            (pl.load_yaml(m) or {}).get("venue") == name for m in sorted(pdir.glob("v*/metadata.yaml"))
        ):
            continue
        print(f"{slug}: {old.get('name')!r}/{old.get('status')} -> {name!r}/{new['status']}/{new['year']}")
        changed += 1
        if args.dry_run:
            continue
        paper["venue"] = new
        pl.dump_yaml(ppath, paper)
        for mpath in sorted(pdir.glob("v*/metadata.yaml")):
            meta = pl.load_yaml(mpath) or {}
            meta["venue"] = name
            if meta.get("year") is None and new["year"]:
                meta["year"] = new["year"]
            score_input = {**meta, "venue": name, "scoring": meta.get("scoring", {})}
            meta["scoring"] = score_paper.score(score_input)
            pl.dump_yaml(mpath, meta)
    print(f"{'would change' if args.dry_run else 'changed'} {changed} paper(s) of {len(rows)} in table")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
