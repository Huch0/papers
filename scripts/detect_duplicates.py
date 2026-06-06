#!/usr/bin/env python3
"""detect_duplicates.py — find probable duplicate papers.

Signals: arXiv base id, DOI, OpenReview id, Semantic Scholar id, normalized title
hash, author overlap, PDF sha256. Never auto-merges. Writes ambiguous candidates to
registry/duplicate_candidates.jsonl for human/`/evolve-paper-system` review.

Usage:
    detect_duplicates.py                 # scan whole library, write candidates
    detect_duplicates.py --candidate '<json>'   # check one candidate vs library
"""
from __future__ import annotations

import argparse
import json

import paperlib as pl


def _ids(paper: dict) -> dict:
    pid = paper.get("primary_ids") or {}
    return {k: (v or "").strip().lower() if isinstance(v, str) else v
            for k, v in pid.items()}


def _author_set(paper: dict) -> set[str]:
    return {a.strip().lower() for a in (paper.get("authors") or []) if a.strip()}


def _pdf_hashes(paper: dict) -> set[str]:
    out = set()
    for v in paper.get("versions") or []:
        if v.get("pdf_sha256"):
            out.add(v["pdf_sha256"])
    return out


def compare(a: dict, b: dict) -> tuple[float, list[str]]:
    """Return (confidence 0..1, reasons)."""
    reasons: list[str] = []
    conf = 0.0
    ia, ib = _ids(a), _ids(b)
    for k in ("arxiv_base_id", "doi", "openreview_id", "semantic_scholar_id", "openalex_id"):
        if ia.get(k) and ia.get(k) == ib.get(k):
            reasons.append(f"same {k}")
            conf = max(conf, 0.99)
    ha, hb = _pdf_hashes(a), _pdf_hashes(b)
    if ha & hb:
        reasons.append("identical PDF sha256")
        conf = max(conf, 0.97)
    if pl.title_hash(a.get("title", "")) == pl.title_hash(b.get("title", "")) and a.get("title"):
        reasons.append("identical normalized title")
        conf = max(conf, 0.9)
        sa, sb = _author_set(a), _author_set(b)
        if sa and sb:
            overlap = len(sa & sb) / max(1, min(len(sa), len(sb)))
            if overlap >= 0.5:
                reasons.append(f"author overlap {overlap:.0%}")
                conf = max(conf, 0.95)
    return conf, reasons


def scan() -> list[dict]:
    papers = list(pl.iter_papers())
    cands: list[dict] = []
    for i in range(len(papers)):
        for j in range(i + 1, len(papers)):
            a, b = papers[i], papers[j]
            if a.get("canonical_key") == b.get("canonical_key"):
                continue
            conf, reasons = compare(a, b)
            if conf >= 0.85:
                cands.append({
                    "ts": pl.now_iso(),
                    "a": a.get("canonical_key"),
                    "b": b.get("canonical_key"),
                    "confidence": round(conf, 2),
                    "reasons": reasons,
                    "resolved": False,
                })
    return cands


def check_candidate(cand: dict) -> list[dict]:
    """Compare a raw candidate (with title/authors/ids) against the library."""
    norm = {
        "title": cand.get("title", ""),
        "authors": cand.get("authors", []),
        "primary_ids": cand.get("ids") or cand.get("primary_ids") or {},
        "versions": [{"pdf_sha256": cand.get("pdf_sha256")}] if cand.get("pdf_sha256") else [],
    }
    hits = []
    for p in pl.iter_papers():
        conf, reasons = compare(norm, p)
        if conf >= 0.85:
            hits.append({"canonical_key": p.get("canonical_key"),
                         "confidence": round(conf, 2), "reasons": reasons})
    return hits


def _main() -> int:
    ap = argparse.ArgumentParser(description="Detect duplicate papers.")
    ap.add_argument("--candidate", help="JSON candidate to check against the library")
    ap.add_argument("--write", action="store_true", default=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.candidate:
        hits = check_candidate(json.loads(args.candidate))
        print(json.dumps(hits, indent=2))
        return 0

    cands = scan()
    # merge with existing, de-dup on (a,b) unresolved pairs
    existing = pl.read_jsonl(pl.DUP_CANDIDATES)
    seen = {(c["a"], c["b"]) for c in existing}
    new = [c for c in cands if (c["a"], c["b"]) not in seen]
    if new:
        for c in new:
            pl.append_jsonl(pl.DUP_CANDIDATES, c)
    if args.json:
        print(json.dumps(cands, indent=2))
    else:
        print(f"duplicate scan: {len(cands)} candidate pair(s), {len(new)} new.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
