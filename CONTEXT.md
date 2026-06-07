# CONTEXT — paper harness & reading site

Project glossary: the domain language we agree on. Definitions only — no implementation
details and no decisions (decisions live in `docs/adr/`). Update inline as terms resolve.

## Harness
The local, authoritative engine driven by Claude Code skills + Python scripts. It ingests
papers, tracks metadata and versions, scores/triages, detects duplicates, maintains the
knowledge base, and validates integrity. The Harness owns the source of truth.

## Authoritative record
The single source of truth for a paper: per-paper `paper.yaml` + per-version
`metadata.yaml`, plus the Summary body. Only the Harness writes it; everything else is
derived from it.

## Derived view
Any artifact regenerated from Authoritative records and never hand-edited: the Markdown
indexes, `papers.jsonl`, the SQLite cache, and the Website. Disposable and reproducible.

## Website (Presentation Layer)
A read-only, human-friendly Derived view for searching, filtering, sorting, and reading
Summaries across computers and devices. It renders Authoritative records; it never
originates paper data.

## Summary
The concise, core-first analysis of one paper version, authored as an MDX body colocated
with its Authoritative record (`library/<slug>/vN/summary.mdx`) and rendered by the
Website. It leads with the core message (TL;DR, contribution, headline result, triage)
and keeps supporting depth collapsed, and it is self-contained (defines its own
non-universal terms). The canonical section structure lives in
`config/summary_template.mdx`. Frontmatter is generated from the Authoritative record and
never hand-synced.

## Catalog
The searchable / filterable / sortable list of all papers the Website presents, built
from `papers.jsonl` (a Derived view). Each Catalog entry links to a Summary. Distinct
from the Markdown `indexes/` (which are Derived views for terminal/Git reading).

## Knowledge base
The global, paper-agnostic store of distilled understanding under `knowledge/` — Concepts
(and chat Sessions). It is Authoritative (authored via Claude Code's paper-tutor, not the
browser); the Website renders a Derived view of it. Knowledge is cross-paper: one Concept
may link many papers, and the corpus is meant to be navigated like the paper Catalog.

## Concept
A single reusable unit of understanding (e.g. "Agent-Computer Interface"), authored as
`knowledge/concepts/<slug>.md`. A Concept links bidirectionally to the Source papers it
was learned from (`related_papers` ↔ a paper's `knowledge_concepts`) and to related
Concepts. Distinct from a Summary: a Summary is about one paper; a Concept spans papers.

## Q&A
Paper-scoped question-and-answer pairs captured while discussing a paper with the
paper-tutor (e.g. on Mind2Web), stored in that paper's version dir and shown on its
Website page. Each Q&A links out to the global Concept(s) that explain it. Distinct from a
Concept (reusable, cross-paper) and from a Session (raw transcript).

## Session
The raw transcript of one paper-tutor conversation, kept under `knowledge/sessions/` as
local provenance. Not a Website surface.

## Curator (curated_by)
The person who invoked the agent to write a Derived doc — a Summary, Concept, or Q&A.
Recorded as `curated_by` (a GitHub login) with a `contributors` list for later editors;
Q&A items record `asked_by` per question. **Distinct from a paper's `authors`** (the
researchers who wrote the paper). Resolved from the git identity via
`config/contributors.yaml` and shown on the Website with the GitHub avatar.

## Source link
The external URL to a paper's PDF or landing page (arXiv or published venue). The project
links to Source links; it does not host or redistribute downloaded PDFs in the shared
repo. (Downloaded PDFs remain local-only inputs to the Harness.)
