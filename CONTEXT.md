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

## Source link
The external URL to a paper's PDF or landing page (arXiv or published venue). The project
links to Source links; it does not host or redistribute downloaded PDFs in the shared
repo. (Downloaded PDFs remain local-only inputs to the Harness.)
