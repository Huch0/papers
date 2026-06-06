#!/usr/bin/env python3
"""fetch_arxiv.py — primary discovery source.

Queries the arXiv API by configured categories + interest keywords, for a date
window, sorted by submittedDate and lastUpdatedDate. Emits normalized candidate
JSONL to stdout (and optionally to inbox/<date>/candidates.jsonl). Does NOT write
into library/.

Usage:
    fetch_arxiv.py --since 3d
    fetch_arxiv.py --from 2026-06-01 --to 2026-06-06
    fetch_arxiv.py --id 2501.12345          # single paper lookup (for /add-paper)
    fetch_arxiv.py --since 2d --tags agent_harness,computer_use_agents
    fetch_arxiv.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

import paperlib as pl
import fetchlib

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def _parse_window(args) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if args.id:
        return now - timedelta(days=3650), now
    if args.from_ or args.to:
        start = pl.parse_date(args.from_) or (now - timedelta(days=2))
        end = pl.parse_date(args.to) or now
        return start, end
    if args.since:
        m = re.fullmatch(r"(\d+)([dwh])", args.since)
        if m:
            n = int(m.group(1))
            unit = {"d": "days", "w": "weeks", "h": "hours"}[m.group(2)]
            return now - timedelta(**{unit: n}), now
        d = pl.parse_date(args.since)
        if d:
            return d, now
    days = pl.sources().get("defaults", {}).get("since_days", 2)
    return now - timedelta(days=days), now


def _build_query(categories: list[str], tags: list[str] | None) -> str:
    groups = pl.interests().get("topic_groups", {})
    if tags:
        groups = {k: v for k, v in groups.items() if k in tags}
    kws: list[str] = []
    for g in groups.values():
        kws.extend(g.get("keywords", []))
    # de-dup, keep multiword phrases quoted
    seen = []
    for k in kws:
        if k not in seen:
            seen.append(k)
    kw_clause = " OR ".join(f'all:"{k}"' if " " in k else f"all:{k}" for k in seen[:40])
    cat_clause = " OR ".join(f"cat:{c}" for c in categories)
    return f"({cat_clause}) AND ({kw_clause})"


def _entry_to_candidate(entry: ET.Element) -> dict:
    def t(tag):
        el = entry.find(ATOM + tag)
        return (el.text or "").strip() if el is not None and el.text else None

    arxiv_url = None
    pdf_url = None
    doi = None
    for link in entry.findall(ATOM + "link"):
        rel = link.get("rel")
        title_attr = link.get("title")
        href = link.get("href")
        if title_attr == "pdf":
            pdf_url = href
        elif rel == "alternate":
            arxiv_url = href
        elif title_attr == "doi":
            doi = href

    doi_el = entry.find(ARXIV_NS + "doi")
    if doi_el is not None and doi_el.text:
        doi = doi_el.text.strip()

    id_url = t("id") or ""
    base, ver = pl.parse_arxiv_id(id_url)
    arxiv_id = f"{base}{ver or ''}" if base else None

    authors = [a.findtext(ATOM + "name", default="").strip()
               for a in entry.findall(ATOM + "author")]
    authors = [a for a in authors if a]

    primary_cat = entry.find(ARXIV_NS + "primary_category")
    cat = primary_cat.get("term") if primary_cat is not None else None

    journal_ref = entry.find(ARXIV_NS + "journal_ref")
    venue = journal_ref.text.strip() if journal_ref is not None and journal_ref.text else "arXiv"

    updated = t("updated")
    published = t("published")
    year = None
    if published:
        try:
            year = int(published[:4])
        except ValueError:
            pass

    title = re.sub(r"\s+", " ", t("title") or "").strip()
    summary = re.sub(r"\s+", " ", t("summary") or "").strip()

    cand = fetchlib.make_candidate(
        title=title, source="arxiv", source_url=arxiv_url or id_url,
        authors=authors, abstract=summary or "Not reported", year=year,
        venue=venue, pdf_url=pdf_url,
        source_updated_at=updated or published,
        ids={"arxiv_id": arxiv_id, "arxiv_base_id": base, "arxiv_version": ver, "doi": doi},
        extra={"arxiv_primary_category": cat, "version_label": f"arXiv {ver}" if ver else "arXiv"},
    )
    return cand


def _query(params: dict, source_label: str) -> list[ET.Element]:
    base = pl.sources()["sources"]["arxiv"]["base_url"]
    status, text = fetchlib.http_get(base, params=params, source=source_label)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        pl.log_error("fetch.arxiv", f"XML parse error: {e}")
        return []
    return root.findall(ATOM + "entry")


def fetch(args) -> list[dict]:
    src = pl.sources()["sources"]["arxiv"]
    if not src.get("enabled", True) and not args.id:
        return []
    start, end = _parse_window(args)
    tags = args.tags.split(",") if args.tags else None
    max_results = args.max or pl.sources().get("defaults", {}).get("max_results_per_source", 60)
    min_gap = src.get("min_seconds_between_requests", 3.0)

    candidates: dict[str, dict] = {}

    if args.id:
        base_id, _ = pl.parse_arxiv_id(args.id)
        entries = _query({"id_list": base_id or args.id, "max_results": 1}, "arxiv_id")
        for e in entries:
            c = _entry_to_candidate(e)
            candidates[c["ids"]["arxiv_base_id"] or c["title"]] = c
        return list(candidates.values())

    query = _build_query(src.get("categories", []), tags)
    for view in src.get("sort_views", ["submittedDate", "lastUpdatedDate"]):
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": view,
            "sortOrder": "descending",
        }
        entries = _query(params, f"arxiv_{view}")
        for e in entries:
            c = _entry_to_candidate(e)
            d = pl.parse_date(c.get("source_updated_at"))
            if d and not (start <= d <= end):
                continue
            key = c["ids"]["arxiv_base_id"] or c["title"]
            # keep the newer-updated record on conflict
            if key not in candidates:
                candidates[key] = c
        time.sleep(min_gap)

    pl.log_fetch("arxiv", window=[start.isoformat(), end.isoformat()],
                 categories=src.get("categories"), found=len(candidates))
    return list(candidates.values())


def _main() -> int:
    ap = argparse.ArgumentParser(description="Fetch candidate papers from arXiv.")
    ap.add_argument("--since", help="e.g. 3d, 1w, 12h, or a YYYY-MM-DD date")
    ap.add_argument("--from", dest="from_", help="YYYY-MM-DD")
    ap.add_argument("--to", help="YYYY-MM-DD")
    ap.add_argument("--id", help="single arXiv id/url lookup")
    ap.add_argument("--tags", help="comma-separated topic groups to restrict query")
    ap.add_argument("--max", type=int, help="max results per view")
    ap.add_argument("--out", help="also append candidates to this JSONL path")
    ap.add_argument("--dry-run", action="store_true", help="print count only")
    args = ap.parse_args()

    try:
        cands = fetch(args)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[dry-run] arxiv: {len(cands)} candidate(s)")
        for c in cands[:10]:
            print(f"  - {c['ids']['arxiv_base_id']}: {c['title'][:80]}")
        return 0

    if args.out:
        for c in cands:
            pl.append_jsonl(args.out, c)
    for c in cands:
        print(json.dumps(c, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
