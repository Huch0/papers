# 1. The Website is a derived view; the Harness/YAML stays authoritative

Status: Accepted (2026-06-06)

## Context
A working Harness already exists: per-paper `paper.yaml` + per-version `metadata.yaml`
are the source of truth, and Python/Claude Code do ingest, scoring/triage, duplicate
detection, the knowledge base, and validation. `indexes/*.md`, `papers.jsonl`, and the
SQLite cache are generated from the authoritative records.

We want a human-friendly website to search/filter/sort and read summaries. The tempting
move is to re-platform — make the web app's own content model (MDX frontmatter +
collections) authoritative and retire the YAML/Python.

## Decision
The Website is a **read-only Derived view**, alongside the Markdown indexes. The
Harness/YAML remains the single source of truth. Concretely:
- Metadata stays in `paper.yaml`/`metadata.yaml`; the Website's catalog is fed by the
  generated `registry/papers.jsonl`.
- The Summary body is authored as `library/<slug>/vN/summary.mdx`; its frontmatter is
  **generated from the Authoritative record**, not hand-synced.
- Ingest, scoring, dedup, versioning, and validation stay in the Harness.

## Consequences
- (+) Preserves the Harness's hard, non-display logic (canonical-key dedup, version
  tracking, scoring, milestone resolution, KB, validation) instead of rebuilding it in a
  web framework.
- (+) The site is disposable and reproducible; it can be rebuilt from authoritative data
  at any time.
- (−) Two artifacts per version (`metadata.yaml` + `summary.mdx`) must agree — mitigated
  by generating MDX frontmatter from YAML so authors never hand-sync.
- (−) Contributors add papers via the Harness (run the scripts), not by editing the site.
