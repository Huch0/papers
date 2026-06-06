---
name: sync-paper-index
description: Validate all metadata and deterministically regenerate every registry file and Markdown index. Use when the user runs /sync-paper-index or after manual edits to config/metadata/summaries.
---

# /sync-paper-index

Validate integrity and rebuild all derived artifacts from the authoritative YAML.

## Steps
1. Backfill any schema drift (idempotent, makes backups):
   ```
   python3 scripts/migrate_registry.py
   ```
2. Validate:
   ```
   python3 scripts/validate_registry.py
   ```
   Surfaces: broken paths, missing PDFs (marked downloaded), PDF sha mismatches,
   missing summaries (marked summarized), duplicate canonical keys, duplicate
   version keys, identical PDF hashes across papers, out-of-taxonomy tags (warning).
3. Scan for duplicates:
   ```
   python3 scripts/detect_duplicates.py
   ```
   New ambiguous pairs go to `registry/duplicate_candidates.jsonl` (never auto-merged).
4. Regenerate indexes + caches:
   ```
   python3 scripts/update_indexes.py
   ```
   Rebuilds `registry/papers.jsonl`, `registry/catalog.sqlite`, and every file under
   `indexes/` (including `MILESTONES.md`).
5. Rebuild + validate the knowledge base:
   ```
   python3 scripts/knowledge.py index
   python3 scripts/knowledge.py validate
   ```
   Regenerates `knowledge/{INDEX,BY_TAG,BY_PAPER}.md` and checks that concept↔paper
   links are reciprocal and reference real papers.

## Report
Print a concise status: number of papers, validation errors vs. warnings (with the
first few of each), new duplicate candidates to resolve, and confirmation that indexes
were regenerated. If validation reports ERRORS, do **not** claim success — list them
and propose fixes (often a missing PDF, a stale `status.summarized` flag, or a tag to
add to `config/tag_taxonomy.yaml`). Errors are also appended to `logs/errors.jsonl`.
