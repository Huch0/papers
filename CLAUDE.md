# CLAUDE.md — papers/ research harness

This directory is a **paper management harness**, not an ordinary code project. Treat
it as a small data system with strong integrity rules. Read this before acting.

## What this is
A local system to fetch, track, summarize, and triage AI research papers for the
user's reading workflow. It is driven by slash-command skills (`/daily-papers`,
`/add-paper`, `/summarize-paper`, `/triage-papers`, `/sync-paper-index`,
`/evolve-paper-system`) and guarded by hooks in `.claude/`.

## Non-negotiable rules
1. **Authoritative data is the per-paper YAML** (`library/<slug>/paper.yaml` and
   `library/<slug>/<vN>/metadata.yaml`). `registry/*.jsonl`, `registry/catalog.sqlite`,
   and everything in `indexes/` are **derived** — regenerate them with
   `scripts/update_indexes.py`; never hand-edit them as a source of truth.
2. **Never overwrite a PDF or summary for a new version.** A new arXiv version, a
   changed PDF sha256, or changed venue/acceptance metadata is a **new version
   directory** (`v2`, `v3`, ...). Use `scripts/ingest.py` (it enforces this). A
   PreToolUse hook blocks shell overwrites of existing version PDFs.
3. **Summaries are in English** and must analyze (contribution / method / evidence /
   limitations / relevance), not paraphrase the abstract. Separate what is *claimed*
   from what the *evidence supports* from what is *unclear*.
4. **Indexes must be deterministic** — same library state ⇒ same index bytes. Don't
   inject timestamps into index bodies beyond the single generated-at header line.
5. **Preserve metadata integrity.** Run `scripts/validate_registry.py` after changing
   scripts, metadata, summaries, or indexes. The PostToolUse hook does this
   automatically for edits under `library/`, `config/`, `registry/`.
6. **User corrections become durable config**, not hidden prompt behavior. Route
   preference/scoring/tagging/layout changes through `/evolve-paper-system`, which
   edits `config/` (or schema + a migration) and logs to `logs/system_changes.md`.
7. **Don't guess metadata.** Use `"Not reported"` for absent source data and
   `"Unclear"` when the PDF text doesn't support a conclusion. If a venue/status/ID is
   uncertain, mark it uncertain.
8. **Preserve failed fetches.** If a fetch fails, keep the candidate/record and record
   the error reason (`logs/errors.jsonl`); don't drop it silently.
9. **Duplicates are never auto-merged.** Probable duplicates go to
   `registry/duplicate_candidates.jsonl`; resolve via `registry/aliases.yaml` or
   `/evolve-paper-system`. This includes `/milestone-papers`: it must dedupe curated
   landmark seeds against existing papers (by canonical key AND normalized title) and
   only mark/ingest accordingly — never re-add a paper already in the library.
10. **Knowledge is global and the user's notes are sacred.** Concepts live in
    `knowledge/concepts/<slug>.md` and may link many papers; a concept learned from one
    paper is meant to be reused/extended from others. Keep concept↔paper links
    reciprocal (use `scripts/knowledge.py`, don't hand-wire), preserve existing prose
    (append/refine, never overwrite the user's notes), and write knowledge in English.
    `knowledge/{INDEX,BY_TAG,BY_PAPER}.md` are derived — regenerate, don't hand-edit.

## How the pieces fit
- `config/` — single source of truth for interests, sources, venues, scoring, tags,
  summary template, and the metadata schema. Change behavior here, not in code.
- `scripts/paperlib.py` — shared schema/keys/hashing/IO. Import it; don't re-derive
  canonical keys or paths elsewhere.
- `scripts/ingest.py` — the only safe writer into `library/`.
- Fetchers (`scripts/fetch_*.py`) emit normalized candidate JSONL and **never** write
  into `library/`.
- Skills in `.claude/skills/` orchestrate scripts; the Python does deterministic work,
  Claude does the reading/summarizing/judgment.
- `config/milestones.yaml` + `scripts/fetch_milestones.py` — curated landmark papers per
  field; the resolver dedupes and never writes into `library/` (ingest does).
- `knowledge/` + `scripts/knowledge.py` — the global, cross-paper knowledge base; the
  `/paper-tutor` skill writes distilled concepts here while explaining a paper.

## When you finish a change
Run, in order: `validate_registry.py` → `update_indexes.py`. If you touched the schema
or existing records, also run `migrate_registry.py`. If validation reports ERRORS, do
not claim success — fix them or surface them.

## Canonical key / slug (for reference)
Key priority: `arxiv-<base_id>` → `doi-<slug>` → `openreview-<id>` → `s2-<id>` →
`openalex-<id>` → `title-<hash>`. Slug = short-title + key suffix. See
`config/metadata_schema.md` for the full schema and required fields.

## Agent skills

### Issue tracker

GitHub Issues in `Huch0/papers` via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Five canonical roles, default strings (`needs-triage`, `needs-info`, `ready-for-agent`,
`ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.
