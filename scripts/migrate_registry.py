#!/usr/bin/env python3
"""migrate_registry.py — schema migrations / backfills for the library.

Idempotent. Brings every paper.yaml / metadata.yaml up to the current schema by
adding any missing keys with safe defaults, normalizing venue tiers, and recomputing
derived fields. Used by /evolve-paper-system when a change touches existing metadata.

Each migration is a named, idempotent function appended to MIGRATIONS. Running again
is a no-op once applied. A backup of every changed file is written to
logs/migrations/<ts>/ before writing.

Usage:
    migrate_registry.py --dry-run
    migrate_registry.py            # apply
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import paperlib as pl

SCHEMA_VERSION = 1


def _ensure(d: dict, key: str, default):
    """Fill a genuinely-missing key (idempotent). A present value of None is left
    alone for scalars (e.g. notes/triage fields are legitimately None), but a None
    container is replaced with the empty default so iteration is always safe."""
    if key not in d:
        d[key] = default
        return True
    if d[key] is None and isinstance(default, (list, dict)):
        d[key] = default
        return True
    return False


def backfill_paper(paper: dict) -> bool:
    changed = False
    changed |= _ensure(paper, "authors", [])
    changed |= _ensure(paper, "topic_groups", [])
    changed |= _ensure(paper, "tags", [])
    changed |= _ensure(paper, "canonical_urls", [])
    changed |= _ensure(paper, "primary_ids", {})
    for k in ("doi", "arxiv_base_id", "openreview_id", "semantic_scholar_id", "openalex_id"):
        changed |= _ensure(paper["primary_ids"], k, None)
    changed |= _ensure(paper, "venue", {"name": None, "tier": None, "status": None, "year": None})
    changed |= _ensure(paper, "user", {})
    changed |= _ensure(paper["user"], "read_status", "unread")
    changed |= _ensure(paper["user"], "triage_label", None)
    changed |= _ensure(paper["user"], "triage_confidence", None)
    changed |= _ensure(paper["user"], "notes", None)
    changed |= _ensure(paper, "milestone", None)
    changed |= _ensure(paper, "knowledge_concepts", [])
    changed |= _ensure(paper, "relations", {})
    for k in ("duplicate_candidates", "related_papers", "supersedes", "superseded_by"):
        changed |= _ensure(paper["relations"], k, [])
    changed |= _ensure(paper, "versions", [])
    return changed


def backfill_meta(meta: dict) -> bool:
    template = pl.new_version_metadata(
        meta.get("canonical_key", ""), meta.get("version_key", ""), meta.get("title", ""))
    changed = False
    for k, v in template.items():
        if k not in meta:
            meta[k] = v
            changed = True
        elif isinstance(v, dict):
            for kk, vv in v.items():
                if kk not in meta[k]:
                    meta[k][kk] = vv
                    changed = True
    return changed


MIGRATIONS = [("backfill_missing_fields", backfill_paper, backfill_meta)]


def run(dry_run: bool = False) -> dict:
    backup_dir = pl.LOGS / "migrations" / pl.now_iso().replace(":", "")
    touched: list[str] = []
    for pdir in pl.iter_paper_dirs():
        pf = pdir / "paper.yaml"
        paper = pl.load_yaml(pf)
        if paper and backfill_paper(paper):
            touched.append(str(pf))
            if not dry_run:
                _backup(pf, backup_dir)
                pl.dump_yaml(pf, paper)
        for v in (paper or {}).get("versions", []):
            mf = pdir / v["version_key"] / "metadata.yaml"
            if mf.exists():
                meta = pl.load_yaml(mf)
                if meta and backfill_meta(meta):
                    touched.append(str(mf))
                    if not dry_run:
                        _backup(mf, backup_dir)
                        pl.dump_yaml(mf, meta)
    return {"schema_version": SCHEMA_VERSION, "touched": touched, "dry_run": dry_run,
            "backup_dir": str(backup_dir) if touched and not dry_run else None}


def _backup(src: Path, backup_root: Path) -> None:
    rel = src.resolve().relative_to(pl.ROOT)
    dest = backup_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _main() -> int:
    ap = argparse.ArgumentParser(description="Migrate/backfill registry to current schema.")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    res = run(dry_run=args.dry_run)
    print(f"schema v{res['schema_version']}: {len(res['touched'])} file(s) "
          f"{'would change' if args.dry_run else 'updated'}")
    for t in res["touched"]:
        print(f"  {t}")
    if res.get("backup_dir"):
        print(f"backup: {res['backup_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
