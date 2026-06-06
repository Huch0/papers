---
name: evolve-paper-system
description: Evolve the paper harness when the user reports friction or requests a workflow change (e.g. too many old GUI papers, shorter summaries for SKIP, a new tag). Inspect the system, propose a minimal plan, apply durable config/script/template changes after confirmation, and log them. Use when the user runs /evolve-paper-system <complaint or request>.
---

# /evolve-paper-system <complaint or improvement request>

Turn a preference correction or friction report into a **durable** change in config,
templates, or scripts — never a hidden prompt-only behavior.

## Steps
1. **Parse the request** into a concrete intent. Map it to the most likely durable
   surface:
   - "too many old GUI papers" → `config/scoring.yaml` (negative signals
     `gui_only_misclassified`, `old_in_fast_area` weights; recency curve) and/or
     `config/interests.yaml` notes.
   - "summaries too long for SKIP" → `config/summary_template.md` guidance or the
     summarize skill's brevity rule for low labels.
   - "add a tag for X" → `config/tag_taxonomy.yaml` (+ note any metadata to backfill).
   - "prioritize venue Y / author Z" → `config/venues.yaml` / `interests.yaml`
     (`watch_authors`, `watch_labs`, `watch_benchmarks`).
   - "change directory layout / add a field" → schema (`config/metadata_schema.md`),
     `scripts/paperlib.py` record templates, and a `migrate_registry.py` migration.
   - "fetch from a new source" → `config/sources.yaml` + a new `scripts/fetch_*.py`.

2. **Inspect** the relevant files before proposing anything (read them; check how the
   scoring/fetch/index code consumes the config you intend to change).

3. **Propose a minimal change plan** to the user: which files change, the exact diff
   intent, whether existing metadata needs migration, and backwards-compatibility.
   For anything nontrivial, **wait for confirmation** before writing.

4. **Apply** the change (edit config/template/script). Prefer the smallest edit that
   makes the behavior durable. Keep backwards compatibility, or add a migration.

5. **Validate**:
   ```
   python3 scripts/validate_registry.py
   python3 scripts/update_indexes.py
   ```
   If the change affects existing metadata, write and run a migration:
   ```
   python3 scripts/migrate_registry.py        # or a new dedicated migration
   ```
   If migration is deferred, say so explicitly and mark it pending.

6. **Log** an entry to `logs/system_changes.md` (date, trigger, change, files touched,
   migration status). If the change encodes a lasting user preference, also save a
   memory so future sessions honor it.

## Principles
- Durable config over prompt-only behavior. Single source of truth: `config/`.
- Minimal, reversible diffs. Backups via `migrate_registry.py` when touching metadata.
- Re-deriving indexes must stay deterministic.
- When uncertain about the user's intent, ask one clarifying question before changing
  scoring/taxonomy that affects every future run.
