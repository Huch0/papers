#!/usr/bin/env python3
"""Index auto-refresh hook.

Two modes:
  (default) PostToolUse(Write|Edit): if an authoritative file changed, regenerate
            derived indexes so INDEX.md/JSONL/etc. never drift from the YAML.
  --stop    Stop hook: if indexes are stale relative to the newest metadata edit,
            regenerate them (safe, deterministic) and remind the user.

Reads hook JSON on stdin (PostToolUse mode). Always exits 0 (non-blocking).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts"
INDEXES = ROOT / "indexes"
LIBRARY = ROOT / "library"
CONFIG = ROOT / "config"

WATCH_DIRS = ("library", "config", "registry", "knowledge")
WATCH_NAMES = ("metadata.yaml", "paper.yaml", "summary.md")


def _read() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return {}


def _regen(reason: str, *, knowledge_only: bool = False) -> None:
    try:
        if not knowledge_only:
            subprocess.run([sys.executable, str(SCRIPTS / "update_indexes.py")],
                           cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        # keep the knowledge index in sync too (cheap; needs paper titles for BY_PAPER)
        subprocess.run([sys.executable, str(SCRIPTS / "knowledge.py"), "index"],
                       cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[auto_update_index] regen failed ({reason}): {e}\n")


def _relevant(fp: str | None) -> bool:
    if not fp:
        return False
    try:
        rel = Path(fp).resolve().relative_to(ROOT)
    except (ValueError, OSError):
        return False
    return (rel.parts and rel.parts[0] in WATCH_DIRS) or Path(fp).name in WATCH_NAMES


def _newest_mtime(*globs) -> float:
    newest = 0.0
    for g in globs:
        for p in g:
            try:
                newest = max(newest, p.stat().st_mtime)
            except OSError:
                pass
    return newest


def _indexes_stale() -> bool:
    src = _newest_mtime(LIBRARY.rglob("metadata.yaml"), LIBRARY.rglob("paper.yaml"),
                        LIBRARY.rglob("summary.md"), CONFIG.glob("*.yaml"),
                        (ROOT / "knowledge" / "concepts").glob("*.md"))
    idx = INDEXES / "INDEX.md"
    if not idx.exists():
        return src > 0
    return src > idx.stat().st_mtime


def main(argv: list[str]) -> int:
    if "--stop" in argv:
        if _indexes_stale():
            _regen("stop-stale")
            sys.stderr.write("[auto_update_index] indexes were stale and have been "
                             "regenerated. (Run /sync-paper-index for a full validate.)\n")
        return 0

    data = _read()
    fp = (data.get("tool_input") or {}).get("file_path") or \
         (data.get("tool_input") or {}).get("path")
    if _relevant(fp):
        kn_only = False
        try:
            kn_only = Path(fp).resolve().relative_to(ROOT).parts[0] == "knowledge"
        except (ValueError, OSError, IndexError):
            pass
        _regen("posttooluse", knowledge_only=kn_only)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[auto_update_index] hook error (ignored): {e}\n")
        sys.exit(0)
