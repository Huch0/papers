#!/usr/bin/env python3
"""PreToolUse(Bash) hook — block destructive operations against the harness.

Reads the hook JSON on stdin. Exit code 2 + stderr message blocks the command and
feeds the reason back to Claude. Exit 0 allows. Conservative by design: it only
blocks clearly dangerous patterns to avoid false positives on normal work.

Blocks:
  - rm -rf / and friends (root / home wipes)
  - deletion of library/, registry/, config/, .claude/ (or files within, recursively)
  - overwriting an existing library/<slug>/vN/paper.pdf (versions are immutable;
    create a new version dir instead)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # papers/
PROTECTED = {"library", "registry", "config", ".claude"}


def _read() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return {}


def block(reason: str) -> None:
    sys.stderr.write(f"[block_destructive_ops] BLOCKED: {reason}\n")
    sys.exit(2)


def main() -> int:
    data = _read()
    if data.get("tool_name") not in (None, "Bash"):
        return 0
    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd:
        return 0
    low = cmd

    # 1. catastrophic recursive deletes of root/home
    if re.search(r"\brm\b[^\n]*\s-[a-z]*r[a-z]*f?[^\n]*\s+(/|~|\$HOME|\.\.)(\s|$)", low) or \
       re.search(r"\brm\s+-[rf]+\s+/\s*$", low):
        block("recursive delete of / or $HOME")

    # 2. deletion / move of protected harness directories
    if re.search(r"\b(rm|rmdir|mv|shred|trash)\b", low):
        for name in PROTECTED:
            if re.search(rf"(^|[\s/'\"]){re.escape(name)}(/|[\s'\"]|$)", low) and \
               re.search(r"-[a-z]*r|--recursive|\brmdir\b|\brm\b", low):
                # allow deletes clearly *inside* an inbox/logs/tmp scratch area
                if re.search(r"\b(inbox|logs|tmp|\.part|\.tmp)\b", low) and name not in low.split():
                    continue
                block(f"attempt to delete/move protected directory '{name}/' "
                      f"(use /evolve-paper-system or a migration instead)")

    # 3. overwriting an existing immutable version PDF via shell redirection / cp / mv
    #    e.g.  cp x library/foo/v1/paper.pdf   or   ... > library/foo/v1/paper.pdf
    for m in re.finditer(r"library/[^\s'\"]+/v\d+/paper\.pdf", low):
        target = ROOT / m.group(0)
        if target.exists() and re.search(r"(>|\bcp\b|\bmv\b|\bdd\b|tee)\s", low):
            block(f"overwrite of existing version PDF '{m.group(0)}'. "
                  f"Versions are immutable — create a new vN directory.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001  — never break the user's shell on hook bug
        sys.stderr.write(f"[block_destructive_ops] hook error (allowing): {e}\n")
        sys.exit(0)
