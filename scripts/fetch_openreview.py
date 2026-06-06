#!/usr/bin/env python3
"""fetch_openreview.py — OpenReview discovery / metadata (API v2).

Tracks OpenReview id, forum URL, venue, decision (when available), and PDF URL for
ICLR/NeurIPS/ICML/ACL-ARR forums where practical. Best-effort: OpenReview's API
shape varies by venue/year, so failures are logged and degrade gracefully.

Usage:
    fetch_openreview.py --forum <id>
    fetch_openreview.py --venue ICLR.cc/2025/Conference --max 50
    fetch_openreview.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys

import paperlib as pl
import fetchlib


def _base() -> str:
    return pl.sources()["sources"]["openreview"]["base_url"]


def _note_to_candidate(note: dict) -> dict:
    content = note.get("content") or {}

    def val(field):
        v = content.get(field)
        if isinstance(v, dict):
            return v.get("value")
        return v

    nid = note.get("id")
    forum = note.get("forum") or nid
    title = val("title") or "Untitled"
    authors = val("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    abstract = val("abstract") or "Not reported"
    venue = val("venue") or val("venueid")
    pdf = val("pdf")
    pdf_url = (f"https://openreview.net{pdf}" if pdf and pdf.startswith("/")
               else (f"https://openreview.net/pdf?id={nid}" if pdf else None))
    decision = val("decision") or val("recommendation")

    year = None
    if isinstance(venue, str):
        import re
        m = re.search(r"(20\d{2})", venue)
        if m:
            year = int(m.group(1))

    return fetchlib.make_candidate(
        title=title, source="openreview",
        source_url=f"https://openreview.net/forum?id={forum}",
        authors=authors if isinstance(authors, list) else [],
        abstract=abstract, year=year, venue=venue or "OpenReview",
        pdf_url=pdf_url,
        ids={"openreview_id": nid},
        extra={"decision": decision, "venue_status": decision},
    )


def fetch(args) -> list[dict]:
    base = _base()
    if args.forum:
        url = f"{base}/notes"
        status, text = fetchlib.http_get(url, params={"forum": args.forum},
                                         source="openreview", accept_json=True)
        notes = json.loads(text).get("notes", [])
        return [_note_to_candidate(n) for n in notes if (n.get("content") or {}).get("title")]
    if args.venue:
        url = f"{base}/notes"
        params = {"content.venueid": args.venue, "limit": args.max or 50,
                  "details": "directReplies"}
        try:
            status, text = fetchlib.http_get(url, params=params,
                                             source="openreview", accept_json=True)
            notes = json.loads(text).get("notes", [])
        except Exception as e:  # noqa: BLE001
            pl.log_error("fetch.openreview", str(e), venue=args.venue)
            return []
        return [_note_to_candidate(n) for n in notes if (n.get("content") or {}).get("title")]
    return []


def _main() -> int:
    ap = argparse.ArgumentParser(description="OpenReview discovery/metadata.")
    ap.add_argument("--forum", help="forum / note id")
    ap.add_argument("--venue", help="venueid, e.g. ICLR.cc/2025/Conference")
    ap.add_argument("--max", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        cands = fetch(args)
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"[dry-run] openreview: {len(cands)} result(s)")
        return 0
    for c in cands:
        print(json.dumps(c, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
