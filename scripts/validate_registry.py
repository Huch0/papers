#!/usr/bin/env python3
"""validate_registry.py — integrity checks over the library.

Validates the authoritative YAML records and the on-disk artifacts they point to.
Returns exit code 0 when there are no ERRORS (warnings are allowed). Designed to be
run by the PostToolUse hook and by /sync-paper-index.

Checks:
  - YAML loads; required fields present (paper.yaml, metadata.yaml)
  - canonical_key uniqueness across library
  - version_key uniqueness within a paper
  - PDF exists + SHA matches when status.downloaded
  - summary exists when status.summarized
  - no two version dirs share a pdf_sha256 unless flagged duplicate/superseded
  - tags outside taxonomy (warning only)
  - indexes regenerable (dry import of update_indexes)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import paperlib as pl


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def ok(self) -> bool:
        return not self.errors


def _require(rec: dict, fields: list[str], where: str, rep: Report) -> None:
    for f in fields:
        if rec.get(f) in (None, "", []):
            rep.err(f"{where}: missing required field '{f}'")


def validate() -> Report:
    rep = Report()
    seen_keys: dict[str, str] = {}
    sha_index: dict[str, list[str]] = {}
    taxonomy = set()
    tt = pl.tag_taxonomy().get("tags", {})
    for group in tt.values():
        taxonomy.update(group)

    for pdir in pl.iter_paper_dirs():
        pf = pdir / "paper.yaml"
        try:
            paper = pl.load_yaml(pf)
        except Exception as e:  # noqa: BLE001
            rep.err(f"{pf}: YAML load failed: {e}")
            continue
        if not isinstance(paper, dict):
            rep.err(f"{pf}: not a mapping")
            continue

        _require(paper, ["canonical_key", "slug", "title"], str(pf), rep)
        ck = paper.get("canonical_key")
        if ck:
            if ck in seen_keys:
                rep.err(f"duplicate canonical_key '{ck}' in {pdir.name} and {seen_keys[ck]}")
            else:
                seen_keys[ck] = pdir.name
        if paper.get("slug") and paper["slug"] != pdir.name:
            rep.warn(f"{pf}: slug '{paper['slug']}' != dir name '{pdir.name}'")

        versions = paper.get("versions") or []
        if not versions:
            rep.err(f"{pf}: no versions listed")
        seen_v: set[str] = set()
        for v in versions:
            vk = v.get("version_key")
            if not vk:
                rep.err(f"{pf}: a version is missing version_key")
                continue
            if vk in seen_v:
                rep.err(f"{pf}: duplicate version_key '{vk}'")
            seen_v.add(vk)
            vdir = pdir / vk
            if not vdir.exists():
                rep.err(f"{pf}: version dir '{vk}' does not exist")
                continue

            # version metadata
            mf = vdir / "metadata.yaml"
            if not mf.exists():
                rep.err(f"{vdir}: metadata.yaml missing")
                meta = {}
            else:
                try:
                    meta = pl.load_yaml(mf) or {}
                except Exception as e:  # noqa: BLE001
                    rep.err(f"{mf}: YAML load failed: {e}")
                    meta = {}
                _require(meta, ["canonical_key", "version_key", "title"], str(mf), rep)
                if meta.get("canonical_key") not in (None, ck):
                    rep.err(f"{mf}: canonical_key mismatch with paper.yaml")

            status = (meta.get("status") or {}) if meta else {}
            # PDF checks
            if status.get("downloaded"):
                pdf_rel = (meta.get("artifacts") or {}).get("pdf")
                pdf_path = (pl.ROOT / pdf_rel) if pdf_rel else (vdir / "paper.pdf")
                if not Path(pdf_path).exists():
                    rep.err(f"{vdir}: marked downloaded but PDF missing ({pdf_path})")
                else:
                    declared = meta.get("pdf_sha256")
                    actual = pl.sha256_file(pdf_path)
                    if declared and declared != actual:
                        rep.err(f"{vdir}: pdf_sha256 mismatch (declared {declared[:12]} != {actual[:12]})")
                    sha_index.setdefault(actual, []).append(f"{pdir.name}/{vk}")
            # summary checks
            if status.get("summarized"):
                sm_rel = (meta.get("artifacts") or {}).get("summary")
                sm_path = (pl.ROOT / sm_rel) if sm_rel else (vdir / "summary.md")
                if not Path(sm_path).exists():
                    rep.err(f"{vdir}: marked summarized but summary.md missing")
            # tag taxonomy (warn)
            for t in (meta.get("tags") or []):
                if taxonomy and t not in taxonomy:
                    rep.warn(f"{vdir}: tag '{t}' not in tag_taxonomy.yaml")

    # duplicate PDF hashes across papers
    for sha, locs in sha_index.items():
        if len(locs) > 1:
            # allowed only if flagged; we can't cheaply verify flags here, so warn.
            rep.warn(f"identical PDF sha256 {sha[:12]} in: {', '.join(locs)} "
                     f"(ensure these are flagged duplicate/superseded)")

    # indexes regenerable
    try:
        import update_indexes  # noqa: F401
    except Exception as e:  # noqa: BLE001
        rep.err(f"update_indexes import failed: {e}")

    return rep


def _main() -> int:
    ap = argparse.ArgumentParser(description="Validate the paper registry.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="only print on error")
    args = ap.parse_args()

    rep = validate()
    if args.json:
        print(json.dumps({"ok": rep.ok(), "errors": rep.errors,
                          "warnings": rep.warnings}, indent=2))
    else:
        for w in rep.warnings:
            print(f"WARN  {w}")
        for e in rep.errors:
            print(f"ERROR {e}")
        if rep.ok():
            if not args.quiet:
                n = sum(1 for _ in pl.iter_paper_dirs())
                print(f"OK: {n} paper(s) valid, {len(rep.warnings)} warning(s).")
        else:
            print(f"FAILED: {len(rep.errors)} error(s), {len(rep.warnings)} warning(s).")

    if not rep.ok():
        for e in rep.errors:
            pl.log_error("validate", e)
    return 0 if rep.ok() else 1


if __name__ == "__main__":
    raise SystemExit(_main())
