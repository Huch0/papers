# 3. Derived artifacts are generated in CI; deploy via gh-pages branch with free PR previews

Status: Accepted (2026-06-06)

## Context
Several colleagues add papers and write summaries to one repo. Committing generated
artifacts (`registry/papers.jsonl`, `indexes/*.md`, `catalog.sqlite`) would cause
constant merge conflicts even though each paper lives in its own folder. We also want
per-PR preview deployments to review rendered summaries before merge, at no dollar cost,
on GitHub Pages (the repo is public).

## Decision
- **Do not commit derived artifacts.** Git-ignore `papers.jsonl`, `indexes/*.md`,
  `catalog.sqlite`, `library/**/paper.pdf`, `library/**/extraction.txt`, `site/dist/`,
  `node_modules/`. Authoritative inputs only are committed (config, YAML, `summary.mdx`,
  knowledge, site source, docs).
- **Generate in CI** (and via a local `predev`/`prebuild` hook): every build runs
  `update_indexes.py` to produce `papers.jsonl` before `astro build`. Generation is
  deterministic (stable sort; the cosmetic `INDEX.md` timestamp line is dropped/pinned).
- **PR gate guarantees `main` always builds:** each PR must pass, in order,
  `validate_registry.py` → `knowledge.py validate` → `update_indexes.py` → `astro build`.
- **Publish via the `gh-pages` branch** (not `actions/deploy-pages`) so PR previews can be
  deployed to a subpath. Use `rossjrw/pr-preview-action` for `/pr-preview/pr-N/` URLs.
- **CI runtime is Node 20**; local dev uses Bun (ADR scope note, not a separate ADR).

## Consequences
- (+) Adding a paper is conflict-free (separate folders); generated files never collide.
- (+) `main` is always buildable; broken inputs fail the PR, not production.
- (+) Free PR previews on public-repo Actions minutes.
- (−) Surprising to a newcomer: no committed `papers.jsonl`/`indexes` — they appear only
  after running the generator. Documented in CONTEXT/README.
- (−) Subpath previews require correct Astro `base`/relative URLs.
- (−) Fork PRs get no preview (GitHub fork-secret restriction) → colleagues must be repo
  collaborators pushing in-repo branches.
