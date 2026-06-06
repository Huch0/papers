#!/usr/bin/env python3
"""fetch_milestones.py — resolve curated milestone seeds into real paper candidates.

Reads config/milestones.yaml. For each seed it resolves a real record (arXiv id when
given, else Semantic Scholar / OpenAlex title search with a match check), attaches a
`milestone` block + `foundational` tag + the field's topic_group, and flags whether the
paper is already in the registry (so the skill never re-adds duplicates). Optionally
augments with live high-citation discovery (`--discover`).

Emits normalized candidate JSONL (same shape ingest.py consumes). Does NOT write into
library/ — the /milestone-papers skill reviews and ingests.

Usage:
    fetch_milestones.py --field computer_use_agents
    fetch_milestones.py --field computer_use_agents --discover
    fetch_milestones.py --all
    fetch_milestones.py --field agent_harness --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys

import paperlib as pl
import fetchlib
import fetch_arxiv
import fetch_semantic_scholar
import fetch_openalex


def _existing_keys() -> set[str]:
    keys = set()
    for p in pl.iter_papers():
        keys.add(p.get("canonical_key"))
        pid = p.get("primary_ids") or {}
        for k in ("arxiv_base_id", "doi", "openreview_id", "semantic_scholar_id"):
            if pid.get(k):
                keys.add(pid[k])
    return keys


def _existing_titles() -> dict[str, str]:
    return {pl.normalize_title(p.get("title", "")): p.get("canonical_key")
            for p in pl.iter_papers() if p.get("title")}


def _title_match(a: str, b: str) -> float:
    na, nb = pl.normalize_title(a), pl.normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    inter = len(ta & tb)
    return inter / max(1, min(len(ta), len(tb)))


def _resolve_seed(seed: dict) -> tuple[dict | None, str]:
    """Resolve a seed to a candidate. Returns (candidate, confidence-note)."""
    title = seed.get("title", "")
    arxiv = (seed.get("arxiv") or "").strip()
    if arxiv:
        try:
            cands = fetch_arxiv.fetch(argparse.Namespace(
                since=None, from_=None, to=None, id=arxiv, tags=None, max=1,
                out=None, dry_run=False))
            if cands:
                return cands[0], f"arxiv:{arxiv}"
        except Exception as e:  # noqa: BLE001
            pl.log_error("milestones.resolve", f"arxiv {arxiv}: {e}")

    # title search: Semantic Scholar first, then OpenAlex
    for fn, label in ((_s2_title, "s2"), (_oa_title, "openalex")):
        try:
            cand = fn(title)
        except Exception as e:  # noqa: BLE001
            pl.log_error("milestones.resolve", f"{label} '{title}': {e}")
            cand = None
        if cand:
            score = _title_match(title, cand.get("title", ""))
            if score >= 0.6:
                return cand, f"{label}:match={score:.2f}"
    return None, "unresolved"


def _s2_title(title: str) -> dict | None:
    res = fetch_semantic_scholar.fetch(argparse.Namespace(
        arxiv=None, doi=None, search=title, year=None, max=5))
    best, bs = None, 0.0
    for c in res:
        s = _title_match(title, c.get("title", ""))
        if s > bs:
            best, bs = c, s
    return best


def _oa_title(title: str) -> dict | None:
    res = fetch_openalex.fetch(argparse.Namespace(
        doi=None, arxiv=None, title=title, search=None, since=None, max=5))
    best, bs = None, 0.0
    for c in res:
        s = _title_match(title, c.get("title", ""))
        if s > bs:
            best, bs = c, s
    return best


def _apply_milestone(cand: dict, field: str, seed: dict, topic_group: str) -> dict:
    cand.setdefault("tags", [])
    for t in ("foundational",):
        if t not in cand["tags"]:
            cand["tags"].append(t)
    tg = set(cand.get("topic_groups") or [])
    tg.add(topic_group)
    cand["topic_groups"] = sorted(tg)
    cand["milestone"] = {
        "field": field,
        "era": seed.get("era", "foundational"),
        "significance": seed.get("significance", ""),
    }
    return cand


def fetch_field(field: str, fcfg: dict, *, discover: bool = False) -> list[dict]:
    topic_group = fcfg.get("topic_group", field)
    existing = _existing_keys()
    existing_titles = _existing_titles()
    out: list[dict] = []

    for seed in fcfg.get("seeds", []):
        cand, note = _resolve_seed(seed)
        if not cand:
            out.append({"_seed": seed.get("title"), "_unresolved": True, "_note": note,
                        "milestone": {"field": field, "era": seed.get("era"),
                                      "significance": seed.get("significance")}})
            continue
        cand = _apply_milestone(cand, field, seed, topic_group)
        ck = pl.derive_canonical_key(_cand_primary_ids(cand), cand.get("title", ""))
        cand["_canonical_key"] = ck
        cand["_resolution"] = note
        cand["_already_known"] = (ck in existing or
                                  pl.normalize_title(cand.get("title", "")) in existing_titles)
        out.append(cand)

    if discover:
        out.extend(_discover(field, fcfg, topic_group, existing, existing_titles,
                             {pl.normalize_title(c.get("title", "")) for c in out if c.get("title")}))
    return out


def _discover(field, fcfg, topic_group, existing, existing_titles, seen_titles) -> list[dict]:
    disc = pl.milestones_cfg().get("discovery", {})
    n = disc.get("per_field_suggestions", 15)
    min_inf = disc.get("min_influential_citations", 25)
    min_year = disc.get("min_year", 2016)
    groups = pl.interests().get("topic_groups", {})
    kws = groups.get(topic_group, {}).get("keywords", [])[:6]
    query = " ".join(kws[:4]) or field.replace("_", " ")
    try:
        res = fetch_semantic_scholar.fetch(argparse.Namespace(
            arxiv=None, doi=None, search=query, year=f"{min_year}-", max=n * 3))
    except Exception as e:  # noqa: BLE001
        pl.log_error("milestones.discover", str(e))
        return []
    suggestions = []
    for c in res:
        inf = c.get("influential_citation_count") or 0
        if inf < min_inf:
            continue
        nt = pl.normalize_title(c.get("title", ""))
        if nt in seen_titles or nt in existing_titles:
            continue
        ck = pl.derive_canonical_key(_cand_primary_ids(c), c.get("title", ""))
        if ck in existing:
            continue
        c = _apply_milestone(c, field, {"era": "expansion", "significance":
                             f"high-influence ({inf} influential citations)"}, topic_group)
        c["_canonical_key"] = ck
        c["_already_known"] = False
        c["_discovered"] = True
        c["_influential_citations"] = inf
        suggestions.append(c)
    suggestions.sort(key=lambda c: -(c.get("_influential_citations") or 0))
    return suggestions[:n]


def mark_existing(cands: list[dict]) -> list[dict]:
    """For resolved seeds already in the registry, set/refresh the `milestone` block on
    the existing paper.yaml (idempotent; no new version) and re-floor its triage label.
    Returns a list of {canonical_key, updated} for the ones touched."""
    import score_paper
    touched = []
    for c in cands:
        if c.get("_unresolved") or not c.get("_already_known") or not c.get("milestone"):
            continue
        ck = c.get("_canonical_key")
        pdir = pl.find_paper_by_key(ck)
        if not pdir:
            # try resolve by title
            nt = pl.normalize_title(c.get("title", ""))
            for p in pl.iter_papers():
                if pl.normalize_title(p.get("title", "")) == nt:
                    pdir = pl.find_paper_by_key(p.get("canonical_key"))
                    ck = p.get("canonical_key")
                    break
        if not pdir:
            continue
        pf = pdir / "paper.yaml"
        paper = pl.load_yaml(pf)
        changed = False
        if paper.get("milestone") != c["milestone"]:
            paper["milestone"] = c["milestone"]
            changed = True
        if "foundational" not in (paper.get("tags") or []):
            paper["tags"] = sorted((paper.get("tags") or []) + ["foundational"])
            changed = True
        if changed:
            pl.dump_yaml(pf, paper)
            # refresh latest version scoring so the floor/label reflect milestone status
            if paper.get("versions"):
                vk = paper["versions"][-1]["version_key"]
                mf = pdir / vk / "metadata.yaml"
                if mf.exists():
                    meta = pl.load_yaml(mf)
                    if "foundational" not in (meta.get("tags") or []):
                        meta.setdefault("tags", []).append("foundational")
                    meta["scoring"] = score_paper.score({**meta, "milestone": c["milestone"]})
                    pl.dump_yaml(mf, meta)
                    paper["user"]["triage_label"] = meta["scoring"]["label"]
                    paper["user"]["triage_confidence"] = meta["scoring"]["confidence"]
                    pl.dump_yaml(pf, paper)
        touched.append({"canonical_key": ck, "updated": changed})
    return touched


def _cand_primary_ids(cand: dict) -> dict:
    ids = cand.get("ids") or {}
    return {"arxiv_base_id": ids.get("arxiv_base_id"), "doi": ids.get("doi"),
            "openreview_id": ids.get("openreview_id"),
            "semantic_scholar_id": ids.get("semantic_scholar_id"),
            "openalex_id": ids.get("openalex_id")}


def _main() -> int:
    ap = argparse.ArgumentParser(description="Resolve milestone seeds into candidates.")
    ap.add_argument("--field", help="a field key from config/milestones.yaml")
    ap.add_argument("--all", action="store_true", help="all fields")
    ap.add_argument("--discover", action="store_true", help="add live high-citation suggestions")
    ap.add_argument("--mark-existing", action="store_true",
                    help="set the milestone block on already-known seeds (idempotent)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = pl.milestones_cfg().get("fields", {})
    if args.all:
        fields = list(cfg.keys())
    elif args.field:
        if args.field not in cfg:
            print(f"unknown field '{args.field}'. Known: {', '.join(cfg)}", file=sys.stderr)
            return 1
        fields = [args.field]
    else:
        ap.error("provide --field <name> or --all")

    all_cands = []
    for f in fields:
        cands = fetch_field(f, cfg[f], discover=args.discover)
        all_cands.extend(cands)

    resolved = [c for c in all_cands if not c.get("_unresolved")]
    new = [c for c in resolved if not c.get("_already_known")]
    if args.dry_run:
        print(f"[dry-run] {len(fields)} field(s): {len(resolved)} resolved, "
              f"{len(new)} new, {len(all_cands) - len(resolved)} unresolved")
        for c in resolved:
            flag = "NEW" if not c.get("_already_known") else "have"
            era = (c.get("milestone") or {}).get("era", "?")
            print(f"  [{flag}] ({era}) {c.get('year','?')} {(c.get('title') or '')[:70]} "
                  f"<- {c.get('_resolution')}")
        for c in all_cands:
            if c.get("_unresolved"):
                print(f"  [UNRESOLVED] {c.get('_seed')}")
        return 0
    if args.mark_existing:
        touched = mark_existing(all_cands)
        sys.stderr.write(f"[mark-existing] {sum(1 for t in touched if t['updated'])} "
                         f"existing paper(s) marked as milestones\n")
    for c in all_cands:
        print(json.dumps(c, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
