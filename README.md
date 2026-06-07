# papers/ — AI research reading harness

A local, evolvable system to **fetch**, **track**, **summarize**, and **triage** AI
research papers (agent harnesses, computer-use agents, SWE agents, document agents, and
related methods). Driven by Claude Code skills and guarded by hooks.

> Authoritative data is per-paper YAML under `library/`. Everything in `indexes/` and
> the JSONL/SQLite caches is regenerated from it. See `CLAUDE.md` for the rules.

> **Contributors & their agents:** read **[CONTRIBUTING.md](CONTRIBUTING.md)** for the
> step-by-step workflow (add a summary / Q&A / knowledge / skill) and **[CLAUDE.md](CLAUDE.md)**
> before editing. `main` is **branch-protected** — every change lands via a pull request
> (no reviewer required; you merge your own). **Never push to `main` directly.**

## Setup
```bash
python3 -m pip install -r requirements.txt   # PyYAML (required), requests + PyMuPDF (recommended)
```
- PyMuPDF (`fitz`) powers PDF extraction; without it, records/summaries still work but
  extraction is skipped.
- Optional: set `SEMANTIC_SCHOLAR_API_KEY` for higher Semantic Scholar rate limits.
- Set your contact email in `config/sources.yaml` (`defaults.contact_email`) for the
  polite API pools.

Scripts are runnable by Claude Code and by humans from the repo root, e.g.
`python3 scripts/update_indexes.py`.

## Directory layout
```
config/     interests, sources, venues, scoring, tags, milestones, summary template, schema  (SOURCE OF TRUTH for behavior)
registry/   papers.jsonl, fetch_log.jsonl, duplicate_candidates.jsonl, aliases.yaml, catalog.sqlite (derived/cache)
indexes/    INDEX, BY_DATE, BY_TAG, BY_VENUE, MUST_READ, RECENT_TRENDS, MILESTONES  (generated)
library/    <slug>/paper.yaml  +  <slug>/vN/{paper.pdf,metadata.yaml,summary.md,triage.md,extraction.txt,notes.md}  (AUTHORITATIVE)
knowledge/  concepts/<slug>.md (global, paper-agnostic notes; AUTHORITATIVE) + sessions/ + INDEX/BY_TAG/BY_PAPER (generated)
inbox/      YYYY-MM-DD/{candidates.jsonl,rejected.jsonl,daily_report.md}
logs/       system_changes.md, errors.jsonl, decisions.md
scripts/    paperlib (shared) + fetch_*/ingest/score/extract/summarize/validate/update_indexes/detect_duplicates/migrate
            + fetch_milestones + knowledge
.claude/    skills/ (slash commands) + hooks/ + settings.json
```

## Skills (slash commands)
| Command | Purpose |
|---|---|
| `/daily-papers [today\|DATE\|--since 3d\|--tags a,b\|--dry-run]` | Fetch + triage + record recent papers; summarize the top ones. |
| `/add-paper <url\|arxiv_id\|doi\|pdf_path>` | Ingest one paper (arXiv, PDF URL/local, DOI, OpenReview, S2, manual); also adds new versions. |
| `/summarize-paper <version_dir\|pdf>` | Generate/refresh a detailed English summary from the paper (not the abstract). |
| `/triage-papers [inbox/DATE\|--untriaged\|--tag g]` | Re-score and re-label against current config; emit a ranked reading list. |
| `/milestone-papers <field> [--discover]` | Find + ingest the landmark papers of a field (emergence→recent), deduped against the library. |
| `/paper-tutor <paper>` | Discuss a paper as a lab colleague/tutor; capture what you learn into the global knowledge base. |
| `/sync-paper-index` | Validate metadata and regenerate all indexes/caches deterministically. |
| `/evolve-paper-system <complaint/request>` | Turn a preference/friction into a durable config/script/template change + log it. |

## Daily workflow
1. `/daily-papers` — fetches from arXiv (primary) within the configured window, scores
   every candidate, ingests non-SKIP papers (records created even if a PDF is missing),
   downloads PDFs for ≥ SKIM papers, writes `inbox/<date>/daily_report.md`, and
   regenerates indexes. Claude then writes full summaries for the above-threshold set.
2. Read `indexes/MUST_READ.md` (or `INDEX.md`) and pick what to read.
3. Disagree with a label or seeing noise? → `/evolve-paper-system "<what's wrong>"`.

## Manual ingestion
```
/add-paper https://arxiv.org/abs/2501.12345
/add-paper 2501.12345
/add-paper https://openreview.net/forum?id=XXXX
/add-paper ./downloads/paper.pdf
```
Pointing `/add-paper` at a newer arXiv version (or a changed PDF) of an existing paper
creates a new `vN+1` directory automatically — the previous version is never touched.

## Metadata & versioning model
- Two YAML records per paper: paper-level (`paper.yaml`) and one per version
  (`vN/metadata.yaml`). Full schema + required fields: `config/metadata_schema.md`.
