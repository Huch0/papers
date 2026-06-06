#!/usr/bin/env python3
"""PostToolUse(Write|Edit) hook — validate after metadata/summary/config/registry edits.

Reads hook JSON on stdin. If the edited file is part of the harness's authoritative
or config surface, runs scripts/validate_registry.py and logs any errors to
logs/errors.jsonl. Non-blocking: always exits 0 (prints a short note if validation
failed so it appears in the transcript). Index regeneration is handled by the
companion auto_update_index.py hook.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "scripts"

WATCH_DIRS = ("library", "config", "registry", "knowledge")
WATCH_NAMES = ("metadata.yaml", "paper.yaml", "summary.md")


def _read() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        return {}


def _file_path(data: dict) -> str | None:
    ti = data.get("tool_input") or {}
    return ti.get("file_path") or ti.get("path")


def _relevant(fp: str) -> bool:
    try:
        rel = Path(fp).resolve().relative_to(ROOT)
    except (ValueError, OSError):
        return False
    parts = rel.parts
    if parts and parts[0] in WATCH_DIRS:
        return True
    return Path(fp).name in WATCH_NAMES


def main() -> int:
    data = _read()
    fp = _file_path(data)
    if not fp or not _relevant(fp):
        return 0
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_registry.py"), "--quiet"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            sys.stderr.write("[validate_metadata] registry validation reported errors:\n")
            sys.stderr.write(proc.stdout[-2000:] + "\n")
            # errors are also appended to logs/errors.jsonl by the validator
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[validate_metadata] hook error (ignored): {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
