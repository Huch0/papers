#!/usr/bin/env python3
"""fetch_openalex.py — OpenAlex enrichment / discovery.

Primary role: metadata enrichment (venue normalization, citation/influence signal,
related works, OpenAlex work id, DOI) and lightweight discovery. NOT a PDF source.

Usage:
    fetch_openalex.py --doi 10.xxxx/yyyy
    fetch_openalex.py --arxiv 2501.12345
    fetch_openalex.py --title "Some Paper Title"
    fetch_openalex.py --search "agent harness" --since 2025-01-01
    fetch_openalex.py --enrich '<candidate json>'      # merge signals into a candidate
"""
from __future__ import annotations

import argparse
import json
import sys

import paperlib as pl
import fetchlib


def _cfg() -> dict:
    return pl.sources()["sources"]["openalex"]


def _reconstruct_abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inv.items():
        for i in idxs:
            positions.append((i, word))
    positions.sort()
    return " ".join(w for _, w in positions)[:3000] or None


def _work_to_candidate(w: dict) -> dict:
    ids = w.get("ids", {})
    doi = (w.get("doi") or "").replace("https://doi.org/", "") or None
    host = w.get("primary_location") or {}
    src = (host.get("source") or {}) or {}
    venue = src.get("display_name")
    pdf_url = host.get("pdf_url")
    arxiv_base = None
    for loc in w.get("locations", []) or []:
        lid = ((loc.get("source") or {}).get("display_name") or "")
        if "arxiv" in lid.lower():
            landing = loc.get("landing_page_url", "")
            arxiv_base, _ = pl.parse_arxiv_id(landing)
    authors = [a.get("author", {}).get("display_name", "")
               for a in w.get("authorships", [])]
    cand = fetchlib.make_candidate(
        title=w.get("title") or w.get("display_name") or "Untitled",
        source="openalex",
        source_url=w.get("id"),
        authors=[a for a in authors if a],
        abstract=_reconstruct_abstract(w.get("abstract_inverted_index")) or "Not reported",
        year=w.get("publication_year"),
        venue=venue or "Not reported",
        pdf_url=pdf_url,
        source_updated_at=w.get("publication_date"),
        ids={"doi": doi, "openalex_id": w.get("id"),
             "arxiv_base_id": arxiv_base},
        extra={
            "citation_count": w.get("cited_by_count"),
            "openalex_concepts": [c.get("display_name") for c in w.get("concepts", [])[:6]],
            "related_works": w.get("related_works", [])[:8],
            "is_oa": (w.get("open_access") or {}).get("is_oa"),
        },
    )
    return cand


def fetch(args) -> list[dict]:
    cfg = _cfg()
    base = cfg["base_url"]
    mailto = cfg.get("mailto") or pl.sources().get("defaults", {}).get("contact_email")
    common = {"mailto": mailto} if mailto else {}

    if args.doi:
        status, text = fetchlib.http_get(f"{base}/doi:{args.doi}", params=common, source="openalex")
        return [_work_to_candidate(json.loads(text))] if status == 200 else []
    if args.arxiv:
        # OpenAlex indexes arxiv via DOI 10.48550/arXiv.<id>
        doi = f"10.48550/arXiv.{args.arxiv}"
        try:
            status, text = fetchlib.http_get(f"{base}/doi:{doi}", params=common, source="openalex")
            if status == 200:
                return [_work_to_candidate(json.loads(text))]
        except Exception:  # noqa: BLE001
            pass
        return []

    params = dict(common)
    filters = []
    if args.since:
        filters.append(f"from_publication_date:{args.since}")
    if args.title:
        params["filter"] = ",".join(filters + [f"title.search:{args.title}"]) if filters else None
        params.setdefault("search", args.title)
    elif args.search:
        params["search"] = args.search
        if filters:
            params["filter"] = ",".join(filters)
    params["per_page"] = args.max or 25
    params = {k: v for k, v in params.items() if v is not None}
    status, text = fetchlib.http_get(base, params=params, source="openalex")
    data = json.loads(text)
    return [_work_to_candidate(w) for w in data.get("results", [])]


def enrich(candidate: dict) -> dict:
    """Merge OpenAlex signals (venue, citations, related, ids) into a candidate."""
    ids = candidate.get("ids") or {}
    found = []
    try:
        if ids.get("doi"):
            found = fetch(argparse.Namespace(doi=ids["doi"], arxiv=None, title=None,
                                             search=None, since=None, max=1))
        elif ids.get("arxiv_base_id"):
            found = fetch(argparse.Namespace(doi=None, arxiv=ids["arxiv_base_id"],
                                             title=None, search=None, since=None, max=1))
    except Exception as e:  # noqa: BLE001
        pl.log_error("fetch.openalex.enrich", str(e))
        return candidate
    if not found:
        return candidate
    oa = found[0]
    candidate.setdefault("ids", {})
    for k in ("openalex_id", "doi"):
        if oa["ids"].get(k) and not candidate["ids"].get(k):
            candidate["ids"][k] = oa["ids"][k]
    if oa.get("venue") and (not candidate.get("venue") or candidate.get("venue") == "arXiv"):
        if oa["venue"] not in (None, "Not reported"):
            candidate["venue"] = oa["venue"]
    candidate["citation_count"] = oa.get("citation_count")
    candidate["related_works"] = oa.get("related_works")
    return candidate


def _main() -> int:
    ap = argparse.ArgumentParser(description="OpenAlex enrichment/discovery.")
    ap.add_argument("--doi")
    ap.add_argument("--arxiv")
    ap.add_argument("--title")
    ap.add_argument("--search")
    ap.add_argument("--since")
    ap.add_argument("--max", type=int)
    ap.add_argument("--enrich", help="candidate JSON to enrich")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.enrich:
        print(json.dumps(enrich(json.loads(args.enrich)), ensure_ascii=False))
        return 0
    try:
        cands = fetch(args)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[dry-run] openalex: {len(cands)} result(s)")
        return 0
    for c in cands:
        print(json.dumps(c, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
