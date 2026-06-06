#!/usr/bin/env python3
"""fetch_semantic_scholar.py — Semantic Scholar enrichment / discovery.

Role: metadata enrichment (paperId, external ids, venue, citation +
influentialCitationCount signals, open-access PDF) and keyword discovery. Not a
PDF source of record. Honors SEMANTIC_SCHOLAR_API_KEY env var if set.

Usage:
    fetch_semantic_scholar.py --arxiv 2501.12345
    fetch_semantic_scholar.py --doi 10.x/y
    fetch_semantic_scholar.py --search "agent harness" --year 2025-
    fetch_semantic_scholar.py --enrich '<candidate json>'
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import paperlib as pl
import fetchlib


def _cfg() -> dict:
    return pl.sources()["sources"]["semantic_scholar"]


def _headers() -> dict:
    cfg = _cfg()
    key = os.environ.get(cfg.get("api_key_env", "SEMANTIC_SCHOLAR_API_KEY"))
    return {"x-api-key": key} if key else {}


def _fields() -> str:
    return ",".join(_cfg().get("fields", [
        "paperId", "externalIds", "title", "abstract", "year", "venue",
        "authors", "citationCount", "influentialCitationCount", "openAccessPdf"]))


def _paper_to_candidate(p: dict) -> dict:
    ext = p.get("externalIds") or {}
    arxiv = ext.get("ArXiv")
    base, ver = (pl.parse_arxiv_id(arxiv) if arxiv else (None, None))
    oa = p.get("openAccessPdf") or {}
    authors = [a.get("name", "") for a in p.get("authors", [])]
    return fetchlib.make_candidate(
        title=p.get("title") or "Untitled",
        source="semantic_scholar",
        source_url=f"https://www.semanticscholar.org/paper/{p.get('paperId')}",
        authors=[a for a in authors if a],
        abstract=p.get("abstract") or "Not reported",
        year=p.get("year"),
        venue=p.get("venue") or "Not reported",
        pdf_url=oa.get("url"),
        ids={"semantic_scholar_id": p.get("paperId"),
             "doi": ext.get("DOI"), "arxiv_base_id": base,
             "arxiv_id": arxiv, "arxiv_version": ver},
        extra={"citation_count": p.get("citationCount"),
               "influential_citation_count": p.get("influentialCitationCount")},
    )


def fetch(args) -> list[dict]:
    base = _cfg()["base_url"]
    h = _headers()
    if args.arxiv:
        base_id, _ = pl.parse_arxiv_id(args.arxiv)
        url = f"{base}/paper/arXiv:{base_id}"
        status, text = fetchlib.http_get(url, params={"fields": _fields()},
                                         headers=h, source="s2", accept_json=True)
        return [_paper_to_candidate(json.loads(text))] if status == 200 else []
    if args.doi:
        url = f"{base}/paper/DOI:{args.doi}"
        status, text = fetchlib.http_get(url, params={"fields": _fields()},
                                         headers=h, source="s2", accept_json=True)
        return [_paper_to_candidate(json.loads(text))] if status == 200 else []
    if args.search:
        url = f"{base}/paper/search"
        params = {"query": args.search, "fields": _fields(), "limit": args.max or 25}
        if args.year:
            params["year"] = args.year
        status, text = fetchlib.http_get(url, params=params, headers=h,
                                         source="s2", accept_json=True)
        data = json.loads(text)
        return [_paper_to_candidate(p) for p in data.get("data", [])]
    return []


def enrich(candidate: dict) -> dict:
    ids = candidate.get("ids") or {}
    try:
        if ids.get("arxiv_base_id"):
            found = fetch(argparse.Namespace(arxiv=ids["arxiv_base_id"], doi=None,
                                             search=None, year=None, max=1))
        elif ids.get("doi"):
            found = fetch(argparse.Namespace(arxiv=None, doi=ids["doi"],
                                             search=None, year=None, max=1))
        else:
            return candidate
    except Exception as e:  # noqa: BLE001
        pl.log_error("fetch.s2.enrich", str(e))
        return candidate
    if not found:
        return candidate
    s2 = found[0]
    candidate.setdefault("ids", {})
    for k in ("semantic_scholar_id", "doi"):
        if s2["ids"].get(k) and not candidate["ids"].get(k):
            candidate["ids"][k] = s2["ids"][k]
    candidate["influential_citation_count"] = s2.get("influential_citation_count")
    if candidate.get("citation_count") is None:
        candidate["citation_count"] = s2.get("citation_count")
    if s2.get("venue") not in (None, "Not reported") and \
            candidate.get("venue") in (None, "arXiv", "Not reported"):
        candidate["venue"] = s2["venue"]
    return candidate


def _main() -> int:
    ap = argparse.ArgumentParser(description="Semantic Scholar enrichment/discovery.")
    ap.add_argument("--arxiv")
    ap.add_argument("--doi")
    ap.add_argument("--search")
    ap.add_argument("--year", help="e.g. 2025 or 2025-")
    ap.add_argument("--max", type=int)
    ap.add_argument("--enrich")
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
        print(f"[dry-run] semantic_scholar: {len(cands)} result(s)")
        return 0
    for c in cands:
        print(json.dumps(c, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
