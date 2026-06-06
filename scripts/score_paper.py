#!/usr/bin/env python3
"""score_paper.py — read-worthiness scoring.

Computes a 0..100 score and a triage label from config/scoring.yaml using a
candidate record or a version metadata.yaml. Heuristic at fetch time (title +
abstract); Claude refines subscores/rationale during summarization and writes
them back, after which re-running here uses the refined subscores.

Usage:
    score_paper.py --candidate '<json>'         # score a raw candidate dict
    score_paper.py library/<slug>/v1            # score a version dir, write back
    score_paper.py library/<slug>/v1 --json     # print result as JSON only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import paperlib as pl

CFG = pl.scoring_cfg
INTERESTS = pl.interests
VENUES = pl.venues


def _text(rec: dict) -> str:
    return " ".join(str(rec.get(k) or "") for k in ("title", "abstract")).lower()


def _interest_fit(rec: dict) -> tuple[float, list[str]]:
    text = _text(rec)
    groups = INTERESTS().get("topic_groups", {})
    best = 0.0
    matched: list[str] = []
    declared = set(rec.get("topic_groups") or [])
    for name, g in groups.items():
        pw = pl.PRIORITY_WEIGHT.get(g.get("priority", "medium"), 0.55)
        hits = [k for k in g.get("keywords", []) if k.lower() in text]
        if name in declared:
            hits.append(f"group:{name}")
        if hits:
            matched.extend(f"{name}:{h}" for h in hits[:3])
            # diminishing returns on multiple hits within a group
            strength = min(1.0, 0.55 + 0.18 * len(hits))
            best = max(best, pw * strength)
    return best, matched


def _recency(rec: dict) -> float:
    cfg = CFG().get("recency", {})
    date = rec.get("source_updated_at") or rec.get("fetched_at")
    d = pl.days_since(date)
    year = rec.get("year")
    sub = 0.0
    if d is not None:
        full = cfg.get("full_score_within_days", 14)
        zero = cfg.get("zero_score_after_days", 540)
        if d <= full:
            sub = 1.0
        elif d >= zero:
            sub = 0.0
        else:
            sub = 1.0 - (d - full) / (zero - full)
    try:
        if year and int(year) >= cfg.get("recent_year_floor_year", 2025):
            sub = max(sub, cfg.get("recent_year_floor", 0.35))
    except (TypeError, ValueError):
        pass
    return max(0.0, min(1.0, sub))


def _venue_quality(rec: dict) -> float:
    name = (rec.get("venue") or "")
    if isinstance(name, dict):
        name = name.get("name") or ""
    name = str(name)
    vcfg = VENUES()
    aliases = {k.lower(): v for k, v in (vcfg.get("aliases") or {}).items()}
    canon = aliases.get(name.lower(), name)
    tiers = vcfg.get("tiers", {})
    nl = canon.lower()
    for tier, spec in tiers.items():
        for v in spec.get("venues", []) or []:
            if v.lower() in nl:
                return float(spec.get("weight", 0.3))
    # No venue match -> treat as preprint/unknown.
    if not name or name.lower() in ("arxiv", "corr", "preprint"):
        return float(tiers.get("workshop_or_minor", {}).get("weight", 0.4))
    return float(tiers.get("unknown", {}).get("weight", 0.3))


def _keyword_subscore(rec: dict, terms_key: str) -> float:
    text = _text(rec)
    terms = CFG().get("heuristics", {}).get(terms_key, [])
    hits = sum(1 for t in terms if t.lower() in text)
    if not terms:
        return 0.0
    return min(1.0, 0.3 + 0.25 * hits) if hits else 0.0


def _harness_relevance(rec: dict) -> float:
    # Reuse agent_harness keyword group + harness-y terms.
    text = _text(rec)
    groups = INTERESTS().get("topic_groups", {})
    kws = groups.get("agent_harness", {}).get("keywords", []) + [
        "harness", "verifier", "executor", "environment", "trajectory",
        "tool", "interface", "workspace"]
    hits = sum(1 for k in set(k.lower() for k in kws) if k in text)
    return min(1.0, 0.2 + 0.16 * hits) if hits else 0.0


def _author_lab_signal(rec: dict) -> float:
    text = (" ".join(rec.get("authors") or []) + " " + str(rec.get("venue") or "")).lower()
    abstract = _text(rec)
    labs = [l.lower() for l in INTERESTS().get("watch_labs", [])]
    authors_watch = [a.lower() for a in INTERESTS().get("watch_authors", [])]
    if any(l in text or l in abstract for l in labs) or any(a in text for a in authors_watch):
        return 1.0
    return 0.0


def _trend_signal(rec: dict) -> float:
    text = _text(rec)
    benches = [b.lower() for b in INTERESTS().get("watch_benchmarks", [])]
    hits = sum(1 for b in benches if b in text)
    return min(1.0, 0.4 + 0.3 * hits) if hits else 0.0


def _negative_signals(rec: dict, subs: dict) -> tuple[float, list[str]]:
    """Heuristic negative-signal detection. Returns (penalty_fraction 0..1, names)."""
    text = _text(rec)
    fired: list[str] = []
    nsig = CFG().get("negative_signals", {})
    # abstract_only: no pdf
    if not rec.get("pdf_sha256") and not rec.get("pdf_url"):
        fired.append("abstract_only")
    # off_topic: zero interest fit
    if subs.get("interest_fit", 0) <= 0.01:
        fired.append("off_topic")
    # old_in_fast_area: low recency + low foundational signal
    if subs.get("recency", 1) < 0.2 and "foundational" not in (rec.get("tags") or []):
        fired.append("old_in_fast_area")
    # gui_only_misclassified: mentions GUI but not other interfaces, claims general
    if "gui" in text and not any(w in text for w in ("cli", "terminal", "shell", "api ", "filesystem")):
        if "computer use" in text or "computer-use" in text:
            fired.append("gui_only_misclassified")
    # explicit tags
    if "superseded" in (rec.get("tags") or []):
        fired.append("superseded")
    # Sum weighted fractions, clamp to 1.0
    frac = 0.0
    for f in fired:
        frac += float(nsig.get(f, {}).get("weight", 0.5))
    return min(1.0, frac), fired


def score(rec: dict) -> dict:
    """rec: a flat dict with title/abstract/venue/year/authors/pdf_url/pdf_sha256/
    tags/topic_groups, plus optional precomputed scoring.subscores."""
    weights = CFG().get("weights", {})
    pre = (rec.get("scoring") or {}).get("subscores") or {}

    fit, matched = _interest_fit(rec)
    subs = {
        "interest_fit": pre.get("interest_fit", fit),
        "recency": pre.get("recency", _recency(rec)),
        "venue_quality": pre.get("venue_quality", _venue_quality(rec)),
        "harness_relevance": pre.get("harness_relevance", _harness_relevance(rec)),
        "novelty": pre.get("novelty", _keyword_subscore(rec, "novelty_positive_terms")),
        "artifact_availability": pre.get("artifact_availability", _keyword_subscore(rec, "artifact_terms")),
        "evaluation_quality": pre.get("evaluation_quality", _keyword_subscore(rec, "evaluation_quality_terms")),
        "trend_signal": pre.get("trend_signal", _trend_signal(rec)),
        "author_or_lab_signal": pre.get("author_or_lab_signal", _author_lab_signal(rec)),
    }

    total = 0.0
    max_total = 0.0
    for dim, w in weights.items():
        if dim == "negative_noise_penalty":
            continue
        if w <= 0:
            continue
        total += subs.get(dim, 0.0) * w
        max_total += w

    neg_frac, neg_names = _negative_signals(rec, subs)
    penalty = abs(weights.get("negative_noise_penalty", -20)) * neg_frac
    total -= penalty

    raw = (total / max_total) * 100 if max_total else 0.0
    final = max(0.0, min(100.0, raw))

    # Curated landmark floor: milestones / foundational papers stay visible despite age.
    floored = False
    if rec.get("milestone") or "foundational" in (rec.get("tags") or []):
        floor = CFG().get("foundational_floor", 65)
        if final < floor:
            final = floor
            floored = True

    label = label_for(final)
    confidence = "high" if matched and subs["interest_fit"] > 0.6 else (
        "medium" if matched else "low")

    rationale = _rationale(subs, matched, neg_names, final, label)
    if floored:
        rationale += " | milestone/foundational floor applied"
    return {
        "score": round(final, 1),
        "label": label,
        "confidence": confidence,
        "rationale": rationale,
        "matched_interests": matched,
        "negative_signals": neg_names,
        "subscores": {k: round(v, 3) for k, v in subs.items()},
    }


def label_for(score_val: float) -> str:
    th = CFG().get("thresholds", {})
    if score_val >= th.get("MUST_READ", 80):
        return "MUST_READ"
    if score_val >= th.get("READ_SOON", 65):
        return "READ_SOON"
    if score_val >= th.get("SKIM", 50):
        return "SKIM"
    if score_val >= th.get("TRACK_ONLY", 35):
        return "TRACK_ONLY"
    return "SKIP"


def _rationale(subs, matched, neg, final, label) -> str:
    top = sorted(subs.items(), key=lambda kv: kv[1], reverse=True)[:3]
    parts = [f"score={final:.0f} -> {label}"]
    parts.append("strong: " + ", ".join(f"{k}({v:.2f})" for k, v in top if v > 0))
    if matched:
        parts.append("interests: " + ", ".join(matched[:4]))
    if neg:
        parts.append("negatives: " + ", ".join(neg))
    return " | ".join(parts)


def _main() -> int:
    ap = argparse.ArgumentParser(description="Score a paper for read-worthiness.")
    ap.add_argument("target", nargs="?", help="version dir (library/<slug>/vN)")
    ap.add_argument("--candidate", help="JSON candidate record to score")
    ap.add_argument("--json", action="store_true", help="print result JSON only")
    ap.add_argument("--write", action="store_true",
                    help="write scoring back into metadata.yaml (default if target given)")
    args = ap.parse_args()

    if args.candidate:
        rec = json.loads(args.candidate)
        print(json.dumps(score(rec), ensure_ascii=False, indent=2))
        return 0

    if not args.target:
        ap.error("provide a version dir or --candidate")

    vdir = pl.resolve_path(args.target)
    mfile = vdir / "metadata.yaml"
    if not mfile.exists():
        print(f"no metadata.yaml at {vdir}", file=sys.stderr)
        return 1
    meta = pl.load_yaml(mfile)
    result = score(meta)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result["rationale"])

    if not args.json or args.write:
        meta["scoring"] = result
        meta.setdefault("status", {})["triaged"] = True
        pl.dump_yaml(mfile, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