- A new arXiv version / changed PDF sha256 / changed venue ⇒ a **new version
  directory**; PDFs and summaries are colocated per version and never overwritten.
- Canonical key priority: arXiv base id → DOI → OpenReview id → Semantic Scholar id →
  OpenAlex id → normalized-title hash.
- Probable duplicates are flagged in `registry/duplicate_candidates.jsonl`, never
  auto-merged; resolve via `registry/aliases.yaml`.

## Summary template & rules
Summaries follow `config/summary_template.md`, which is built on three references:
Keshav's **"How to Read a Paper"** (three-pass method + the Five Cs), Kim's
**"Motivation ≠ Novelty"**, and the AI@UVA **FOCUS** extraction discipline. The template
is organized as three passes:
- **Pass 1 — Triage** (bird's-eye): one-sentence takeaway, the **Five Cs** (Category,
  Context, Correctness, Contributions, Clarity), and why it matters now.
- **Pass 2 — Content**: **Motivation** (the problem) kept *strictly separate* from
  **Novelty** (the genuine delta over prior work + the *mechanistic reason* the design
  must take its form), then core idea/method, **harness relevance**, experimental setup,
  and key results (read the figures, not just the prose).
- **Pass 3 — Critique**: claim-by-claim evidence check, hidden assumptions & failure
  modes, a "could I reconstruct it?" reproducibility test, strengths/weaknesses, and
  relationship to prior work. Then the Decision block (what to read, triage, notes).

