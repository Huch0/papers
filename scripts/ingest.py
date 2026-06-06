#!/usr/bin/env python3
"""ingest.py — create/update paper records and version directories.

The single safe path for writing into library/. Enforces the versioning rule:
a new arXiv version, a changed PDF sha256, or changed venue/acceptance metadata
creates a NEW version dir; nothing is overwritten. Duplicates are flagged, never
auto-merged.

Used by /add-paper and /daily-papers. Can also be driven from the CLI:

    ingest.py --candidate '<json>'          # ingest one normalized candidate
    ingest.py --candidate '<json>' --pdf <path-or-url>

A "candidate" is a normalized dict (see normalize_candidate / the fetchers):
    {title, authors[], abstract, year, venue, source, source_url, pdf_url,
     source_updated_at, ids:{doi,arxiv_id,arxiv_base_id,arxiv_version,openreview_id,
     semantic_scholar_id,openalex_id}, tags[], topic_groups[], scoring{...}}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import paperlib as pl
import detect_duplicates
import score_paper


def _primary_ids(cand: dict) -> dict:
    ids = cand.get("ids") or {}
    return {
        "doi": ids.get("doi"),
        "arxiv_base_id": ids.get("arxiv_base_id"),
        "openreview_id": ids.get("openreview_id"),
        "semantic_scholar_id": ids.get("semantic_scholar_id"),
        "openalex_id": ids.get("openalex_id"),
    }


def _venue_block(cand: dict) -> dict:
    v = cand.get("venue")
    name = v.get("name") if isinstance(v, dict) else v
    tier = _venue_tier(name)
    return {"name": name, "tier": tier,
            "status": (v.get("status") if isinstance(v, dict) else None) or
                      ("preprint" if (name or "").lower() in ("arxiv", "corr", "") else "unknown"),
            "year": cand.get("year")}


def _venue_tier(name: str | None) -> str:
    if not name:
        return "unknown"
    vcfg = pl.venues()
    aliases = {k.lower(): val for k, val in (vcfg.get("aliases") or {}).items()}
    canon = aliases.get(name.lower(), name).lower()
    for tier, spec in vcfg.get("tiers", {}).items():
        for vn in spec.get("venues", []) or []:
            if vn.lower() in canon:
                return tier
    if canon in ("arxiv", "corr", "preprint"):
        return "workshop_or_minor"
    return "unknown"


_GENERIC_VENUES = {"", "arxiv", "corr", "preprint", "not reported", "openreview"}


def _is_new_version(latest_meta: dict, cand: dict, pdf_sha: str | None) -> tuple[bool, str]:
    """Decide whether cand differs enough from the latest version to warrant a new one.

    A new version is warranted by: a new arXiv version, a changed PDF sha256, or a
    *material* venue change. A venue is only material when both the old and new values
    are specific and differ — downgrading a known venue (e.g. 'ICLR') back to a generic
    source label ('arXiv') is NOT material (it just means this candidate came from a
    less-enriched source), so re-running discovery never spawns spurious versions.
    """
    if latest_meta is None:
        return True, "first version"
    old_ids = latest_meta.get("ids") or {}
    new_av = (cand.get("ids") or {}).get("arxiv_version")
    old_av = old_ids.get("arxiv_version")
    if new_av and old_av and new_av != old_av:
        return True, f"arxiv version {old_av} -> {new_av}"
    if pdf_sha and latest_meta.get("pdf_sha256") and pdf_sha != latest_meta["pdf_sha256"]:
        return True, "pdf sha256 changed"
    old_venue = str(latest_meta.get("venue") or "").strip()
    new_v = cand.get("venue")
    new_venue = (new_v.get("name") if isinstance(new_v, dict) else (new_v or "")).strip()
    if (new_venue and new_venue.lower() not in _GENERIC_VENUES
            and old_venue.lower() != new_venue.lower()):
        return True, f"venue '{old_venue}' -> '{new_venue}'"
    return False, "no material change"


def ingest(cand: dict, pdf_source: str | None = None, *,
           force_new_version: bool = False, dry_run: bool = False) -> dict:
    """Ingest one candidate. pdf_source: a local path or URL to fetch.
    Returns a result dict describing what happened."""
    title = cand.get("title") or (cand.get("ids") or {}).get("arxiv_base_id") or "Untitled"
    pids = _primary_ids(cand)
    canonical_key = derive_key_with_aliases(pids, title)
    slug = pl.derive_slug(canonical_key, title)

    # duplicate check against the rest of the library (not the same canonical key)
    dup_hits = [h for h in detect_duplicates.check_candidate(cand)
                if h["canonical_key"] != canonical_key]

    existing_dir = pl.find_paper_by_key(canonical_key)
    paper_dir = existing_dir or (pl.LIBRARY / slug)
    paper = pl.load_yaml(paper_dir / "paper.yaml") if existing_dir else \
        pl.new_paper_record(canonical_key, paper_dir.name, title)

    # latest version metadata for diffing
    latest_meta = None
    if paper.get("versions"):
        lv = paper["versions"][-1]["version_key"]
        latest_meta = pl.load_yaml(paper_dir / lv / "metadata.yaml")

    # resolve pdf sha if a local file is provided up front
    pdf_sha = None
    local_pdf = None
    if pdf_source and Path(pdf_source).exists():
        local_pdf = Path(pdf_source)
        pdf_sha = pl.sha256_file(local_pdf)

    make_new, reason = (True, "forced") if force_new_version else \
        _is_new_version(latest_meta, cand, pdf_sha)

    result = {
        "canonical_key": canonical_key, "slug": paper_dir.name,
        "is_new_paper": existing_dir is None, "duplicate_candidates": dup_hits,
        "dry_run": dry_run,
    }

    if not make_new and existing_dir is not None:
        result.update({"action": "unchanged", "reason": reason,
                       "version_key": paper["versions"][-1]["version_key"]})
        if dup_hits:
            _record_dups(canonical_key, dup_hits, dry_run)
        return result

    version_key = pl.next_version_key(paper)
    vdir = paper_dir / version_key
    result.update({"action": "new_version" if existing_dir else "new_paper",
                   "version_key": version_key, "reason": reason,
                   "version_dir": pl.rel(vdir)})

    if dry_run:
        if dup_hits:
            result["note"] = "duplicate candidates detected (not written in dry-run)"
        return result

    vdir.mkdir(parents=True, exist_ok=True)

    # build version metadata
    meta = pl.new_version_metadata(canonical_key, version_key, title)
    meta.update({
        "authors": cand.get("authors") or [],
        "abstract": cand.get("abstract") or "Not reported",
        "venue": (cand.get("venue") or {}).get("name") if isinstance(cand.get("venue"), dict) else cand.get("venue"),
        "year": cand.get("year"),
        "source": cand.get("source"),
        "source_url": cand.get("source_url"),
        "pdf_url": cand.get("pdf_url"),
        "source_updated_at": cand.get("source_updated_at"),
        "ids": {**meta["ids"], **(cand.get("ids") or {})},
        "tags": cand.get("tags") or [],
        "topic_groups": cand.get("topic_groups") or [],
    })
    meta["artifacts"]["code_url"] = cand.get("code_url")
    meta["artifacts"]["project_url"] = cand.get("project_url")

    # PDF: copy local, or download from url
    pdf_path = None
    if local_pdf:
        pdf_path = vdir / "paper.pdf"
        pdf_path.write_bytes(local_pdf.read_bytes())
    elif pdf_source and pdf_source.startswith("http"):
        try:
            import download_pdf
            info = download_pdf.download(pdf_source, vdir / "paper.pdf")
            pdf_path = vdir / "paper.pdf"
            meta["pdf_sha256"] = info["pdf_sha256"]
        except Exception as e:  # noqa: BLE001
            pl.log_error("ingest.download", str(e), key=canonical_key)
            result["pdf_error"] = str(e)

    if pdf_path and pdf_path.exists():
        meta["pdf_sha256"] = pl.sha256_file(pdf_path)
        meta["artifacts"]["pdf"] = pl.rel(pdf_path)
        meta["status"]["downloaded"] = True
        pdf_bytes = pl.file_bytes(pdf_path)
    else:
        pdf_bytes = None

    # heuristic scoring at ingest time
    score_input = {**meta, "venue": meta["venue"], "scoring": meta.get("scoring", {})}
    meta["scoring"] = score_paper.score(score_input)
    meta["status"]["triaged"] = True

    pl.dump_yaml(vdir / "metadata.yaml", meta)
    # ensure placeholder artifact files exist for colocation discipline
    (vdir / "notes.md").touch(exist_ok=True)

    # update paper-level record
    paper["title"] = paper.get("title") or title
    paper["authors"] = paper.get("authors") or cand.get("authors") or []
    paper["year"] = paper.get("year") or cand.get("year")
    paper["primary_ids"] = {**paper.get("primary_ids", {}), **{k: v for k, v in pids.items() if v}}
    paper["topic_groups"] = sorted(set((paper.get("topic_groups") or []) + (cand.get("topic_groups") or [])))
    paper["tags"] = sorted(set((paper.get("tags") or []) + (cand.get("tags") or [])))
    # milestone: curated landmark marker (from /milestone-papers). Implies foundational.
    if cand.get("milestone"):
        paper["milestone"] = cand["milestone"]
        if "foundational" not in paper["tags"]:
            paper["tags"] = sorted(paper["tags"] + ["foundational"])
    paper.setdefault("knowledge_concepts", [])
    paper["venue"] = _venue_block(cand) if (cand.get("venue") or not paper.get("venue", {}).get("name")) else paper["venue"]
    paper.setdefault("user", {})
    paper["user"]["triage_label"] = meta["scoring"]["label"]
    paper["user"]["triage_confidence"] = meta["scoring"]["confidence"]
    paper["user"].setdefault("read_status", "unread")
    for u in (cand.get("source_url"), cand.get("pdf_url")):
        if u and u not in paper["canonical_urls"]:
            paper["canonical_urls"].append(u)

    ver_entry = {
        "version_key": version_key,
        "version_label": cand.get("version_label") or
            (f"arXiv {cand.get('ids', {}).get('arxiv_version')}" if cand.get("ids", {}).get("arxiv_version") else cand.get("source") or "ingested"),
        "source": cand.get("source"),
        "source_url": cand.get("source_url"),
        "pdf_path": pl.rel(pdf_path) if pdf_path and pdf_path.exists() else None,
        "summary_path": None,
        "metadata_path": pl.rel(vdir / "metadata.yaml"),
        "fetched_at": pl.now_iso(),
        "source_updated_at": cand.get("source_updated_at"),
        "arxiv_version": cand.get("ids", {}).get("arxiv_version"),
        "pdf_sha256": meta.get("pdf_sha256"),
        "pdf_bytes": pdf_bytes,
        "summary_status": "none",
        "extraction_status": "none",
        "created_at": pl.now_iso(),
        "updated_at": pl.now_iso(),
    }
    # supersession bookkeeping
    if paper.get("versions"):
        prev = paper["versions"][-1]["version_key"]
        result["supersedes_version"] = prev
    paper["versions"].append(ver_entry)

    pl.dump_yaml(paper_dir / "paper.yaml", paper)

    if dup_hits:
        _record_dups(canonical_key, dup_hits, dry_run)
        paper["relations"]["duplicate_candidates"] = sorted(set(
            (paper["relations"].get("duplicate_candidates") or []) +
            [h["canonical_key"] for h in dup_hits]))
        pl.dump_yaml(paper_dir / "paper.yaml", paper)

    result["score"] = meta["scoring"]["score"]
    result["label"] = meta["scoring"]["label"]
    return result


def derive_key_with_aliases(pids: dict, title: str) -> str:
    key = pl.derive_canonical_key(pids, title)
    aliases = (pl.load_yaml(pl.ALIASES) or {}).get("aliases") or {}
    return aliases.get(key, key)


def _record_dups(key: str, hits: list[dict], dry_run: bool) -> None:
    if dry_run:
        return
    for h in hits:
        pl.append_jsonl(pl.DUP_CANDIDATES, {
            "ts": pl.now_iso(), "a": key, "b": h["canonical_key"],
            "confidence": h["confidence"], "reasons": h["reasons"], "resolved": False})


def _main() -> int:
    ap = argparse.ArgumentParser(description="Ingest a normalized candidate.")
    ap.add_argument("--candidate", required=True, help="JSON normalized candidate")
    ap.add_argument("--pdf", help="local PDF path or URL to attach")
    ap.add_argument("--force-new-version", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cand = json.loads(args.candidate)
    res = ingest(cand, args.pdf, force_new_version=args.force_new_version, dry_run=args.dry_run)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
