#!/usr/bin/env python3
"""SessionStart hook — print a short dashboard.

stdout from a SessionStart hook is added to the session context, so this gives each
new session a quick view of the library state: untriaged papers, summaries pending,
recent MUST_READ, and the last logged error. Read-only and fast; never fails the
session (always exits 0).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    try:
        import paperlib as pl
    except Exception:  # noqa: BLE001
        return 0

    papers = list(pl.iter_papers())
    if not papers and not (pl.LIBRARY.exists() and any(pl.LIBRARY.iterdir())):
        print("[papers] Library is empty. Run /daily-papers or /add-paper <ref> to start.")
        return 0

    untriaged = 0
    pending_summary = 0
    must_read = []
    for p in papers:
        u = p.get("user") or {}
        if not u.get("triage_label"):
            untriaged += 1
        for v in p.get("versions") or []:
            if v.get("summary_status") in (None, "none", "stale"):
                pending_summary += 1
        if u.get("triage_label") == "MUST_READ":
            must_read.append(p.get("title") or p.get("canonical_key"))

    last_err = None
    errs = pl.read_jsonl(pl.ERRORS_JSONL)
    if errs:
        last_err = errs[-1]

    concepts = len(list((pl.CONCEPTS).glob("*.md"))) if pl.CONCEPTS.exists() else 0
    milestones = sum(1 for p in papers if p.get("milestone"))
    print(f"[papers] {len(papers)} paper(s) | untriaged: {untriaged} | "
          f"summaries pending: {pending_summary} | MUST_READ: {len(must_read)} | "
          f"milestones: {milestones} | KB concepts: {concepts}")
    for t in must_read[:5]:
        print(f"  ★ {t[:90]}")
    if last_err:
        print(f"  last error [{last_err.get('stage')}]: {str(last_err.get('message'))[:120]}")
    print("  commands: /daily-papers  /add-paper  /summarize-paper  /triage-papers  "
          "/sync-paper-index  /evolve-paper-system")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        sys.exit(0)