Rules (applied by the skills): English only and **declarative** (no "the authors state
that…"); analyze, don't paraphrase the abstract; "Not reported" for absent data,
"Unclear" when unsupported; exact numbers + short quotes with page/section anchors. The
central rule is **Motivation ≠ Novelty** — state the delta so it survives deleting "we
propose" (insight, not artifact), and separate experiments that *verify the novelty*
from those that *merely confirm the motivation*. Type-specific checks: empirical papers →
experiments/baselines/ablations/artifacts/limitations + figure scrutiny (error bars,
significance, abstract-vs-table mismatches); benchmarks → task construction, evaluator
reliability, leakage, reproducibility, aging; SWE agents → execution-based eval and
test-validated patches; computer-use agents → interface type (GUI/CLI/API/shell/browser/
OS/IDE/workspace); document agents → artifact type, editing granularity, evaluator,
structural validation. For SKIM/TRACK_ONLY papers, Pass 1 + the Decision block is enough.

## Milestone papers
`/milestone-papers <field>` builds out the canonical landmark papers of a field from
its emergence to recent, **without duplicating** papers already in the library. The
durable list of "what is a milestone" lives in `config/milestones.yaml` (titles + era +
significance per field); the skill resolves each seed to a real record (arXiv id when
given, else title search), dedupes by canonical key + normalized title, ingests new
ones tagged `foundational` with a `milestone` block, and marks already-present seeds
idempotently. Milestones get a score floor (READ_SOON) so age never buries them. Output:
`indexes/MILESTONES.md` — a per-field timeline (emergence → foundational → expansion →
recent). Add a new field by adding it to `config/milestones.yaml` (or ask
`/evolve-paper-system`). `--discover` augments the curated seeds with live
high-influential-citation suggestions.

## Knowledge base (chat + global notes)
`/paper-tutor <paper>` lets you chat about a paper with a tutor/lab-colleague agent that
explains intuitively and **writes what you learn into a global knowledge base** under
`knowledge/`. Knowledge is paper-agnostic and **sharable across papers**: a concept
(e.g. "agent-computer interface") learned while reading paper A becomes a note in
`knowledge/concepts/<slug>.md`, linked bidirectionally to A, and is reused/extended when
you later discuss paper B that shares it. Each concept note has `## Intuition / Details /
Q&A / See also` sections; concepts and papers cross-link both ways (`paper.yaml:
knowledge_concepts` ↔ concept `related_papers`). Generated views: `knowledge/INDEX.md`
(all concepts), `knowledge/BY_PAPER.md` (concepts per paper), `knowledge/BY_TAG.md`.
Manage with `scripts/knowledge.py {ensure-concept,link,search,session,qa-add,index,validate}`;
your own notes are always preserved. Concepts are authored as **`.mdx`** (rendered on the
site at `/knowledge/<slug>/`).

**On the web:** concepts are browsable like the paper library (`/knowledge/`), each paper
page shows **Related concepts** + a **"Questions & Discussion"** panel (paper-scoped
`qa.mdx`, written by `/paper-tutor`), and concepts carry build-time **"Referenced by"**
backlinks. Every summary / concept / Q&A is **attributed** — `curated_by` / `asked_by`
(your GitHub login, resolved from `config/contributors.yaml`) shown with an avatar. Add
yourself to `config/contributors.yaml` so your attribution renders.

## Triage labels
`MUST_READ` (≥80) · `READ_SOON` (≥65) · `SKIM` (≥50) · `TRACK_ONLY` (≥35) · `SKIP`
(<35). Scores come from `config/scoring.yaml` (interest fit, recency, venue, harness
relevance, novelty, artifacts, evaluation quality, trend signal, author/lab signal,
minus negative-noise penalties). Every label carries a rationale. Recent-year papers
get a recency floor; citation count is capped for papers younger than ~6 months; old
GUI-only papers are penalized unless foundational.

## Validation & index regeneration
```
python3 scripts/validate_registry.py     # integrity checks (exit 0 = no errors)
python3 scripts/update_indexes.py         # regenerate JSONL/SQLite + all Markdown indexes
python3 scripts/detect_duplicates.py      # refresh duplicate candidates
python3 scripts/migrate_registry.py       # idempotent schema backfill (makes backups)
```
The PostToolUse hook runs validation + index refresh automatically after edits under
`library/`, `config/`, or `registry/`. The Stop hook regenerates stale indexes.

## Evolving preferences
Use `/evolve-paper-system "<complaint or request>"`. It inspects the relevant config/
template/script, proposes a minimal plan, applies it after confirmation for nontrivial
changes, runs validation, logs to `logs/system_changes.md`, and migrates existing
metadata if needed. Examples:
- `/evolve-paper-system I keep getting too many old GUI papers`
- `/evolve-paper-system Make summaries shorter for SKIP papers`
- `/evolve-paper-system Add a tag for evaluation-harness reliability`

## Website (reading site)
A static **Astro** site in `site/` is a read-only view over the harness (ADR-0001): it
reads `registry/papers.jsonl` for the catalog and renders `library/**/summary.{md,mdx}`.
See `docs/website-requirements.md` and `docs/adr/`.

- **Run locally:** `cd site && bun install && bun run dev` (or `npm install && npm run dev`).
  The `predev`/`prebuild` hook runs `update_indexes.py` so the feed is fresh.
- **Build:** `cd site && npm run build` → static output in `site/dist/` (Pagefind full-text
  index built automatically). Catalog supports facet filter (venue/year/tag/topic/triage) +
  sort + full-text search.
- **Theming:** default is **"Readable"** (Atkinson Hyperlegible, tuned for dense technical
  reading); a header **theme panel** lets each reader switch preset / typeface / accent /
  density, saved per-browser (GitHub Pages ships the default). See `docs/adr/0005`–`0006`.
- **Validate MDX before committing:** `node site/scripts/check-mdx.mjs <abs path to .mdx>`
  must print `OK` for any summary / concept / `qa.mdx` you write (the `/summarize-paper`
  and `/paper-tutor` skills run this automatically).
- **Summaries** are authored as **MDX** (`config/summary_template.mdx`) using a curated
  component set (`config/summary_components.md`) — concise, core-first, with depth in
  collapsible `<Pass>` and inline hover `<Term>` glossary. Legacy `.md` summaries render
  as-is; new ones are `.mdx`.
- **Contributing a paper (two paths, same result):**
  - *With Claude Code:* `/add-paper <ref>` then `/summarize-paper <vdir>` (writes MDX).
  - *Without Claude Code:* run `python3 scripts/fetch_arxiv.py --id <id> | python3 scripts/ingest.py …`,
    then `python3 scripts/summarize_paper.py <vdir> --prepare --format mdx` and fill the body
    against `config/summary_components.md`.
  - Open a PR; CI runs `validate_registry.py --skip-pdf` → `knowledge.py validate` →
    `update_indexes.py` → `astro build`, deploys a preview, and on merge publishes to Pages.
- **PDFs are not shared** — the site links to the source (arXiv/venue). Derived artifacts
  (`papers.jsonl`, `indexes/`, `site/dist/`) and PDFs are git-ignored; CI regenerates them.
- **Deploy:** GitHub Actions (`.github/workflows/pages.yml`) publishes to the `gh-pages`
  branch (prod at root, PR previews at `/pr-preview/pr-N/`). Set repo Pages source to
  `gh-pages`; add collaborators as repo members so their PR branches get previews.

## Troubleshooting
- **arXiv timeouts**: the fetchers retry with exponential backoff; if a run fully
  fails, re-run — errors are logged to `logs/errors.jsonl` and candidates preserved.
- **PDF won't download / not a PDF**: a record is still created; `status.downloaded`
  stays false and the error is logged. Re-attach later via `/add-paper`.
- **"PDF sha mismatch" / "summary missing" in validation**: a flag in `metadata.yaml`
  (`status.downloaded`/`status.summarized`) is ahead of reality — re-run the relevant
  step or correct the flag, then `/sync-paper-index`.
- **Out-of-taxonomy tag warning**: add the tag to `config/tag_taxonomy.yaml` (or via
  `/evolve-paper-system`).
- **Hook noise**: hooks never block normal work except clearly destructive shell
  commands; see `.claude/settings.json` and `.claude/hooks/`.
