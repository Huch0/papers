#!/usr/bin/env python3
"""daily.py — orchestrate one daily-papers run (mechanical parts).

Fetches candidates from enabled sources, dedupes against the registry, ingests new
papers / new versions, downloads PDFs for above-threshold papers, regenerates
indexes, and writes inbox/<date>/{candidates.jsonl,rejected.jsonl,daily_report.md}.

Full English summaries for above-threshold papers are written by Claude (the
/daily-papers skill calls summarize-paper for each). This script does the
deterministic discovery/triage/record-keeping and reports what needs summarizing.

Usage:
    daily.py                       # default window (config since_days), today's inbox
    daily.py --since 3d
    daily.py --from 2026-06-01 --to 2026-06-06
    daily.py --tags agent_harness,computer_use_agents
    daily.py --date 2026-06-04     # inbox date label override
    daily.py --dry-run             # fetch + score, write nothing into library/
    daily.py --enrich              # also call OpenAlex/S2 enrichment (slower)
    daily.py --pdf-threshold 50    # min score to download PDF (default from scoring)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import paperlib as pl
import fetch_arxiv
import ingest as ingest_mod
import score_paper
import update_indexes

try:
    import fetch_openalex
    import fetch_semantic_scholar
    HAVE_ENRICH = True
except Exception:  # noqa: BLE001
    HAVE_ENRICH = False


def _existing_keys() -> set[str]:
    keys = set()
    for p in pl.iter_papers():
        keys.add(p.get("canonical_key"))
        pid = p.get("primary_ids") or {}
        if pid.get("arxiv_base_id"):
            keys.add(f"arxiv-{pid['arxiv_base_id']}")
    return keys


def run(args) -> dict:
    date_label = args.date or pl.today()
    inbox = pl.INBOX / date_label
    inbox.mkdir(parents=True, exist_ok=True)

    # 1. fetch (arXiv primary)
    fetch_args = argparse.Namespace(
        since=args.since, from_=args.from_, to=args.to, id=None,
        tags=args.tags, max=args.max, out=None, dry_run=False)
    candidates: list[dict] = []
    errors: list[dict] = []
    source_coverage: dict[str, int] = {}
    try:
        arx = fetch_arxiv.fetch(fetch_args)
        candidates.extend(arx)
        source_coverage["arxiv"] = len(arx)
    except Exception as e:  # noqa: BLE001
        errors.append({"source": "arxiv", "error": str(e)})
        pl.log_error("daily.fetch_arxiv", str(e))

    # 2. optional enrichment
    if args.enrich and HAVE_ENRICH:
        for c in candidates:
            try:
                c = fetch_openalex.enrich(c)
                c = fetch_semantic_scholar.enrich(c)
            except Exception as e:  # noqa: BLE001
                pl.log_error("daily.enrich", str(e))

    # 3. score all, split rejected (below TRACK_ONLY) for inbox visibility
    existing = _existing_keys()
    triaged: list[dict] = []
    for c in candidates:
        sc = score_paper.score(c)
        c["scoring"] = sc
        ck = pl.derive_canonical_key(ingest_mod._primary_ids(c), c.get("title", ""))
        c["_canonical_key"] = ck
        c["_already_known"] = ck in existing
        triaged.append(c)

    # write candidates.jsonl (all), rejected.jsonl (SKIP)
    pl.write_jsonl(inbox / "candidates.jsonl", triaged)
    rejected = [c for c in triaged if c["scoring"]["label"] == "SKIP"]
    pl.write_jsonl(inbox / "rejected.jsonl", rejected)

    if args.dry_run:
        report = _report(date_label, triaged, [], errors, source_coverage, dry_run=True)
        (inbox / "daily_report.md").write_text(report, encoding="utf-8")
        return {"date": date_label, "fetched": len(triaged),
                "dry_run": True, "report": pl.rel(inbox / "daily_report.md")}

    # 4. ingest non-SKIP candidates (records always created; PDFs above threshold)
    pdf_threshold = args.pdf_threshold if args.pdf_threshold is not None else \
        pl.scoring_cfg().get("thresholds", {}).get("SKIM", 50)
    results = []
    for c in triaged:
        if c["scoring"]["label"] == "SKIP":
            continue  # still recorded in rejected.jsonl; not ingested into library
        pdf_src = c.get("pdf_url") if c["scoring"]["score"] >= pdf_threshold else None
        try:
            res = ingest_mod.ingest(c, pdf_src)
            res["needs_summary"] = (c["scoring"]["score"] >= pdf_threshold and
                                    res.get("action") in ("new_paper", "new_version"))
            results.append(res)
        except Exception as e:  # noqa: BLE001
            errors.append({"key": c.get("_canonical_key"), "error": str(e)})
            pl.log_error("daily.ingest", str(e), key=c.get("_canonical_key"))

    # 5. regenerate indexes
    update_indexes.build(write=True)

    report = _report(date_label, triaged, results, errors, source_coverage)
    (inbox / "daily_report.md").write_text(report, encoding="utf-8")

    needs_summary = [r for r in results if r.get("needs_summary")]
    return {
        "date": date_label,
        "fetched": len(triaged),
        "new": sum(1 for r in results if r.get("action") == "new_paper"),
        "updated": sum(1 for r in results if r.get("action") == "new_version"),
        "unchanged": sum(1 for r in results if r.get("action") == "unchanged"),
        "duplicates": sum(1 for r in results if r.get("duplicate_candidates")),
        "errors": len(errors),
        "needs_summary": [
            {"version_dir": r.get("version_dir"), "label": r.get("label"),
             "score": r.get("score"), "key": r.get("canonical_key")}
            for r in needs_summary],
        "report": pl.rel(inbox / "daily_report.md"),
    }


def _report(date_label, triaged, results, errors, coverage, dry_run=False) -> str:
    from collections import Counter
    labels = Counter(c["scoring"]["label"] for c in triaged)
    new = [r for r in results if r.get("action") == "new_paper"]
    updated = [r for r in results if r.get("action") == "new_version"]
    dups = [r for r in results if r.get("duplicate_candidates")]

    def by_label(label):
        return sorted([c for c in triaged if c["scoring"]["label"] == label],
                      key=lambda c: -c["scoring"]["score"])

    lines = [f"# Daily paper report — {date_label}", ""]
    if dry_run:
        lines.append("> DRY RUN — no records written to library/.\n")
    lines += [
        "## Counts",
        f"- Fetched: {len(triaged)}",
        f"- New papers: {len(new)}",
        f"- Updated (new versions): {len(updated)}",
        f"- Duplicate candidates: {len(dups)}",
        f"- Errors: {len(errors)}",
        "",
        "### Triage breakdown",
    ]
    for lbl in pl.TRIAGE_LABELS:
        lines.append(f"- {lbl}: {labels.get(lbl, 0)}")
    lines.append("")

    def table(items, n=20):
        rows = ["| Score | Label | Title | Venue | arXiv |", "|---|---|---|---|---|"]
        for c in items[:n]:
            ids = c.get("ids", {})
            ax = ids.get("arxiv_base_id") or "—"
            title = (c.get("title") or "")[:80].replace("|", "\\|")
            venue = (c.get("venue") or "—")
            if isinstance(venue, dict):
                venue = venue.get("name") or "—"
            rows.append(f"| {c['scoring']['score']:.0f} | {c['scoring']['label']} "
                        f"| {title} | {venue} | {ax} |")
        return rows

    lines += ["## Top MUST_READ", ""] + table(by_label("MUST_READ")) + [""]
    lines += ["## READ_SOON", ""] + table(by_label("READ_SOON")) + [""]
    lines += ["## SKIM", ""] + table(by_label("SKIM"), n=15) + [""]
    skipped = by_label("SKIP")
    lines += [f"## Skipped ({len(skipped)})", ""]
    for c in skipped[:15]:
        lines.append(f"- ({c['scoring']['score']:.0f}) {(c.get('title') or '')[:90]} — "
                     f"{', '.join(c['scoring']['negative_signals']) or 'low fit'}")
    lines.append("")

    if dups:
        lines += ["## Duplicate candidates", ""]
        for r in dups:
            for d in r["duplicate_candidates"]:
                lines.append(f"- {r['canonical_key']} ~ {d['canonical_key']} "
                             f"({d['confidence']}: {', '.join(d['reasons'])})")
        lines.append("")

    lines += ["## Source coverage", ""]
    for s, n in coverage.items():
        lines.append(f"- {s}: {n}")
    lines.append("")

    if errors:
        lines += ["## Errors", ""]
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    # trend notes (rough): top topic groups today
    from collections import Counter as C
    tg = C()
    for c in triaged:
        for g in c.get("topic_groups", []):
            tg[g] += 1
    lines += ["## Trend notes", ""]
    for g, n in tg.most_common():
        lines.append(f"- {g}: {n} candidate(s)")
    lines.append("")
    return "\n".join(lines)


def _main() -> int:
    ap = argparse.ArgumentParser(description="Run a daily-papers discovery pass.")
    ap.add_argument("--since")
    ap.add_argument("--from", dest="from_")
    ap.add_argument("--to")
    ap.add_argument("--date", help="inbox date label (default: today)")
    ap.add_argument("--tags")
    ap.add_argument("--max", type=int)
    ap.add_argument("--enrich", action="store_true")
    ap.add_argument("--pdf-threshold", type=float)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    res = run(args)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
