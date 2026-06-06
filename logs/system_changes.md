# System changes log

Append-only record of changes made via /evolve-paper-system or manual maintenance.
Each entry: date, trigger, change, files touched, migration status.

---

## 2026-06-06 — System bootstrapped

- Trigger: initial build request.
- Change: created full paper-harness skeleton (config, scripts, skills, hooks, indexes).
- Files: entire papers/ tree.
- Migration: none (green-field directory).

---

## 2026-06-06 — Added milestone discovery + global knowledge base

- Trigger: user feature request — (1) a skill to fetch milestone papers of a field from
  emergence to recent without duplicating existing papers; (2) a tutor/lab-colleague
  chat skill that captures learned knowledge into a global, cross-paper knowledge base.
- Change:
  - New config `config/milestones.yaml` (curated landmark seeds per field; titles + era
    + significance, resolved to real records at fetch time).
  - New scripts `scripts/fetch_milestones.py` (resolve + dedupe + `--discover` +
    `--mark-existing`) and `scripts/knowledge.py` (global concept notes: ensure-concept,
    link, search, session, index, validate).
  - New skills `.claude/skills/milestone-papers/` and `.claude/skills/paper-tutor/`.
  - Schema additions to `paper.yaml`: `milestone` block + `knowledge_concepts` (backfilled
    via migrate_registry); new `indexes/MILESTONES.md`; new `knowledge/` tree with
    generated INDEX/BY_TAG/BY_PAPER.
  - Scoring: `foundational_floor` (READ_SOON) so curated/foundational papers stay visible
    despite age; ingest carries the `milestone` block through and tags `foundational`.
  - Hooks/docs: auto_update_index + validate_metadata now watch `knowledge/`; sync skill
    rebuilds+validates the KB; README/CLAUDE.md/metadata_schema updated; SessionStart
    dashboard shows milestone + KB-concept counts.
- Migration: `migrate_registry.py` backfills the two new paper fields (idempotent, makes
  backups). Ran on the existing library (1 paper updated at time of change).
- Backwards compatibility: preserved — new fields default to null/[]; existing records
  validate unchanged.

---

## 2026-06-06 — Exhaustive milestone search: computer_use_agents

- Trigger: user request to exhaustively search milestone papers in the computer-use-agent field.
- Method: 5 parallel expert sweeps (web, gui_grounding, os_desktop, mobile,
  enabler_benchmark_survey) using web search + the harness's discover pass; merged and
  deduped by arXiv id then normalized title; flagged against the existing library.
- Result: 95 unique milestones (88 new, 7 already in library), spanning 4 eras.
- Durable capture: config/milestones.yaml `computer_use_agents` field restructured with
  sub-areas and expanded from 8 to 95 curated seeds (each title/year/era/arxiv/subarea/
  significance). Ingestion remains on-demand via /milestone-papers (dedup-protected).
- Note: a few late-2025 entries are tech reports/blogs without arXiv ids (Claude Computer
  Use, OpenAI Operator/CUA, Project Mariner, OSWorld-Verified); arXiv ids are validated at
  ingest time, so any imperfect id resolves by title search or is flagged unresolved.

## 2026-06-06 — Ingested all 88 new computer_use_agents milestones

- Ingested all 88 new milestones from the exhaustive search (records + metadata via a
  Semantic Scholar batch call to avoid arXiv rate limits; 84 arXiv PDFs downloaded with
  0 failures; 4 product reports kept as PDF-less records).
- Deep-summarized all 29 new emergence + foundational papers via parallel subagents,
  each grounded in its own PDF extraction with verified numbers and claim/evidence/
  unclear separation (several flagged abstract-vs-table discrepancies).
- Expansion (39) + recent (23) milestones remain as complete records (metadata + abstract
  + READ_SOON triage), summarizable on demand via /summarize-paper.
- Library: 11 -> 99 papers; 96 computer_use_agents milestones (91 with PDF, 36 with full
  summaries). Validation clean (0 errors/warnings); indexes + MILESTONES.md regenerated.

## 2026-06-06 — Revised the summary template (three-pass + Motivation≠Novelty + FOCUS)

- Trigger: user request to revise config/summary_template.md, referring to Keshav
  "How to Read a Paper", Kim "Motivation ≠ Novelty", and the AI@UVA "FOCUS" prompt.
- Change: restructured config/summary_template.md into Keshav's three passes
  (Triage → Content → Critique). Pass 1 adds the Five Cs. Pass 2 splits MOTIVATION
  (the problem) from NOVELTY (the genuine delta + the mechanistic reason the design must
  take its form), with Kim's litmus tests ("survives deleting 'we propose'?", "verify
  novelty vs merely confirm motivation", 30-second novelty test). FOCUS adds a
  declarative-voice / specific-numbers-with-anchors extraction rule and figure-scrutiny
  (axes/error-bars/significance, abstract-vs-table mismatches).
- Preserved script contracts: the `# <Paper Title>` header, the 12 `## Metadata` bullets
  (filled by summarize_paper.py --prepare), and the `## Personal notes`/`Free-form notes
  for later.` anchor (note preservation). Verified prepare fills metadata and preserves
  an injected note.
- Propagated to .claude/skills/summarize-paper/SKILL.md (requirements) and README
  ("Summary template & rules"). No metadata migration needed.
- Backwards compatibility: the ~37 existing summaries used the prior structure and remain
  valid (the template guides generation; it is not an enforced schema). Re-run
  /summarize-paper on any paper to regenerate it in the new format.

## 2026-06-06 — Self-contained rule + HTML summary format (experiment)

- Self-contained rule added to config/summary_template.md (+ skill): define every
  non-universal term/acronym/dataset/metric/method inline AND in a new Glossary section.
- Added an experimental rich HTML format: config/summary_template.html (CSS + color-coded
  claim/evidence/weak/limit callouts, results & claim→evidence tables, collapsible Pass 3,
  <dfn> glossary). summarize_paper.py gained `--format {md,html}` (prepare fills placeholders;
  finalize wires summary.html; status.summary_format recorded). Indexes/validate handle .html.
- Experiment: summarized 5 new CUA milestones in HTML (WebVoyager, OS-Atlas, AndroidWorld,
  Agent S2, UI-TARS-2). Measured vs last turn's 5 MD summaries (same paper types):
  same content (words 1.00x), artifact 1.27x bytes, generation cost ~1.03x — NOT 2-4x.
  Decision on default format pending user review.
