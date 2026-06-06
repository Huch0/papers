---
name: milestone-papers
description: Find and ingest the landmark/milestone papers of a field, from the field's emergence to recent, deduped against papers already in the library. Use when the user runs /milestone-papers <field> (e.g. computer use agents, SWE agents), or asks to backfill foundational papers for an interest area.
---

# /milestone-papers <field> [--discover]

Build out the canonical landmark papers for a field (e.g. "computer use agents") across
its whole timeline — emergence → foundational → expansion → recent — without creating
duplicates of papers already in the library.

## Resolve the field
Map the user's phrase to a field key in `config/milestones.yaml`
(`computer_use_agents`, `software_engineering_agents`, `agent_harness`,
`document_agents`, ...). If the field isn't there yet, propose adding it (a short
`seeds:` list with titles + era + significance) — that's a durable
`/evolve-paper-system`-style edit; confirm with the user, then add it.

## Steps
1. Resolve the curated seeds (and optionally discover more) — this hits the network and
   **dedupes against the registry** but writes nothing yet:
   ```
   python3 scripts/fetch_milestones.py --field <field> [--discover] --dry-run
   ```
   Review the printed list: `[NEW]` = not in library, `[have]` = already ingested,
   `[UNRESOLVED]` = a seed whose title/id couldn't be matched. `--discover` adds live
   high-influential-citation suggestions beyond the curated seeds.

2. Present the timeline to the user (era → year → title → significance) and confirm
   which to ingest. Default: ingest all `[NEW]` resolved seeds; surface UNRESOLVED ones
   so the user can supply an arXiv id or correct title (then add it to
   `config/milestones.yaml`).

3. Ingest the new ones and mark already-known seeds as milestones (idempotent):
   ```
   # get the JSONL of resolved candidates (re-runs resolution; or capture step 1 output)
   python3 scripts/fetch_milestones.py --field <field> [--discover] --mark-existing \
       > /tmp/milestones.jsonl
   ```
   Then, for each line that is resolved and `_already_known == false`, ingest it
   (downloading the PDF when a `pdf_url` is present):
   ```
   python3 scripts/ingest.py --candidate '<one candidate json line>' --pdf '<pdf_url>'
   ```
   `--mark-existing` already set the `milestone` block on seeds you'd previously added
   (so SWE-bench etc. show up in MILESTONES.md) without creating new versions.
   ingest.py carries the `milestone` block through and adds the `foundational` tag, so
   the scorer floors these at READ_SOON (curated landmarks stay visible despite age).

4. Summarize the most important new milestones (at least the `emergence` and
   `foundational` eras) via the **summarize-paper** procedure, so the user gets real
   English analysis, not just records. Lower-priority ones can stay as triage records.

5. Rebuild indexes and report:
   ```
   python3 scripts/update_indexes.py
   python3 scripts/validate_registry.py
   ```
   Point the user at `indexes/MILESTONES.md` (the per-field timeline) and summarize:
   how many added, how many already present, any unresolved seeds to fix.

## Notes
- Never re-add a paper already in the library — the resolver flags `_already_known` by
  canonical key AND normalized title; respect it.
- Milestones are intentionally old; that's why they get the `foundational` floor. Don't
  "fix" their low recency.
- If the user wants a brand-new field tracked, add it to `config/milestones.yaml` (and
  usually `config/interests.yaml`) so it's durable — then this skill covers it forever.
